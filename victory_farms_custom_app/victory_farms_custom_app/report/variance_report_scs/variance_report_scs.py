# Copyright (c) 2024, Sloufy and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Link",
            "options": "Item",
            "width": 120,
        },
        {
            'fieldname': 'destination_warehouse',
            'label': _('Warehouse'),
            'fieldtype': 'Data',
            "options": "Warehouse",
            'width': 100,
            'align': 'left'
        },
        {
            'fieldname': 'total_opening_stock',
            'label': _('Opening Stock'),
            'fieldtype': 'Data',
            'width': 120,
            'align': 'right'
        },
        {
            'fieldname': 'received_qty',
            'label': _('In Stock'),
            'fieldtype': 'Data',
            'width': 130,
            'align': 'right'
        },
        {
            'fieldname': 'total_quantity_sold',
            'label': _('Out Stock'),
            'fieldtype': 'Data',
            'width': 100,
            'align': 'right'
        },
        {
            'fieldname': 'spoilage_stock',
            'label': _('Spoilage Stock'),
            'fieldtype': 'Data',
            'width': 120,
            'align': 'right'
        },
        {
            'fieldname': 'expected_closing_stock',
            'label': _('Expected Closing Stock'),
            'fieldtype': 'Data',
            'width': 160,
            'align': 'right'
        },
        {
            'fieldname': 'system_stock',
            'label': _('System Stock'),
            'fieldtype': 'Data',
            'width': 120,
            'align': 'right'
        },
        {
            'fieldname': 'difference',
            'label': _('Difference'),
            'fieldtype': 'Data',
            'width': 100,
            'align': 'right'
        },
        {
            'fieldname': 'sum_stock_takes',
            'label': _('Sum Stock Takes'),
            'fieldtype': 'Data',
            'width': 140,
            'align': 'right'
        },
        {
            'fieldname': 'posting_date',
            'label': _('Date'),
            'fieldtype': 'Date',
            'width': 100
        },
    ]
    return columns

