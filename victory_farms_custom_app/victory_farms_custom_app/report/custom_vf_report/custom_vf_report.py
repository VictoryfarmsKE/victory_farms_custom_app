# Copyright (c) 2024, Sloufy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime
from frappe.utils.dateutils import user_to_str

def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data


def get_columns(filters):
    columns = [
        # {
        #     'fieldname': 'rec_date',
        #     'label': _('Recon Date'),
        #     'fieldtype': 'Data',
        #     'width': 100
        # },
        {
            'fieldname': 'posting_date',
            'label': _('Date'),
            'fieldtype': 'Date',
            'width': 100
        },
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 120,
        },
        {
            'fieldname': 'warehouse',
            'label': _('Warehouse'),
            'fieldtype': 'Link',
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
   
    ]
    return columns
def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    format_from_date = user_to_str(from_date, 'yyyy-mm-dd')
    format_to_date = user_to_str(to_date, 'yyyy-mm-dd')
    item_code = filters.get("item_code")
    warehouse = filters.get("warehouse")
    print("::::::::::format_from_date::::::::1:::::::::::",format_from_date)
    print("::::::::::format_to_date::::::::::2:::::::::",format_to_date)
#     if item_code:
#         return frappe.db.sql(
#             """
#             SELECT
                
#                 it.item_code,
#                 it.warehouse,
#                 (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) AS total_opening_stock,
#                 COALESCE(
#                     (SELECT COALESCE(SUM(sed.qty), 0) 
#                      FROM `tabStock Entry Detail` AS sed
#                      WHERE sed.item_code = it.item_code),
#                     0
#                 ) AS received_qty,
#                 (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) 
#                  FROM `tabStock Ledger Entry` AS sle
#                  WHERE sle.item_code = it.item_code AND sle.actual_qty < 0) AS total_quantity_sold,
             
#                 sr.posting_date  AS posting_date,

#                 -- COALESCE(
#                 --     (SELECT COALESCE(SUM(sri.qty), 0) FROM `tabStock Reconciliation Item` AS sri 
#                 --     JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
#                 --     WHERE pit.item_group = 'Spoilage' and sri.item_code = pit.item_code)
#                 -- )AS spoilage_stock,

#               --  COALESCE(
#               --       (
#               --           SELECT 
#               --               CASE 
#               --                   WHEN pit.item_group = 'Spoilage' THEN COALESCE(SUM(sri.qty), 0)
#               --                   ELSE 0
#               --               END AS spoilage_stock
#               --           FROM `tabStock Reconciliation Item` AS sri 
#               --           JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
#               --           JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
#               --           WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
#               --           GROUP BY sri.item_code, bb.posting_date  -- Include item_code and posting_date in the GROUP BY clause
#               --       ), 
#               --       0
#               -- ) AS spoilage_stock,

#               -- COALESCE(
#               --       (
#               --           SELECT 
#               --               CASE 
#               --                   WHEN pit.item_group = 'Spoilage' THEN COALESCE(SUM(sri.qty), 0)
#               --                   ELSE 0
#               --               END AS spoilage_stock
#               --           FROM `tabStock Reconciliation Item` AS sri 
#               --           JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
#               --           JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
#               --           WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
#               --           GROUP BY sri.item_code, bb.posting_date  -- Include item_code and posting_date in the GROUP BY clause
#               --       ), 
#               --       0
#               -- ) AS spoilage_stock,

#                 COALESCE(
#                         (
#                             SELECT 
#                                 CASE 
#                                     WHEN pit.item_group = 'Spoilage' THEN COALESCE((sri.qty), 0)
#                                     ELSE 0
#                                 END AS spoilage_stock
#                             FROM `tabStock Reconciliation Item` AS sri 
#                             JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
#                             JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
#                             WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
#                             GROUP BY bb.posting_time DESC LIMIT 1  -- Include item_code and posting_date in the GROUP BY clause
#                         ), 
#                         0
#                   ) AS spoilage_stock,


#                 COALESCE(
#                     (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) 
#                 )AS system_stock,


