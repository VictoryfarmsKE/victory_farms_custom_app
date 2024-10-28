// Copyright (c) 2024, Solufy and contributors
// For license information, please see license.txt

frappe.query_reports["Store Analysis"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee"
		},
		{
			fieldname: "period_of_month",
			label: __("Period of Month"),
			fieldtype: "Int"
		},
	]
};