def get_data(filters):
    item_name = filters.get("item_name")
    destination_warehouse = filters.get("destination_warehouse")
    if item_name:

        return frappe.db.sql(
            """
            SELECT
                it.item_name,
                (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) AS total_opening_stock,
                COALESCE(
                    (SELECT COALESCE(SUM(sed.qty), 0) 
                     FROM `tabStock Entry Detail` AS sed
                     WHERE sed.item_code = it.item_code),
                    0
                ) AS received_qty,
                (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) 
                 FROM `tabStock Ledger Entry` AS sle
                 WHERE sle.item_code = it.item_code AND sle.actual_qty < 0) AS total_quantity_sold,
                -- COALESCE(
                --     (SELECT COALESCE(SUM(sed.qty), 0) 
                --      FROM `tabStock Entry Detail` AS sed
                --      WHERE sed.item_code = it.item_code 
                --      AND it.item_group = 'Spoilage'),
                --     0
                -- ) AS spoilage_stock,
                -- COALESCE(
                --     (SELECT se.to_warehouse FROM `tabStock Entry` AS se
                --      JOIN `tabStock Entry Detail` AS sed ON se.name = sed.parent
                --      WHERE sed.item_code = it.item_code 
                --      AND it.item_group = 'Spoilage'
                --      ORDER BY posting_date DESC LIMIT 1),
                --     'No destination warehouse'
                -- ) AS destination_warehouse,
                -- COALESCE(
                --     (SELECT MAX(posting_date) FROM `tabStock Entry` AS se
                --      JOIN `tabStock Entry Detail` AS sed ON se.name = sed.parent
                --      WHERE sed.item_code = it.item_code 
                --      AND it.item_group = 'Spoilage'),
                --     'No posting date'
                -- ) AS posting_date,

                COALESCE(
                    (SELECT t_warehouse FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code LIMIT 1)) AS destination_warehouse,

                COALESCE(
                    (SELECT COALESCE(SUM(sc.qty), 0) FROM `tabSpoilage Child` AS sc WHERE sc.item_code = it.item_code)) AS spoilage_stock,
              
                COALESCE(
                    (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) 
                )AS system_stock,


                ((
                    (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                    (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                ) - 
                (
                    (SELECT COALESCE(SUM(sc.qty), 0) FROM `tabSpoilage Child` AS sc WHERE sc.item_code = it.item_code) +
                    (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                )) AS expected_closing_stock,
                -- Found diff expected closing stock - system stock

                (
                    (
                        (
                            (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                            (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                        ) - 
                        (
                            (SELECT COALESCE(SUM(sc.qty), 0) FROM `tabSpoilage Child` AS sc WHERE sc.item_code = it.item_code) +
                            (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                        )
                    ) - (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code)
                ) as difference

            FROM
                `tabItem` AS it
            WHERE
                item_name = %s
            """,
            (item_name),
            as_dict=True,
        )
    elif destination_warehouse:
        return frappe.db.sql(
            """
            SELECT
                it.item_name,
                (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) AS total_opening_stock,
                COALESCE(
                    (SELECT COALESCE(SUM(sed.qty), 0) 
                     FROM `tabStock Entry Detail` AS sed
                     WHERE sed.item_code = it.item_code),
                    0
                ) AS received_qty,
                (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) 
                 FROM `tabStock Ledger Entry` AS sle
                 WHERE sle.item_code = it.item_code AND sle.actual_qty < 0) AS total_quantity_sold,
                -- COALESCE(
                --     (SELECT COALESCE(SUM(sed.qty), 0) 
                --      FROM `tabStock Entry Detail` AS sed
                --      WHERE sed.item_code = it.item_code 
                --      AND it.item_group = 'Spoilage'),
                --     0
                -- ) AS spoilage_stock,
                -- COALESCE(
                --     (SELECT se.to_warehouse FROM `tabStock Entry` AS se
                --      JOIN `tabStock Entry Detail` AS sed ON se.name = sed.parent
                --      WHERE sed.item_code = it.item_code 
                --      AND it.item_group = 'Spoilage'
                --      ORDER BY posting_date DESC LIMIT 1),
                --     'No destination warehouse'
                -- ) AS destination_warehouse,
                -- COALESCE(
                --     (SELECT MAX(posting_date) FROM `tabStock Entry` AS se
                --      JOIN `tabStock Entry Detail` AS sed ON se.name = sed.parent
                --      WHERE sed.item_code = it.item_code 
                --      AND it.item_group = 'Spoilage'),
                --     'No posting date'
                -- ) AS posting_date,

                COALESCE(
                    (SELECT t_warehouse FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code LIMIT 1)) AS destination_warehouse,
                     

                COALESCE(
                    (SELECT COALESCE(SUM(sc.qty), 0) FROM `tabSpoilage Child` AS sc WHERE sc.item_code = it.item_code)) AS spoilage_stock,

                COALESCE(
                    (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) 
                )AS system_stock,


                ((
                    (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                    (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                ) - 
                (
                    (SELECT SUM(qty) FROM `tabSpoilage Child` AS sc JOIN `tabItem` AS prod ON sc.item_code = prod.item_name) +
                    (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                )) AS expected_closing_stock,
                -- Found diff expected closing stock - system stock

                (
                    (
                        (
                            (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                            (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                        ) - 
                        (
                            (SELECT COALESCE(SUM(sc.qty), 0) FROM `tabSpoilage Child` AS sc WHERE sc.item_code = it.item_code) +
                            (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                        )
                    ) - (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code)
                ) as difference

            FROM
                `tabItem` AS it
            WHERE
                destination_warehouse = %s
            """,
            (destination_warehouse,),
            as_dict=True,

        )
    else:
        return frappe.db.sql(
            """
            SELECT
                it.item_name,
                (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) AS total_opening_stock,
                COALESCE(
                    (SELECT COALESCE(SUM(sed.qty), 0) 
                     FROM `tabStock Entry Detail` AS sed
                     WHERE sed.item_code = it.item_code),
                    0
                ) AS received_qty,
                (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) 
                 FROM `tabStock Ledger Entry` AS sle
                 WHERE sle.item_code = it.item_code AND sle.actual_qty < 0) AS total_quantity_sold,
                -- COALESCE(
                --     (SELECT COALESCE(SUM(sed.qty), 0) 
                --      FROM `tabStock Entry Detail` AS sed
                --      WHERE sed.item_code = it.item_code 
                --      AND it.item_group = 'Spoilage'),
                --     0
                -- ) AS spoilage_stock,
                -- COALESCE(
                --     (SELECT se.to_warehouse FROM `tabStock Entry` AS se
                --      JOIN `tabStock Entry Detail` AS sed ON se.name = sed.parent
                --      WHERE sed.item_code = it.item_code 
                --      AND it.item_group = 'Spoilage'
                --      ORDER BY posting_date DESC LIMIT 1),
                --     'No destination warehouse'
                -- ) AS destination_warehouse,
                -- COALESCE(
                --     (SELECT MAX(posting_date) FROM `tabStock Entry` AS se
                --      JOIN `tabStock Entry Detail` AS sed ON se.name = sed.parent
                --      WHERE sed.item_code = it.item_code 
                --      AND it.item_group = 'Spoilage'),
                --     'No posting date'
                -- ) AS posting_date,

                COALESCE(
                    (SELECT t_warehouse FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code LIMIT 1)) AS destination_warehouse,
                     

                COALESCE(
                    (SELECT COALESCE(SUM(sc.qty), 0) FROM `tabSpoilage Child` AS sc WHERE sc.item_code = it.item_code)) AS spoilage_stock,

                COALESCE(
                    (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) 
                )AS system_stock,


                ((
                    (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                    (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                ) - 
                (
                    (SELECT SUM(qty) FROM `tabSpoilage Child` AS sc JOIN `tabItem` AS prod ON sc.item_code = prod.item_name) +
                    (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                )) AS expected_closing_stock,
                -- Found diff expected closing stock - system stock

                (
                    (
                        (
                            (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                            (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                        ) - 
                        (
                            (SELECT COALESCE(SUM(sc.qty), 0) FROM `tabSpoilage Child` AS sc WHERE sc.item_code = it.item_code) +
                            (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                        )
                    ) - (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code)
                ) as difference

            FROM
                `tabItem` AS it
            -- WHERE
            --     item_name = %s
            """,
            # (item_name,),
            as_dict=True,
        )