#                 ((
#                     (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
#                     (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
#                 ) - 
#                 (
#                     (SELECT 
#                         CASE 
#                             WHEN pit.item_group = 'Spoilage' THEN COALESCE(SUM(sri.qty), 0)
#                             ELSE 0
#                         END AS spoilage_stock
#                     FROM `tabStock Reconciliation Item` AS sri 
#                     JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
#                     JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
#                     WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
#                     GROUP BY sri.item_code, bb.posting_date) +
#                     (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
#                 )) AS expected_closing_stock,
#                 -- Found diff expected closing stock - system stock

#                 (
#                     (
#                         (
#                             (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
#                             (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
#                         ) - 
#                         (
#                             (SELECT 
#                                 CASE 
#                                     WHEN pit.item_group = 'Spoilage' THEN COALESCE(SUM(sri.qty), 0)
#                                     ELSE 0
#                                 END AS spoilage_stock
#                             FROM `tabStock Reconciliation Item` AS sri 
#                             JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
#                             JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
#                             WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
#                             GROUP BY sri.item_code, bb.posting_date) +
#                             (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
#                         )
#                     ) - (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code)
#                 ) as difference

#             FROM
#                 `tabStock Reconciliation` AS sr
#             JOIN `tabStock Reconciliation Item` AS it ON sr.name = it.parent
#             -- JOIN 'tabItem' AS prod ON prod.item_name = it.item_name
#             WHERE 
#                 item_code = %s
#             """,
#             (item_code,),
#             as_dict=True,
# )
    # elif warehouse:
#       return frappe.db.sql(
#             """
#             SELECT
                
#                 it.item_code,
#                 it.warehouse,
#                 (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) AS total_opening_stock,
#                 COALESCE(
#                     (SELECT COALESCE(SUM(sed.qty), 0) 
#                      FROM `tabStock Entry Detail` AS sed
#                      WHERE sed.item_code = it.item_code),
#                     0
#                 ) AS received_qty,
#                 (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) 
#                  FROM `tabStock Ledger Entry` AS sle
#                  WHERE sle.item_code = it.item_code AND sle.actual_qty < 0) AS total_quantity_sold,

#                 sr.posting_date  AS posting_date,
#                 COALESCE(
#                     (SELECT t_warehouse FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code LIMIT 1)) AS destination_warehouse,
                     

#                 -- COALESCE(
#                 --     (SELECT COALESCE(SUM(sri.qty), 0) FROM `tabStock Reconciliation Item` AS sri 
#                 --     JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
#                 --     WHERE pit.item_group = 'Spoilage' and sri.item_code = pit.item_code)
#                 -- )AS spoilage_stock,

#                COALESCE(
#                     (
#                         SELECT 
# 	                        CASE 
# 	                            WHEN pit.item_group = 'Spoilage' THEN COALESCE(SUM(sri.qty), 0)
# 	                            ELSE 0
# 	                        END AS spoilage_stock
#                         FROM `tabStock Reconciliation Item` AS sri 
#                         JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
#                         JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
#                         WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
#                         GROUP BY sri.item_code, bb.posting_date  -- Include item_code and posting_date in the GROUP BY clause
#                     ), 
#                     0
#               ) AS spoilage_stock,

#                 COALESCE((SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code)) AS system_stock,


#                 ((
#                     (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
#                     (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
#                 ) - 
#                 (
#                     (SELECT 
#                         CASE 
#                             WHEN pit.item_group = 'Spoilage' THEN COALESCE(SUM(sri.qty), 0)
#                             ELSE 0
#                         END AS spoilage_stock
#                     FROM `tabStock Reconciliation Item` AS sri 
#                     JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
#                     JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
#                     WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
#                     GROUP BY sri.item_code, bb.posting_date) +
#                     (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
#                 )) AS expected_closing_stock,
#                 -- Found diff expected closing stock - system stock

#                 (
#                     (
#                         (
#                             (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
#                             (SELECT COALESCE(SUM(sed.qty), 0)  FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
#                         ) - 
#                         (
#                             (SELECT 
# 	                            CASE 
# 	                                WHEN pit.item_group = 'Spoilage' THEN COALESCE(SUM(sri.qty), 0)
# 	                                ELSE 0
# 	                            END AS spoilage_stock
# 	                        FROM `tabStock Reconciliation Item` AS sri 
# 	                        JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
# 	                        JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
# 	                        WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
# 	                        GROUP BY sri.item_code, bb.posting_date) +
#                             (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
#                         )
#                     ) - (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code)
#                 ) as difference

