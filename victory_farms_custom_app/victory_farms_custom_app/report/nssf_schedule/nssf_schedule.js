// Copyright (c) 2025, Solufy and contributors
// For license information, please see license.txt

frappe.query_reports["NSSF Schedule"] = {
	"filters": [
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
			reqd: 1,
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			reqd: 1,
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
	]
};
