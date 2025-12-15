# Copyright (c) 2025, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, get_quarter_ending, get_year_start, get_year_ending, flt, get_first_day, get_last_day
from frappe.model.document import Document
from datetime import datetime
from frappe.query_builder.custom import ConstantColumn




class AnnualAppraisal(Document):
    def on_submit(self):
        self.create_appraisal_payout()


    def create_appraisal_payout(self):
        year_dates = frappe.db.get_value("Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"], as_dict=1)
        ap_doc = frappe.new_doc("Appraisal Payout")
        ap_doc.posting_date = self.posting_date
        ap_doc.start_date = year_dates.get("year_start_date")
        ap_doc.end_date = year_dates.get("year_end_date")
        ap_doc.payout_frequency = "Annually"
        bonus_calculation_amount = ap_doc.get_amount_used_for_bonus_calculation(self.employee)

        individual_score_value = self.total_individual_score
        individual_score = flt((individual_score_value * 100) / 5, 2)
        matrix_percent = ap_doc.get_matrix_percent(individual_score)
        individual_bonus_percent = ap_doc.get_bonus_percent(self.bonus_potential, matrix_percent)
        individual_bonus = flt((individual_bonus_percent / 100) * bonus_calculation_amount, 3)

        department_score_value = self.total_avg
        department_score = flt((department_score_value * 100) / 5, 2)
        matrix_percent = ap_doc.get_matrix_percent(department_score)
        department_bonus_percent = ap_doc.get_bonus_percent(self.bonus_potential_department, matrix_percent)
        department_bonus = flt((department_bonus_percent / 100) * bonus_calculation_amount, 3)

        company_score_value = self.company_score
        company_score = flt((company_score_value * 100) / 5, 2)
        matrix_percent = ap_doc.get_matrix_percent(company_score)
        company_bonus_percent = ap_doc.get_bonus_percent(self.bonus_potential_company, matrix_percent)
        company_bonus = flt((company_bonus_percent / 100) * bonus_calculation_amount, 3)

        ap_doc.append("appraisal_payout_details",{
            "employee": self.employee, 
            "individual_score_value": self.total_individual_score,
            "department_score_value": self.total_avg,
            "company_score_value": self.company_score,
            "individual_bonus": individual_bonus,
            "department_bonus": department_bonus,
            "company_bonus": company_bonus,
            "total_bonus": individual_bonus + department_bonus + company_bonus
        })
        ap_doc.flags.ignore_permissions = True
        ap_doc.save()
        self.db_set("appraisal_payout", ap_doc.name)

    @frappe.whitelist()
    def get_department_data(self):
        department_data = self.get_employee_department_data()

        self.department_map = {row.department: row.weightage for row in department_data}
    
        # If there are no departments, avoid querying appraisal data
        # which would produce an empty IN () clause in SQL. Use an
        # empty list for subsequent processing.
        # Build quarter ranges once and reuse
        quarter_data = self._build_quarter_data()

        # prepare counter for individual scores (used whether departments exist or not)
        individual_scr = 0

        # If there are no departments, still fetch individual appraisal
        # scores (they are recorded separately) and populate the
        # per-quarter individual fields. Department appraisal data is
        # independent, so we only call get_appraisal_data when there
        # are departments to fetch.
        if not self.department_map:
            APC = frappe.qb.DocType("Appraisal Cycle")
            APP = frappe.qb.DocType("Appraisal")
            indi_query = frappe.qb.from_(APP).inner_join(APC).on(APP.appraisal_cycle == APC.name).select(
                APP.total_score, ConstantColumn(1).as_("count"), APP.appraisal_cycle, APC.start_date
            ).where((APP.employee == self.employee) & (APP.docstatus == 1) & (APC.end_date.isin(quarter_data["dates"]))).orderby(APC.start_date)

            indi_rows = indi_query.run(as_dict=1)
            # Map appraisal rows to quarters and set qX_individual fields
            for row in indi_rows:
                start_date = row.get("start_date")
                quarter_label = None
                if quarter_data["Q1"][0] <= start_date <= quarter_data["Q1"][1]:
                    quarter_label = "Q1"
                elif quarter_data["Q2"][0] <= start_date <= quarter_data["Q2"][1]:
                    quarter_label = "Q2"
                elif quarter_data["Q3"][0] <= start_date <= quarter_data["Q3"][1]:
                    quarter_label = "Q3"
                elif quarter_data["Q4"][0] <= start_date <= quarter_data["Q4"][1]:
                    quarter_label = "Q4"

                if quarter_label:
                    if self.get(f"{quarter_label.lower()}_individual") != row.get("total_score"):
                        individual_scr += int(row.get("count")) if row.get("count") else 0
                        self.db_set(f"{quarter_label.lower()}_individual", row.get("total_score") if row.get("total_score") else 0)

            # proceed with empty department scores
            dep_score_data = []
        else:
            dep_score_data = self.get_appraisal_data()

        dep_quarter_data = frappe._dict({})
        self.quarterly_department_details = []
        for row in dep_score_data:
            weightage = self.department_map[row.department]
            self.append("quarterly_department_details", {
                "quarter": row.quarter,
                "appraisal_cycle": row.appraisal_cycle,
                "department": row.department,
                "weightage": weightage,
                "score": row.total_goal_score
            })
            if self.get(f"{row.quarter.lower()}_individual") != row.get("total_score"):
                individual_scr += int(row.get("count")) if row.get("count") else 0
                self.db_set(f"{row.quarter.lower()}_individual", row.get("total_score") if row.get("total_score") else 0)
            dep_quarter_data.setdefault((row.quarter, row.department, weightage), 0) 
            dep_quarter_data[(row.quarter, row.department, weightage)] += row.total_goal_score

        score_count = individual_scr
        # If we didn't count any individual appraisal rows (because
        # the quarter fields were already set), derive the count from
        # the existing q1..q4 individual fields so we can compute the
        # average correctly.
        if not score_count:
            q1 = flt(getattr(self, "q1_individual", 0))
            q2 = flt(getattr(self, "q2_individual", 0))
            q3 = flt(getattr(self, "q3_individual", 0))
            q4 = flt(getattr(self, "q4_individual", 0))
            non_empty = sum(1 for v in (q1, q2, q3, q4) if v is not None and v != "")
            if non_empty:
                score_count = non_empty
        self.q1_avg = 0
        self.q2_avg = 0
        self.q3_avg = 0
        self.q4_avg = 0

        for row in dep_quarter_data:
            dep_avg = flt((dep_quarter_data[row] / 3) * (row[2] / 100), 3)
            if row[0] == "Q1":
                self.q1_avg += dep_avg
            elif row[0] == "Q2":
                self.q2_avg += dep_avg
            elif row[0] == "Q3":
                self.q3_avg += dep_avg
            else:
                self.q4_avg += dep_avg
        
        # Prevent division by zero when there are no individual scores counted
        if score_count:
            q1 = flt(getattr(self, "q1_individual", 0))
            q2 = flt(getattr(self, "q2_individual", 0))
            q3 = flt(getattr(self, "q3_individual", 0))
            q4 = flt(getattr(self, "q4_individual", 0))
            self.total_individual_score = flt((q1 + q2 + q3 + q4) / score_count, 2)
        else:
            self.total_individual_score = 0
        self.total_avg = flt((self.q1_avg + self.q2_avg + self.q3_avg + self.q4_avg) / 4, 2)
        
        december_start = datetime(int(self.fiscal_year), 12, 1).date()
        december_end = datetime(int(self.fiscal_year), 12, 31).date()

        appraisal_cycle = frappe.db.get_value("Appraisal Cycle", {"start_date": ["<=", december_start], "end_date": [">=", december_end]}, "name")
        
        employee_data = frappe.db.get_value("Employee", self.employee, ["custom_appraisal_on_group", "company"], as_dict=1)
        
        if employee_data.get("custom_appraisal_on_group"):
            company = frappe.db.get_single_value("Navari Custom Payroll Settings", "group_company")
        else:
            company = employee_data.get("company")
            
        self.company_score = frappe.db.get_value("Company Appraisal",{"appraisal_cycle": appraisal_cycle,"docstatus":1, "company": company},"score")

        if not self.company_score:
            self.company_score = 0
            frappe.msgprint("No Company Appraisal found for the given date range.")
        
        self.company_score  = flt(self.company_score * (5 / 100), 3)

        total = flt(sum([
            self.bonus_potential * self.total_individual_score,
            self.bonus_potential_department* self.total_avg,
            self.bonus_potential_company * self.company_score
        ]), 3)

        self.final_score = flt(total / (self.bonus_potential + self.bonus_potential_department + self.bonus_potential_company),3)

    def get_employee_department_data(self):
        return frappe.db.get_all("Department Details", {"parent": self.employee}, ["department", "weightage"])

    def _build_quarter_data(self):
        quarter_data = frappe._dict({
            "Q1": [],
            "Q3": [],
            "Q2": [],
            "Q4": [],
            "Year": [],
            "dates": []
        })
        for idx, date in enumerate(["01", "04", "07", "10"]):
            from_date = getdate(f"{date}-01-{self.fiscal_year}")
            to_date = get_quarter_ending(from_date)
            if not quarter_data.get("Year"):
                quarter_data["Year"] = [get_year_start(from_date), get_year_ending(from_date)]
            quarter_data["dates"].append(to_date)
            quarter_data[f"Q{idx + 1}"] = [from_date, to_date]

        return quarter_data

    def get_appraisal_data(self):
        quarter_data = self._build_quarter_data()

        DPA = frappe.qb.DocType("Department Appraisal")
        APC = frappe.qb.DocType("Appraisal Cycle")
        APP = frappe.qb.DocType("Appraisal")

