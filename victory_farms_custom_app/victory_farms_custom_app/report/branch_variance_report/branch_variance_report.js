// Copyright (c) 2024, Solufy and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Branch Variance Report"] = {
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
            "label": __("Start Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "to_date",
            "label": __("End Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
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
        },
        {
            "fieldname": "custom_item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        },
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname == "received_qty" && data && data.received_qty > 0) {
            value = "<span style='color:green'>" + value + "</span>";
        }
        else if (column.fieldname == "total_quantity_sold" && data && data.total_quantity_sold > 0) {
            value = "<span style='color:red'>" + value + "</span>";
        }
        return value;
    }
};


// frappe.query_reports["VF Stock Balance"] = {
// 	"filters": [
// 		{
//             "fieldname": "company",
//             "label": __("Company"),
//             "fieldtype": "Link",
//             "options": "Company",
//             "default": frappe.defaults.get_user_default("Company")
//         },
//         {
//             "fieldname": "from_date",
//             "label": __("Start Date"),
//             "fieldtype": "Date",
//             "default": frappe.defaults.get_user_default("year_start_date"),
//             // "reqd": 1
//         },
//         {
//             "fieldname": "to_date",
//             "label": __("End Date"),
//             "fieldtype": "Date",
//             "default": frappe.defaults.get_user_default("year_end_date"),
//             // "reqd": 1
//         },
//         {
//             "fieldname": "item_code",
//             "label": __("Item Code"),
//             "fieldtype": "Link",
//             "options": "Item"
//         },
//         // {
//         //     "fieldname": "item_group",
//         //     "label": __("Item Group"),
//         //     "fieldtype": "Link",
//         //     "options": "Item Group"
//         // },
//         {
//             "fieldname": "warehouse",
//             "label": __("Warehouse"),
//             "fieldtype": "Link",
//             "options": "Warehouse"
//         }

// 	]
//     'formatter': function (value, row, column, data, default_formatter) {
//         // console.log("======",value)
//         value = default_formatter(value, row, column, data);
//         if (column.fieldname == "received_qty" && data && data.received_qty < 0) {
//             value = "<span style='color:red'>" + value + "</span>";
//         }
//         else if (column.fieldname == "total_quantity_sold" && data && data.total_quantity_sold > 0) {
//             value = "<span style='color:green'>" + value + "</span>";
//         }

//         return value;
//     },
// };
// erpnext.utils.add_inventory_dimensions('Stock Ledger', 10);