# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt

from collections import defaultdict
import frappe
from frappe import _
from frappe.query_builder import CustomFunction

def execute(filters=None):

	filters.months = {
			1 : "Jan",
			2 : "Feb",
			3 : "Mar",
			4 : "Apr",
			5 : "May",
			6 : "Jun",
			7 : "Jul",
			8 : "Aug",
			9 : "Sep",
			10 : "Oct",
			11 : "Nov",
			12 : "Dec",
	}

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data


def get_columns(filters):
	columns = [
		{
			"label": _("Employee"),
			"fieldtype": "Link",
			"fieldname": "employee",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"fieldname": "employee_name",
			"width": 120,
		},
	]
	
	for row in filters.months.values():
		columns += [
				{
				"label": _(f"{row}"),
				"fieldtype": "Currency",
				"fieldname": f"{row}",
				"width": 100,
			},
		]

	columns += [
		{
			"label": _("Total"),
			"fieldtype": "Currency",
			"fieldname": "total",
			"width": 120,
		},
	]


	return columns

def get_data(filters):

	deduction_component = frappe.db.get_value("Salary Component", {"is_for_store_deduction": 1})

	if not deduction_component:
		return []

	ASL = frappe.qb.DocType("Additional Salary")
	EMP = frappe.qb.DocType("Employee")

	filters.from_date, filters.to_date = frappe.db.get_value("Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"])

	month = CustomFunction("MONTH", ["date"])

	raw_data = (
		frappe.qb.from_(ASL)
		.join(EMP).on(EMP.name == ASL.employee)
		.select(ASL.employee, ASL.employee_name, ASL.amount, month(ASL.payroll_date).as_("month_number"))
		.where((ASL.docstatus == 1)
			& (ASL.salary_component == deduction_component)
			& (ASL.payroll_date >= filters.from_date)
			& (ASL.payroll_date <= filters.to_date)
			)
		.groupby(ASL.employee, ASL.payroll_date)
		)

	if filters.get("employment_type"):
		raw_data = raw_data.where(EMP.employment_type == filters.employment_type)
	
	if filters.get("location"):
		raw_data = raw_data.where(EMP.custom_location == filters.location)
	
	if filters.get("department"):
		raw_data = raw_data.where(EMP.department == filters.department)
	
	if filters.get("designation"):
		raw_data = raw_data.where(EMP.designation == filters.designation)
	
	if filters.get("employee_category"):
		raw_data = raw_data.where(EMP.custom_employee_category == filters.employee_category)

	raw_data = raw_data.run(as_dict = True)

	processed_data = defaultdict(lambda: {"total": 0})

	for row in raw_data:
		month = filters.months.get(row.month_number)
		emp_data = processed_data[row.employee]
		emp_data["employee_name"] = row.employee_name
		emp_data[month] = emp_data.get(month, 0) + row.amount
		emp_data["total"] += row.amount

	return [{"employee": emp, **emp_data} for emp, emp_data in processed_data.items()]