// Copyright (c) 2024, Solufy and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["SCS Report"] = {
	"filters": [
		{
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company")
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.defaults.get_user_default("year_start_date")
            // "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("End Date"),
            "fieldtype": "Date",
            "default": frappe.defaults.get_user_default("year_end_date")
            // "reqd": 1
        },
        {
            "fieldname": "item_code",
            "label": __("Item Code"),
            "fieldtype": "Link",
            "options": "Item"
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse"
        }

	]
};
 