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
			"fieldname": "pin_of_employee",
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
			"fieldname": "residential_status", 
			"label": _("Residential Status"),
			"fieldtype": "Data", 
			"read_only": 1,
			"width": 100
		},
		{   
			"fieldname": "type_of_employee", 
			"label": _("Type Of Employee"),
			"fieldtype": "Data", 
			"read_only": 1,
			"width": 100
		},
		{   
			"fieldname": "basic_salary", 
			"label": _("Basic Salary"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "housing_allowance",
			"label": _("Housing Allowance"), 
			"fieldtype": "Float", 
			"width": 180
		},
		{
			"fieldname": "transport_allowance",
			"label": _("Transport Allowance"), 
			"fieldtype": "Float", 
			"width": 150
		 },
		{
			"fieldname": "leave_pay", 
			"label": _("Leave Pay"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "over_time_allowance", 
			"label": _("Over Time Allowance"), 
			"fieldtype": "Float", 
			"width": 200
		},
		{
			"fieldname": "directors_fees", 
			"label": _("Directors Fees"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "lump_sum_pay_if_any", 
			"label": _("Lump Sum Pay if any"), 
			"fieldtype": "Float",
			"width": 250
		},
		{
			"fieldname": "other_allowance", 
			"label": _("Other Allowance"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "total_cash_pay", 
			"label": _("Total Cash Pay"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "value_of_car_benefit", 
			"label": _("Value of Car Benefit"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "other_non_cash_benefit", 
			"label": _("Other Non cash benefit"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "total_non_cash_benefits", 
			"label": _("Total Non Cash Benefits"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "value_of_meals", 
			"label": _("Value of meals"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "type_of_housing", 
			"label": _("Type of Housing"), 
			"fieldtype": "Data", 
			"width": 150
		},
		{
			"fieldname": "rent_of_house", 
			"label": _("Rent of House"),
			"fieldtype": "Float", 
			"width": 150,
		},
		{
			"fieldname": "computed_rent_of_house", 
			"label": _("Computed Rent of House"),
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "rent_recovered_from_employee", 
			"label": _("Rent Recovered from Employee"),
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "net_value_of_housing", 
			"label": _("Net Value of Housing"),
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "total_gross_pay", 
			"label": _("Total Gross Pay"),
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "social_health_insurance_fund", 
			"label": _("Social Health Insurance Fund"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "actual_contribution(nssf)", 
			"label": _("Actual Contribution (NSSF)"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "post_retirement_medical_fund", 
			"label": _("Post Retirement medical Fund"), 
			"fieldtype": "Float", 
			"width": 280
		},
		{
			"fieldname": "mortgage_interest", 
			"label": _("Mortgage Interest"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "affordable_housing_levy", 
			"label": _("Affordable Housing Levy"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "amount_of_benefit", 
			"label": _("Amount of Benefit"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "taxable_pay", 
			"label": _("Taxable Pay"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "tax_payable", 
			"label": _("Tax Payable"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "monthly_relief", 
			"label": _("Monthly Relief"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "amount_of_insurance_relief", 
			"label": _("Amount of Insurance Relief"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "paye_allowance", 
			"label": _("PAYE"), 
			"fieldtype": "Float", 
			"width": 150
		},
		{
			"fieldname": "self_assessed_paye_tax", 
			"label": _("Self Assessed PAYE Tax"), 
			"fieldtype": "Float", 
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
			employee.residential_status,
			employee.type_of_employee,
			employee.type_of_housing,
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
					"residential_status": row.get("residential_status"),
					"type_of_employee": row.get("type_of_employee"),
					"type_of_housing": row.get("type_of_housing"),
					"components": {}
				}

			if tax_deduction_type:
				if tax_deduction_type not in employee_data[employee_key]["components"]:
					employee_data[employee_key]["components"][tax_deduction_type] = 0
				employee_data[employee_key]["components"][tax_deduction_type] += amount

			component_key = salary_component.lower().replace(" ", "_")
			employee_data[employee_key][component_key] = employee_data[employee_key].get(component_key, 0) + amount

	p9_cards = ["Basic Salary",
			"Benefits NonCash",
			"Value of Quarters",
			"Total Gross Pay",
			"Rent of House",
			"E1 Defined Contribution Retirement Scheme",
			"E2 Defined Contribution Retirement Scheme",
			"E3 Defined Contribution Retirement Scheme",
			"Owner Occupied Interest",
			"Retirement Contribution and Owner Occupied Interest",
			"Chargeable Pay",
			"Computed Rent of House",
			"Tax Charged",
			"Personal Relief",
			"Insurance Relief",
			"Housing Allowance",
			"Transport Allowance",
			"Leave Pay",
			"Over Time Allowance",
			"Directors Fees",
			"Lump Sum Pay if any",
			"PAYE",
			"Other Allowance",
			"Value of Car Benefit",
			"Other Non cash benefit",
			"Value of meals",
			"Type of Housing",
			"Social Health Insurance Fund",
			"Actual Contribution(NSSF)",
			"Post Retirement medical Fund",
			"Mortgage Interest",
			"Affordable Housing Levy",
			"Monthly Relief",
			"Rent Recovered from Employee",
			"Amount of Insurance Relief",
			"Self Assessed PAYE Tax",
			"Amount of Benefit",
			"Total Cash Pay",
			"Total Non Cash Benefits",
			"Net Value of Housing"]

	report_data = []
	for employee_key, details in employee_data.items():
		components = details.pop("components")
		row = {
			"tax_id": details["tax_id"],
			"employee_name": details["employee_name"],
			"residential_status": details.get("residential_status"),
			"type_of_employee": details.get("type_of_employee"),
			"type_of_housing": details.get("type_of_housing"),
		}
		for component_type, total_amount in components.items():
			key = component_type.lower().replace(" ", "_")
			p9_cards.append(key)
			row[key] = total_amount

		row.update(details)
		for key in p9_cards:
			act_key = key.lower()
			if not row.get(act_key):
				row[act_key] = 0

		report_data.append(row)
	return report_data