<<<<<<< HEAD
        indi_query = frappe.qb.from_(APP).inner_join(APC).on(APP.appraisal_cycle == APC.name).select(APP.total_score, ConstantColumn(1).as_("count"), APP.appraisal_cycle, APC.start_date
=======
        indi_query = frappe.qb.from_(APP).inner_join(APC).on(APP.appraisal_cycle == APC.name).select(APP.total_score.as_("custom_total_individual_goal_scor"), ConstantColumn(1).as_("count"), APP.appraisal_cycle, APC.start_date
>>>>>>> 1346290d85cd89cfad799d6cee2a27e3d7940048
            ).where((APP.employee == self.employee)  & (APP.docstatus == 1) 
            & (APC.end_date.isin(quarter_data["dates"]))).orderby(APC.start_date)


        query = frappe.qb.from_(DPA).inner_join(APC).on(DPA.appraisal_cycle == APC.name).left_join(indi_query).on((indi_query.appraisal_cycle == APC.name) & (indi_query.start_date == APC.start_date)).select(DPA.department, DPA.appraisal_cycle, indi_query.total_score, indi_query.count,
            DPA.total_goal_score,
            frappe.qb.terms.Case()
            .when(APC.start_date[quarter_data["Q1"][0] : quarter_data["Q1"][1]], "Q1")
            .when(APC.start_date[quarter_data["Q2"][0] : quarter_data["Q2"][1]], "Q2")
            .when(APC.start_date[quarter_data["Q3"][0] : quarter_data["Q3"][1]], "Q3")
            .when(APC.start_date[quarter_data["Q4"][0] : quarter_data["Q4"][1]], "Q4")
            .else_("No Quarter").as_("quarter")
            ).where((DPA.department.isin(list(self.department_map.keys()))) & (DPA.docstatus == 1) 
            & (APC.start_date[quarter_data["Year"][0] : quarter_data["Year"][1]])).orderby(APC.start_date)

        return query.run(as_dict = 1)