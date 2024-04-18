# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from itertools import filterfalse
from erpnext.stock.utils import get_stock_balance 

def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters, columns)
    return columns, data

def get_columns():
    return [
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
            'fieldtype': 'Float',
            'width': 120,
            'align': 'right'
        },
        {
            'fieldname': 'received_qty',
            'label': _('In Stock'),
            'fieldtype': 'Float',
            'width': 130,
            'align': 'right'
        },
        {
            'fieldname': 'total_quantity_sold',
            'label': _('Out Stock'),
            'fieldtype': 'Float',
            'width': 100,
            'align': 'right'
        },
        {
            'fieldname': 'spoilage_stock',
            'label': _('Spoilage Stock'),
            'fieldtype': 'Float',
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
        }
        # {
        #     'fieldname': 'item_group',
        #     'label': _('Item Group'),
        #     'fieldtype': 'Data',
        #     'width': 100,
        #     'hide': 0,
        # }
    ]


def get_data(filters, columns):
    query_filters = {}

    # Check if filters are provided
    if filters:
        if filters.get("item_code"):
            query_filters["item_code"] = filters["item_code"]
        if filters.get("warehouse"):
            query_filters["warehouse"] = filters["warehouse"]
        if filters.get("item_group"):
            query_filters["custom_item_group"] = filters["item_group"]
        if filters.get("from_date") and filters.get("to_date"):
            query_filters["posting_date"] = ["between", [filters["from_date"], filters["to_date"]]]

    # Fetch data from the Stock Ledger Entry table based on filters

    query = frappe.get_all(
        "Stock Ledger Entry",
        filters=query_filters,
        fields=["posting_date", "name"]
    )

    result = []

    # Process the query results
    for qr in query:
        ledger_entry = frappe.get_doc("Stock Ledger Entry", qr.name)
        end_date = ledger_entry.posting_date + relativedelta(days=-1)
        # item = ledger_entry.item_code
        # it_grp = frappe.get_doc("Item",item)
        # itm_group = it_grp.item_group
        total_opening_stock = get_opening_stock(ledger_entry.item_code, ledger_entry.warehouse, end_date)
        received_qty = get_received_qty(ledger_entry.item_code, ledger_entry.warehouse, ledger_entry.posting_date)
        total_quantity_sold = get_quantity_sold(ledger_entry.item_code, ledger_entry.warehouse, ledger_entry.posting_date)
        spoilage_stock = get_spoilage_stock(ledger_entry.item_code, ledger_entry.warehouse, ledger_entry.posting_date)
        # item_grp = itm_group

        data = {
            "posting_date": ledger_entry.posting_date,
            "item_code": ledger_entry.item_code,
            "warehouse": ledger_entry.warehouse,
            "total_opening_stock": total_opening_stock,
            "received_qty": received_qty,
            "total_quantity_sold": total_quantity_sold,
            "spoilage_stock": spoilage_stock,
            "expected_closing_stock": (total_opening_stock + received_qty) - (abs(total_quantity_sold) + 0.0),
            "system_stock": total_opening_stock,
            "difference": (total_opening_stock + received_qty) - (abs(total_quantity_sold) + 0.0) - total_opening_stock
            # "item_group": item_grp
        }
        result.append(data)

    # Remove duplicates METHOD 1
    unique_result = list({tuple(sorted(d.items())): d for d in result}.values())
    # Remove duplicates METHOD 2
    # unique_result = []
    # seen = set()
    # for d in result:
    #     t = tuple(sorted(d.items()))
    #     if t not in seen:
    #         seen.add(t)
    #         unique_result.append(d)

    return unique_result
def get_opening_stock(item_code, warehouse, end_date):
    blnc_qty = get_stock_balance( item_code=item_code, warehouse=warehouse, posting_date=end_date)

    # capacity_data = frappe.db.get_all(
    #     "Putaway Rule",
    #     fields=["item_code", "warehouse", "stock_capacity", "company"],
    #     filters=filters,
    #     # limit_start=start,
    #     # limit_page_length="11",
    # )

    # for entry in capacity_data:
    #     balance_qty = get_stock_balance(entry.item_code, entry.warehouse, nowdate()) or 0
    #     entry.update(
    #         {
    #             "actual_qty": balance_qty,
    #             "percent_occupied": flt((flt(balance_qty) / flt(entry.stock_capacity)) * 100, 0),
    #         }
    #     )
    # opening_stock = frappe.db.sql("""
    #     SELECT COALESCE(SUM(item.qty), 0)
    #     FROM `tabStock Ledger Entry` AS sr
    #     JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
    #     WHERE item.item_code = %s AND item.warehouse = %s AND sr.posting_date <= %s
    #         -- AND sr.purpose = 'Opening Stock'
    # """, (item_code, warehouse, end_date))[0][0]
    return blnc_qty or 0.0



def get_received_qty(item_code, warehouse, posting_date):
    # #Now Date Received Stock
    # received_qty = get_stock_balance(item_code=item_code, warehouse=warehouse, posting_date=posting_date)
    # Use a parameterized query to avoid SQL injection
    received_qty = frappe.db.sql("""
        SELECT COALESCE(SUM(item.qty), 0)
        FROM `tabStock Reconciliation` AS sr
        JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
        WHERE item.item_code = %s AND item.warehouse = %s AND sr.posting_date = %s
            -- AND sr.purpose = 'Stock Reconciliation'
        
        UNION ALL

        SELECT COALESCE(SUM(item.qty), 0)
        FROM `tabStock Entry` AS se
        JOIN `tabStock Entry Detail` AS item ON se.name = item.parent
        WHERE item.item_code = %s AND item.t_warehouse = %s
            AND se.stock_entry_type = 'Material Transfer'
    """, (item_code, warehouse, posting_date, item_code, warehouse))

    # Extract the first element of each tuple and then sum
    return sum(entry[0] for entry in received_qty) or 0.0
    # return received_qty or 0.0





def get_quantity_sold(item_code, warehouse, posting_date):
    quantity_sold = frappe.db.sql("""
        SELECT COALESCE(SUM(CASE WHEN sle.actual_qty < 0 THEN sle.actual_qty ELSE 0 END), 0)
        FROM `tabStock Ledger Entry` AS sle
        WHERE sle.item_code = %s AND sle.warehouse = %s AND sle.posting_date = %s
    """, (item_code, warehouse, posting_date))[0][0]

    return abs(quantity_sold)


def get_spoilage_stock(item_code, warehouse, posting_date):
    spoilage_st = frappe.db.sql("""
        SELECT COALESCE(SUM(item.qty), 0)
        FROM `tabStock Entry` AS se
        JOIN `tabItem Summery` AS item ON se.name = item.parent
        WHERE item.item = %s
            AND se.stock_entry_type = 'Repack Spoilage'
            AND se.posting_date = %s 
    """, (item_code, posting_date))
    # Extract the first element of each tuple and then sum
    return sum(entry[0] for entry in spoilage_st) or 0.0



# def get_item_groups(item_code, warehouse, posting_date):
#     it_group = frappe.db.sql("""
#         SELECT COALESCE(item.item_group, 0)
#         FROM `tabStock Ledger Entry` AS sle
#         LEFT JOIN `tabItem` AS item ON sle.item_code = item.item_code
#         WHERE sle.item_code = %s 
#             AND sle.posting_date = %s
#             AND sle.warehouse = %s
#     """, (item_code, posting_date, warehouse))
    
#     # Extract item group values from tuples
#     item_groups = [group[0] for group in it_group]
#     return item_groups