#             FROM
#                 `tabStock Reconciliation` AS sr
#             JOIN `tabStock Reconciliation Item` AS it ON sr.name = it.parent
#             -- JOIN 'tabItem' AS prod ON prod.item_name = it.item_name
#             WHERE 
#                 warehouse = %s
#             """,
#             (warehouse,),
#             as_dict=True,
#         )
    if item_code:
        return frappe.db.sql(
    """
    SELECT
        it.item_code,
        it.warehouse,
        COALESCE(
            (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code),
            0
        ) AS total_opening_stock,
        COALESCE(
            (SELECT COALESCE(SUM(sed.qty), 0) FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code),
            0
        ) AS received_qty,
        COALESCE(
            (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0),
            0
        ) AS total_quantity_sold,
        sr.posting_date AS posting_date,
        COALESCE(
            (
                SELECT COALESCE((CASE WHEN pit.item_group = 'Spoilage' THEN sri.qty ELSE 0 END), 0)
                FROM `tabStock Reconciliation Item` AS sri 
                JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
                JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
                WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
                GROUP BY bb.posting_time DESC LIMIT 1
            ), 
            0
        ) AS spoilage_stock,
        COALESCE(
            (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code),
            0
        ) AS system_stock,
        COALESCE(
            (
                (
                    (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                    (SELECT COALESCE(SUM(sed.qty), 0) FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                ) 
                - 
                (
                    COALESCE(
                        (
                            SELECT COALESCE((CASE WHEN pit.item_group = 'Spoilage' THEN sri.qty ELSE 0 END), 0)
                            FROM `tabStock Reconciliation Item` AS sri 
                            JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
                            JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
                            WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
                            GROUP BY bb.posting_time DESC LIMIT 1
                        ), 
                        0
                    )
                    +
                    (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                )
            ),
            0
        ) AS expected_closing_stock,
        COALESCE(
            (
                (
                    (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                    (SELECT COALESCE(SUM(sed.qty), 0) FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                ) 
                - 
                (
                    COALESCE(
                        (
                            SELECT COALESCE((CASE WHEN pit.item_group = 'Spoilage' THEN sri.qty ELSE 0 END), 0)
                            FROM `tabStock Reconciliation Item` AS sri 
                            JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
                            JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
                            WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
                            GROUP BY bb.posting_time DESC LIMIT 1
                        ), 
                        0
                    )
                    +
                    (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                )
            )
            -
            (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code)
        ) AS difference
    FROM
        `tabStock Reconciliation` AS sr
    JOIN `tabStock Reconciliation Item` AS it ON sr.name = it.parent
    WHERE
        it.item_code = %s
    GROUP BY it.item_code
    """,
    (item_code),
    as_dict=True,
)
    elif warehouse:
            return frappe.db.sql(
        """
        SELECT
            it.item_code,
            it.warehouse,
            COALESCE(
                (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code),
                0
            ) AS total_opening_stock,
            COALESCE(
                (SELECT COALESCE(SUM(sed.qty), 0) FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code),
                0
            ) AS received_qty,
            COALESCE(
                (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0),
                0
            ) AS total_quantity_sold,
            sr.posting_date AS posting_date,
            COALESCE(
                (
                    SELECT COALESCE((CASE WHEN pit.item_group = 'Spoilage' THEN sri.qty ELSE 0 END), 0)
                    FROM `tabStock Reconciliation Item` AS sri 
                    JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
                    JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
                    WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
                    GROUP BY bb.posting_time DESC LIMIT 1
                ), 
                0
            ) AS spoilage_stock,
            COALESCE(
                (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code),
                0
            ) AS system_stock,
            COALESCE(
                (
                    (
                        (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                        (SELECT COALESCE(SUM(sed.qty), 0) FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                    ) 
                    - 
                    (
                        COALESCE(
                            (
                                SELECT COALESCE((CASE WHEN pit.item_group = 'Spoilage' THEN sri.qty ELSE 0 END), 0)
                                FROM `tabStock Reconciliation Item` AS sri 
                                JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
                                JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
                                WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
                                GROUP BY bb.posting_time DESC LIMIT 1
                            ), 
                            0
                        )
                        +
                        (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                    )
                ),
                0
            ) AS expected_closing_stock,
            COALESCE(
                (
                    (
                        (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                        (SELECT COALESCE(SUM(sed.qty), 0) FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                    ) 
                    - 
                    (
                        COALESCE(
                            (
                                SELECT COALESCE((CASE WHEN pit.item_group = 'Spoilage' THEN sri.qty ELSE 0 END), 0)
                                FROM `tabStock Reconciliation Item` AS sri 
                                JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
                                JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
                                WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
                                GROUP BY bb.posting_time DESC LIMIT 1
                            ), 
                            0
                        )
                        +
                        (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                    )
                )
                -
                (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code)
            ) AS difference
        FROM
            `tabStock Reconciliation` AS sr
        JOIN `tabStock Reconciliation Item` AS it ON sr.name = it.parent
        WHERE 
            it.warehouse = %s
        GROUP BY it.warehouse
        """,
        (warehouse),
        as_dict=True,
    )
    else:
            return frappe.db.sql(
        """
        SELECT
            it.item_code,
            it.warehouse,
            COALESCE(
                (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code),
                0
            ) AS total_opening_stock,
            COALESCE(
                (SELECT COALESCE(SUM(sed.qty), 0) FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code),
                0
            ) AS received_qty,
            COALESCE(
                (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0),
                0
            ) AS total_quantity_sold,
            sr.posting_date AS posting_date,
            COALESCE(
                (
                    SELECT COALESCE((CASE WHEN pit.item_group = 'Spoilage' THEN sri.qty ELSE 0 END), 0)
                    FROM `tabStock Reconciliation Item` AS sri 
                    JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
                    JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
                    WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
                    GROUP BY bb.posting_time DESC LIMIT 1
                ), 
                0
            ) AS spoilage_stock,
            COALESCE(
                (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code),
                0
            ) AS system_stock,
            COALESCE(
                (
                    (
                        (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                        (SELECT COALESCE(SUM(sed.qty), 0) FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                    ) 
                    - 
                    (
                        COALESCE(
                            (
                                SELECT COALESCE((CASE WHEN pit.item_group = 'Spoilage' THEN sri.qty ELSE 0 END), 0)
                                FROM `tabStock Reconciliation Item` AS sri 
                                JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
                                JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
                                WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
                                GROUP BY bb.posting_time DESC LIMIT 1
                            ), 
                            0
                        )
                        +
                        (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                    )
                ),
                0
            ) AS expected_closing_stock,
            COALESCE(
                (
                    (
                        (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code) +
                        (SELECT COALESCE(SUM(sed.qty), 0) FROM `tabStock Entry Detail` AS sed WHERE sed.item_code = it.item_code)
                    ) 
                    - 
                    (
                        COALESCE(
                            (
                                SELECT COALESCE((CASE WHEN pit.item_group = 'Spoilage' THEN sri.qty ELSE 0 END), 0)
                                FROM `tabStock Reconciliation Item` AS sri 
                                JOIN `tabItem` AS pit ON pit.item_code = sri.item_code
                                JOIN `tabStock Reconciliation` AS bb ON bb.name = sri.parent
                                WHERE pit.item_group = 'Spoilage' AND sri.item_code = it.item_code AND bb.posting_date = sr.posting_date
                                GROUP BY bb.posting_time DESC LIMIT 1
                            ), 
                            0
                        )
                        +
                        (SELECT COALESCE(SUM(ABS(sle.actual_qty)), 0) FROM `tabStock Ledger Entry` AS sle WHERE sle.item_code = it.item_code AND sle.actual_qty < 0)
                    )
                )
                -
                (SELECT COALESCE(SUM(st.actual_qty), 0) FROM `tabBin` AS st WHERE st.item_code = it.item_code)
            ) AS difference
        FROM
            `tabStock Reconciliation` AS sr
        JOIN `tabStock Reconciliation Item` AS it ON sr.name = it.parent
        WHERE 
            sr.posting_date BETWEEN %s AND %s
        GROUP BY sr.posting_date
        """,
        (format_from_date, format_to_date),
        as_dict=True,
    )


