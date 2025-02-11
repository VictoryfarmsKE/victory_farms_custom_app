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
			"fieldname": "other_allowance", 
			"label": _("Other Allowance"), 
			"fieldtype": "Currency", 
			"width": 150
		},
		{
			"fieldname": "total_cash_pay", 
			"label": _("Total Cash Pay"), 
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
			"fieldname": "total_non_cash_benefits", 
			"label": _("Total Non Cash Benefits"), 
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
			"fieldname": "rent_of_house", 
			"label": _("Rent of House"),
			"fieldtype": "Currency", 
			"width": 150
		},
		{
			"fieldname": "computed_rent_of_house", 
			"label": _("Computed Rent of House"),
			"fieldtype": "Currency", 
			"width": 150
		},
		{
			"fieldname": "rent_recovered_from_employee", 
			"label": _("Rent Recovered from Employee"),
			"fieldtype": "Currency", 
			"width": 150
		},
		{
			"fieldname": "net_value_of_housing", 
			"label": _("Net Value of Housing"),
			"fieldtype": "Currency", 
			"width": 150
		},
		{
			"fieldname": "total_gross_pay", 
			"label": _("Total Gross Pay"),
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
			"fieldname": "actual_contribution(nssf)", 
			"label": _("Actual Contribution (NSSF)"), 
			"fieldtype": "Currency", 
			"width": 150
		},
		{
			"fieldname": "post_retirement_medical_fund", 
			"label": _("Post Retirement medical Fund"), 
			"fieldtype": "Currency", 
			"width": 280
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
			"fieldname": "amount_of_benefit", 
			"label": _("Amount of Benefit"), 
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
		# row["total_non_cash_benefits"] = row["other_non_cash_benefit"] + row["value_of_meals"]
		# row["net_value_of_housing"] = row["computed_rent_of_house"] - row["rent_recovered_from_employee"]
		# row["total_gross_pay"] = row["total_cash_pay"] + row["total_non_cash_benefits"] + row["value_of_meals"] + row["net_value_of_housing"] + row["value_of_car_benefit"]
		# row["amount_of_benefit"] = row["actual_contribution(nssf)"] + row["mortgage_interest"]
		# row["taxable_pay"] = row["total_gross_pay"] - row["social_health_insurance_fund"] - row["post_retirement_medical_fund"] - row["affordable_housing_levy"] - row["amount_of_benefit"]
		
		row.update(details)
		report_data.append(row)
	print(">>>>>>>>>>>>..",report_data)
	return report_data