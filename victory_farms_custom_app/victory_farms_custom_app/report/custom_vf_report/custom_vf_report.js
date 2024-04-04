frappe.query_reports["Custom VF report"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            // "default": frappe.defaults.get_user_default("Company")
        },
        {
            "fieldname": "from_date",
            "label": __("Start Date"),
            "fieldtype": "Date",
            // "default": frappe.defaults.get_user_default("year_start_date"),
            // "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("End Date"),
            "fieldtype": "Date",
            // "default": frappe.defaults.get_user_default("year_end_date"),
            // "reqd": 1
        },
        {
            "fieldname": "item_code",
            "label": __("Item code"),
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

