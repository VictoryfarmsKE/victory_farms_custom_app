# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import DocType
from frappe import _

def execute(filters=None):
	columns, data = [], []

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		{
			"label": _("ID (Store Deduction)"),
			"fieldtype": "Link",
			"fieldname": "name",
			"options": "Store Deduction",
			"width": 120,
		},
		{
			"label": _("Date of Issue"),
			"fieldtype": "Date",
			"fieldname": "date_of_issue",
			"width": 80,
		},
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
		{
			"label": _("Item"),
			"fieldtype": "Link",
			"fieldname": "item",
			"options": "Item",
			"width": 120,
		},
		{
			"label": _("Period of Payment (Months)"),
			"fieldtype": "Int",
			"fieldname": "period_of_payment",
			"width": 60,
		},
		{
			"label": _("Remaining Payments"),
			"fieldtype": "Int",
			"fieldname": "remaining_payments",
			"width": 60,
		},
		{
			"label": _("Item Cost"),
			"fieldtype": "Currency",
			"fieldname": "item_cost",
			"width": 100,
		},
		{
			"label": _("Deduction"),
			"fieldtype": "Currency",
			"fieldname": "deduction",
			"width": 100,
		},
		{
			"label": _("Outstanding Amount"),
			"fieldtype": "Currency",
			"fieldname": "outstanding",
			"width": 100,
		},
	]

def get_data(filters):
	SD = frappe.qb.DocType("Store Deduction")

	query = (
		frappe.qb.from_(SD)
		.select(SD.name, SD.posting_date.as_("date_of_issue"), SD.item, SD.period_of_payment, SD.item_cost.as_("deduction"), SD.employee, SD.employee_name, SD.remaining_payments, (SD.item_cost / SD.period_of_payment).as_("item_cost"), (SD.remaining_payments * (SD.item_cost / SD.period_of_payment)).as_("outstanding"))
		.where(SD.docstatus == 1)
	)

	if filters.get("from_date"):
		query = query.where(SD.posting_date >= filters.from_date)

	if filters.get("to_date"):
		query = query.where(SD.posting_date <= filters.to_date)
	
	if filters.get("employee"):
		query = query.where(SD.employee == filters.employee)
	
	if filters.get("period_of_month"):
		query = query.where(SD.period_of_payment == filters.period_of_month)

	return query.run(as_dict=True)