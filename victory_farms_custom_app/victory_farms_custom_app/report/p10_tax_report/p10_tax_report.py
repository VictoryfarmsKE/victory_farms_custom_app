# # Copyright (c) 2023, Navari Limited and contributors
# # For license information, please see license.txt

import frappe
from frappe import _
from pypika import Case
from functools import reduce


def execute(filters=None):
    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be greater than To Date"))

    return get_columns(), get_p10_report_data(filters)

def get_columns():
    columns = [
        {
            "fieldname": "tax_id",
            "label": _("PIN of Employee"), 
            "fieldtype": "Link", 
            "options": "Employee", 
            "width": 150
        },
        {   
            "fieldname": "employee_name", 
            "label": _("Employee Name"),
            "fieldtype": "Data", 
            "read_only": 1,
            "width": 150
        },
        {   
            "fieldname": "basic_salary", 
            "label": _("Basic Salary"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "housing_allowance",
            "label": _("Housing Allowance"), 
            "fieldtype": "Currency", 
            "width": 180
        },
        {
            "fieldname": "transport_allowance",
            "label": _("Transport Allowance"), 
            "fieldtype": "Currency", 
            "width": 150
         },
        {
            "fieldname": "leave_pay", 
            "label": _("Leave Pay"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "overtime", 
            "label": _("Over Time Allowance"), 
            "fieldtype": "Currency", 
            "width": 200
        },
        {
            "fieldname": "directors_fees", 
            "label": _("Directors Fees"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "lump_sum_payment", 
            "label": _("Lump Sum Pay if any"), 
            "fieldtype": "Currency",
            "width": 250
        },
        {
            "fieldname": "paye", 
            "label": _("PAYE"), 
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "other_allowance", 
            "label": _("Other Allowance"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "value_of_car_benefit", 
            "label": _("Value of Car Benefit"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "other_non_cash_benefit", 
            "label": _("Other Non cash benefit"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "value_of_meals", 
            "label": _("Value of meals"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "type_of_housing", 
            "label": _("Type of Housing"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "social_health_insurance_fund", 
            "label": _("Social Health Insurance Fund"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "actual_contribution_nssf", 
            "label": _("Actual Contribution(NSSF)"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "post_retirement_medical_fund", 
            "label": _("Post Retirement medical Fund"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "mortgage_interest", 
            "label": _("Mortgage Interest"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "affordable_housing_levy", 
            "label": _("Affordable Housing Levy"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "monthly_relief", 
            "label": _("Monthly Relief"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "amount_of_insurance_relief", 
            "label": _("Amount of Insurance Relief"), 
            "fieldtype": "Currency", 
            "width": 150
        },
        {
            "fieldname": "self_assessed_paye_tax", 
            "label": _("Self Assessed PAYE Tax"), 
            "fieldtype": "Currency", 
            "width": 150
        },
    ]

    return columns


def get_p10_report_data(filters):
    employee = frappe.qb.DocType("Employee")
    salary_slip = frappe.qb.DocType("Salary Slip")
    salary_detail = frappe.qb.DocType("Salary Detail")
    salary_component = frappe.qb.DocType("Salary Component")

    conditions = [salary_slip.docstatus == 1]
    if filters.get("company"):
        conditions.append(salary_slip.company == filters.get("company"))
    if filters.get("employee"):
        conditions.append(salary_slip.employee == filters.get("employee"))
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(
            salary_slip.posting_date.between(filters.get("from_date"), filters.get("to_date"))
        )

    query = frappe.qb.from_(salary_slip) \
        .inner_join(employee) \
        .on(employee.name == salary_slip.employee) \
        .inner_join(salary_detail) \
        .on(salary_slip.name == salary_detail.parent) \
        .inner_join(salary_component) \
        .on(salary_detail.salary_component == salary_component.name) \
        .select(
            employee.tax_id,
            salary_slip.employee_name,
            salary_detail.salary_component,
            salary_detail.amount,
            salary_component.p9a_tax_deduction_card_type
        ).where(
            reduce(lambda x, y: x & y, conditions)
        ).orderby(salary_slip.employee)

    data = query.run(as_dict=True)

    employee_data = {}
    for row in data:
        employee_pin = row["tax_id"]
        employee_name = row["employee_name"]
        salary_component = row["salary_component"]
        amount = row["amount"]
        tax_deduction_type = row.get("p9a_tax_deduction_card_type")

        if salary_component and amount:
            employee_key = f"{employee_pin}-{employee_name}"
            if employee_key not in employee_data:
                employee_data[employee_key] = {
                    "employee_name": employee_name,
                    "tax_id": employee_pin,
                    "components": {}
                }

            if tax_deduction_type:
                if tax_deduction_type not in employee_data[employee_key]["components"]:
                    employee_data[employee_key]["components"][tax_deduction_type] = 0
                employee_data[employee_key]["components"][tax_deduction_type] += amount

            component_key = salary_component.lower().replace(" ", "_")
            employee_data[employee_key][component_key] = employee_data[employee_key].get(component_key, 0) + amount

    report_data = []
    for employee_key, details in employee_data.items():
        components = details.pop("components")
        row = {
            "tax_id": details["tax_id"],
            "employee_name": details["employee_name"]
        }
        for component_type, total_amount in components.items():
            row[component_type.lower().replace(" ", "_")] = total_amount

        row.update(details)
        report_data.append(row)
    print("\n\n>>>>>>>>",report_data,"\n\n")
    return report_data




# [{'tax_id': 'A017211510P', 'employee_name': 'Christine Nyathira Kanga', 'type_of_housing': 155.93, 'actual_contribution(nssf)': 25000.0, 'basic_salary': 205740.0, 'other_allowance': 195.0, 'value_of_meals': 1039.5, 'over_time_allowance': 16225.05, 'leave_pay': 2160.0, 'social_health_insurance_fund': 8000.0, 'directors_fees': 5000.0, 'post_retirement_medical_fund': 100.0, 'housing_allowance': 2160.0, 'transport_allowance': 2160.0, 'other_non_cash_benefit': 12174.12, 'value_of_car_benefit': 2400.0, 'lumpsum_pay_if_any': 195.0, 'ahl_relief': 155.93, 'max_mortgage_interest_relief': 25000.0, 'taxable_income': 67140.0, 'gross_pay': 69300.0, 'employer_housing_levy': 1039.5, 'insurance_relief': 195.0, 'employee_housing_levy': 1039.5, 'gross_paye': 14925.05, 'provident_fund_relief': 2160.0, 'max_hosp_relief': 8000.0, 'max_insurance_relief': 5000.0, 'bereavement_fund': 100.0, 'employee_nssf': 2160.0, 'employer_nssf': 2160.0, 'paye': 12174.12, 'basic_pay': 69300.0, 'personal_relief': 2400.0, 'nhif': 1300.0, 'gross_insurance_relief': 195.0}] 
