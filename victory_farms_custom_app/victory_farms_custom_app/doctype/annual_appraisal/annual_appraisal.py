# Copyright (c) 2025, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, get_quarter_ending, get_year_start, get_year_ending
from frappe.model.document import Document


class AnnualAppraisal(Document):
	@frappe.whitelist()
	def get_department_data(self):
		department_data = self.get_employee_department_data()
		for row in department_data:
			appraisal_data = self.get_appraisal_data(row)
			for data in appraisal_data:
				self.append("quarterly_department_details", {
					"quarter": data.quarter,
					"department": row.department,
					"weightage": row.weightage,
					"score": data.total_goal_score
				})


	def get_employee_department_data(self):
		return frappe.db.get_all("Department Details", {"parent": self.employee}, ["department", "weightage"])

	def get_appraisal_data(self, row):
		quarter_data = frappe._dict({
			"Q1": [],
			"Q2": [],
			"Q3": [],
			"Q4": [],
			"Year": []
		})
		for idx, date in enumerate(["01", "04", "07", "10"]):
			from_date = getdate(f"{date}-01-{self.fiscal_year}")
			to_date = get_quarter_ending(from_date)
			if not quarter_data.get("Year"):
				quarter_data["Year"] = [get_year_start(from_date), get_year_ending(from_date)]
			quarter_data[f"Q{idx + 1}"] = [from_date, to_date]

		DPA = frappe.qb.DocType("Department Appraisal")
		APC = frappe.qb.DocType("Appraisal Cycle")

		query = frappe.qb.from_(DPA).inner_join(APC).on(DPA.appraisal_cycle == APC.name).select(DPA.total_goal_score,
		frappe.qb.terms.Case()
		.when(APC.start_date[quarter_data["Q1"][0] : quarter_data["Q1"][1]], "Q1")
		.when(APC.start_date[quarter_data["Q2"][0] : quarter_data["Q2"][1]], "Q2")
		.when(APC.start_date[quarter_data["Q3"][0] : quarter_data["Q3"][1]], "Q3")
		.when(APC.start_date[quarter_data["Q4"][0] : quarter_data["Q4"][1]], "Q4")
		.else_("No Quarter").as_("quarter")
		).where((DPA.department == row.department) & (DPA.docstatus == 1) & (APC.start_date[quarter_data["Year"][0] : quarter_data["Year"][1]])).orderby(APC.start_date)

		return query.run(as_dict = 1)