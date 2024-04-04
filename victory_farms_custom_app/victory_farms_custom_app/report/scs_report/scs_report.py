# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data



# import frappe
# from frappe import _

# def execute(filters=None):
#     columns, data = [], []
#     columns = get_columns()
#     data = get_data(filters, columns)
#     return columns, data

# def get_columns():
#     return [
#         {
#             'fieldname': 'posting_date',
#             'label': _('Date'),
#             'fieldtype': 'Date',
#             'width': 100
#         },
#         {
#             "label": _("Item Code"),
#             "fieldname": "item_code",
#             "fieldtype": "Link",
#             "options": "Item",
#             "width": 120,
#         },
#         {
#             'fieldname': 'warehouse',
#             'label': _('Warehouse'),
#             'fieldtype': 'Link',
#             "options": "Warehouse",
#             'width': 100,
#             'align': 'left'
#         },
#         {
#             'fieldname': 'total_opening_stock',
#             'label': _('Opening Stock'),
#             'fieldtype': 'Float',
#             'width': 120,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'received_qty',
#             'label': _('In Stock'),
#             'fieldtype': 'Float',
#             'width': 130,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'total_quantity_sold',
#             'label': _('Out Stock'),
#             'fieldtype': 'Float',
#             'width': 100,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'spoilage_stock',
#             'label': _('Spoilage Stock'),
#             'fieldtype': 'Float',
#             'width': 120,
#             'align': 'right'
#         },
# 		{
#             'fieldname': 'expected_closing_stock',
#             'label': _('Expected Closing Stock'),
#             'fieldtype': 'Data',
#             'width': 160,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'system_stock',
#             'label': _('System Stock'),
#             'fieldtype': 'Data',
#             'width': 120,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'difference',
#             'label': _('Difference'),
#             'fieldtype': 'Data',
#             'width': 100,
#             'align': 'right'
#         }
#     ]

# def get_data(filters, columns):
#     query_filters = {}
#     if filters and filters.get("item_code"):
#         query_filters["item_code"] = filters["item_code"]
#     if filters and filters.get("warehouse"):
#         query_filters["warehouse"] = filters["warehouse"]
#     if filters and filters.get("from_date") and filters.get("to_date"):
#         query_filters["posting_date"] = ["between", [filters["from_date"], filters["to_date"]]]

#     query = frappe.get_all(
#         "Stock Reconciliation",
#         filters=query_filters,
#         fields=["posting_date", "name"]
#     )
#     result = []
#     if query:
#         for qr in query:
#             reconciliation = frappe.get_doc("Stock Reconciliation", qr.name)
#             for item in reconciliation.items:
#                 total_opening_stock = get_opening_stock(item.item_code)
#                 received_qty = get_received_qty(item.item_code)
#                 total_quantity_sold = get_quantity_sold(item.item_code)
#                 warehouse = get_warehouse(item.item_code)
                
#                 spoilage_stock = 0.0
#                 # Check if the item belongs to the "Spoilage" item group
#                 item_doc = frappe.get_doc("Item", item.item_code)
#                 if item_doc.item_group == "Spoilage":
#                     spoilage_stock = total_quantity_sold
                
#                 data = {
#                     "posting_date": qr.posting_date, 
#                     "item_code": item.item_code,
#                     "warehouse": warehouse,
#                     "total_opening_stock": total_opening_stock,
#                     "received_qty": received_qty,
#                     "total_quantity_sold": total_quantity_sold,
#                     "spoilage_stock": spoilage_stock,
#                     "expected_closing_stock": (total_opening_stock + received_qty) - (abs(total_quantity_sold) + spoilage_stock),
#                     "system_stock": total_opening_stock,
#                     "difference" : (total_opening_stock + received_qty) - (total_quantity_sold + spoilage_stock) - total_opening_stock	
#                 }
#                 result.append(data)

#     # Debug print statements
#     print("Result:", result)

#     return result

# def get_opening_stock(item_code):
#     opening_stock = frappe.db.sql("""
#         SELECT COALESCE(SUM(item.qty), 0)
#         FROM `tabStock Reconciliation` AS sr
#         JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
#         WHERE item.item_code = %s
#             AND sr.purpose = 'Opening Stock'
#     """, (item_code))[0][0]

#     return opening_stock or 0.0

# def get_received_qty(item_code):
#     # Use a parameterized query to avoid SQL injection
#     received_qty = frappe.db.sql("""
#         SELECT COALESCE(SUM(item.qty), 0)
#         FROM `tabStock Reconciliation` AS sr
#         JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
#         WHERE item.item_code = %s
#             AND sr.purpose = 'Stock Reconciliation'
#     """, (item_code))[0][0]

#     return received_qty or 0.0



# def get_quantity_sold(item_code):
#     quantity_sold = frappe.db.sql("""
#         SELECT COALESCE(SUM(sle.actual_qty), 0)
#         FROM `tabStock Ledger Entry` AS sle
#         WHERE sle.item_code = %s
#     """, (item_code))[0][0]
#     return quantity_sold  # Take the absolute value to get the total outgoing quantity


# def get_warehouse(item_code):
#     warehouse = frappe.db.sql("""
#         SELECT sle.warehouse
#         FROM `tabStock Ledger Entry` AS sle
#         WHERE sle.item_code = %s
#     """, (item_code))[0][0]

#     return warehouse if warehouse else ""  # Return an empty string if warehouse is None




# import frappe
# from frappe import _

# def execute(filters=None):
#     columns, data = [], []
#     columns = get_columns()
#     data = get_data(filters, columns)
#     return columns, data

# def get_columns():
#     return [
#         {
#             'fieldname': 'posting_date',
#             'label': _('Date'),
#             'fieldtype': 'Date',
#             'width': 100
#         },
#         {
#             "label": _("Item Code"),
#             "fieldname": "item_code",
#             "fieldtype": "Link",
#             "options": "Item",
#             "width": 120,
#         },
#         {
#             'fieldname': 'warehouse',
#             'label': _('Warehouse'),
#             'fieldtype': 'Link',
#             "options": "Warehouse",
#             'width': 100,
#             'align': 'left'
#         },
#         {
#             'fieldname': 'total_opening_stock',
#             'label': _('Opening Stock'),
#             'fieldtype': 'Float',
#             'width': 120,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'received_qty',
#             'label': _('In Stock'),
#             'fieldtype': 'Float',
#             'width': 130,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'total_quantity_sold',
#             'label': _('Out Stock'),
#             'fieldtype': 'Float',
#             'width': 100,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'spoilage_stock',
#             'label': _('Spoilage Stock'),
#             'fieldtype': 'Float',
#             'width': 120,
#             'align': 'right'
#         },
# 		{
#             'fieldname': 'expected_closing_stock',
#             'label': _('Expected Closing Stock'),
#             'fieldtype': 'Data',
#             'width': 160,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'system_stock',
#             'label': _('System Stock'),
#             'fieldtype': 'Data',
#             'width': 120,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'difference',
#             'label': _('Difference'),
#             'fieldtype': 'Data',
#             'width': 100,
#             'align': 'right'
#         }
#     ]

# def get_data(filters, columns):
#     query_filters = {}
#     if filters and filters.get("item_code"):
#         query_filters["item_code"] = filters["item_code"]
#     if filters and filters.get("warehouse"):
#         query_filters["warehouse"] = filters["warehouse"]
#     if filters and filters.get("from_date") and filters.get("to_date"):
#         query_filters["posting_date"] = ["between", [filters["from_date"], filters["to_date"]]]

#     query = frappe.get_all(
#         "Stock Ledger Entry",
#         filters=query_filters,
#         fields=["posting_date", "name"]
#     )
#     result = []
#     if query:
#         for qr in query:
#             ledger_entry = frappe.get_doc("Stock Ledger Entry", qr.name)
#             # for item in reconciliation.items:
#             total_opening_stock = get_opening_stock(ledger_entry.item_code, ledger_entry.warehouse)
#             received_qty = get_received_qty(ledger_entry.item_code, ledger_entry.warehouse)
#             total_quantity_sold = get_quantity_sold(ledger_entry.item_code, ledger_entry.warehouse)
#                 # warehouse = get_warehouse(item.item_code)
                
#                 # spoilage_stock = 0.0
#                 # Check if the item belongs to the "Spoilage" item group
#                 # item_doc = frappe.get_doc("Item", item.item_code)
#                 # if item_doc.item_group == "Spoilage":
#                 #     spoilage_stock = total_quantity_sold
                
#             data = {
#                 "posting_date": ledger_entry.posting_date, 
#                 "item_code": ledger_entry.item_code,
#                 "warehouse": ledger_entry.warehouse,
#                 "total_opening_stock": total_opening_stock,
#                 "received_qty": received_qty,
#                 "total_quantity_sold": total_quantity_sold
#                 #     "spoilage_stock": spoilage_stock,
#                 #     "expected_closing_stock": (total_opening_stock + received_qty) - (abs(total_quantity_sold) + spoilage_stock),
#                 #     "system_stock": total_opening_stock,
#                 #     "difference" : (total_opening_stock + received_qty) - (total_quantity_sold + spoilage_stock) - total_opening_stock	
#             }
#             result.append(data)

#     # Debug print statements
#     # print("Result:", result)

#     return result

# def get_opening_stock(item_code,warehouse):
#     opening_stock = frappe.db.sql("""
#         SELECT COALESCE(SUM(item.qty), 0)
#         FROM `tabStock Reconciliation` AS sr
#         JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
#         WHERE item.item_code = %s AND item.warehouse = %s
#             AND sr.purpose = 'Opening Stock'
#     """, (item_code, warehouse))[0][0]

#     return opening_stock or 0.0

# # def get_received_qty(item_code, warehouse):
# #     # Use a parameterized query to avoid SQL injection
# #     received_qty = frappe.db.sql("""
# #         SELECT COALESCE(SUM(item.qty), 0)
# #         FROM `tabStock Reconciliation` AS sr
# #         JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
# #         WHERE item.item_code = %s AND item.warehouse = %s
# #             AND sr.purpose = 'Stock Reconciliation'
# #     """, (item_code, warehouse))[0][0]
# #     return received_qty or 0.0

# # def get_received_qty(item_code, warehouse):
# #     # Use a parameterized query to avoid SQL injection
# #     received_qty = frappe.db.sql("""
# #         SELECT COALESCE(SUM(item.qty), 0)
# #         FROM `tabStock Entry` AS sr
# #         JOIN `tabStock Entry Detail` AS item ON sr.name = item.parent
# #         WHERE item.item_code = %s AND item.t_warehouse = %s
# #             AND sr.stock_entry_type = 'Material Transfer'
# #     """, (item_code, warehouse))[0][0]
# #     return received_qty or 0.0


# def get_received_qty(item_code, warehouse):
#     # Use a parameterized query to avoid SQL injection
#     received_qty = frappe.db.sql("""
#         SELECT COALESCE(SUM(item.qty), 0)
#         FROM `tabStock Reconciliation` AS sr
#         JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
#         WHERE item.item_code = %s AND item.warehouse = %s
#             AND sr.purpose = 'Stock Reconciliation'
        
#         UNION ALL

#         SELECT COALESCE(SUM(item.qty), 0)
#         FROM `tabStock Entry` AS se
#         JOIN `tabStock Entry Detail` AS item ON se.name = item.parent
#         WHERE item.item_code = %s AND item.t_warehouse = %s
#             AND se.stock_entry_type = 'Material Transfer'
#     """, (item_code, warehouse, item_code, warehouse))

#     # Extract the first element of each tuple and then sum
#     return sum(entry[0] for entry in received_qty) or 0.0




# def get_quantity_sold(item_code, warehouse):
#     quantity_sold = frappe.db.sql("""
#         SELECT COALESCE(SUM(CASE WHEN sle.actual_qty < 0 THEN sle.actual_qty ELSE 0 END), 0)
#         FROM `tabStock Ledger Entry` AS sle
#         WHERE sle.item_code = %s AND sle.warehouse = %s
#     """, (item_code, warehouse))[0][0]

#     return abs(quantity_sold




# import frappe
# from frappe import _

# def execute(filters=None):
#     columns, data = [], []
#     columns = get_columns()
#     data = get_data(filters, columns)
#     return columns, data

# def get_columns():
#     return [
#         {
#             'fieldname': 'posting_date',
#             'label': _('Date'),
#             'fieldtype': 'Date',
#             'width': 100
#         },
#         {
#             "label": _("Item Code"),
#             "fieldname": "item_code",
#             "fieldtype": "Link",
#             "options": "Item",
#             "width": 120,
#         },
#         {
#             'fieldname': 'warehouse',
#             'label': _('Warehouse'),
#             'fieldtype': 'Link',
#             "options": "Warehouse",
#             'width': 100,
#             'align': 'left'
#         },
#         {
#             'fieldname': 'total_opening_stock',
#             'label': _('Opening Stock'),
#             'fieldtype': 'Float',
#             'width': 120,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'received_qty',
#             'label': _('In Stock'),
#             'fieldtype': 'Float',
#             'width': 130,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'total_quantity_sold',
#             'label': _('Out Stock'),
#             'fieldtype': 'Float',
#             'width': 100,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'spoilage_stock',
#             'label': _('Spoilage Stock'),
#             'fieldtype': 'Float',
#             'width': 120,
#             'align': 'right'
#         },
# 		{
#             'fieldname': 'expected_closing_stock',
#             'label': _('Expected Closing Stock'),
#             'fieldtype': 'Data',
#             'width': 160,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'system_stock',
#             'label': _('System Stock'),
#             'fieldtype': 'Data',
#             'width': 120,
#             'align': 'right'
#         },
#         {
#             'fieldname': 'difference',
#             'label': _('Difference'),
#             'fieldtype': 'Data',
#             'width': 100,
#             'align': 'right'
#         }
#     ]

# def get_data(filters, columns):
#     query_filters = {}

#     # Check if filters are provided
#     if filters:
#         if filters.get("item_code"):
#             query_filters["item_code"] = filters["item_code"]
#         if filters.get("warehouse"):
#             query_filters["warehouse"] = filters["warehouse"]
#         if filters.get("from_date") and filters.get("to_date"):
#             query_filters["posting_date"] = ["between", [filters["from_date"], filters["to_date"]]]

#     # Fetch data from the Stock Ledger Entry table based on filters
#     query = frappe.get_all(
#         "Stock Ledger Entry",
#         filters=query_filters,
#         fields=["posting_date", "name"]
#     )

#     result = []
#     al_wr = []

#     # Process the query results
#     for qr in query:
#         ledger_entry = frappe.get_doc("Stock Ledger Entry", qr.name)
#         total_opening_stock = get_opening_stock(ledger_entry.item_code, ledger_entry.warehouse)
#         received_qty = get_received_qty(ledger_entry.item_code, ledger_entry.warehouse)
#         total_quantity_sold = get_quantity_sold(ledger_entry.item_code, ledger_entry.warehouse)

#         if ledger_entry.warehouse not in al_wr:
#             al_wr.append(ledger_entry.warehouse)
#             data = {
#                 "posting_date": ledger_entry.posting_date,
#                 "item_code": ledger_entry.item_code,
#                 "warehouse": ledger_entry.warehouse,
#                 "total_opening_stock": total_opening_stock,
#                 "received_qty": received_qty,
#                 "total_quantity_sold": total_quantity_sold,
#                 "spoilage_stock": 0.0,  # Placeholder for spoilage stock (you may adjust this based on your logic)
#                 "expected_closing_stock": (total_opening_stock + received_qty) - (abs(total_quantity_sold) + 0.0),
#                 "system_stock": total_opening_stock,
#                 "difference": (total_opening_stock + received_qty) - (abs(total_quantity_sold) + 0.0) - total_opening_stock
#             }
#             result.append(data)

#     return result


# def get_opening_stock(item_code,warehouse):
#     opening_stock = frappe.db.sql("""
#         SELECT COALESCE(SUM(item.qty), 0)
#         FROM `tabStock Reconciliation` AS sr
#         JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
#         WHERE item.item_code = %s AND item.warehouse = %s
#             AND sr.purpose = 'Opening Stock'
#     """, (item_code, warehouse))[0][0]

#     return opening_stock or 0.0


# def get_received_qty(item_code, warehouse):
#     # Use a parameterized query to avoid SQL injection
#     received_qty = frappe.db.sql("""
#         SELECT COALESCE(SUM(item.qty), 0)
#         FROM `tabStock Reconciliation` AS sr
#         JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
#         WHERE item.item_code = %s AND item.warehouse = %s
#             AND sr.purpose = 'Stock Reconciliation'
        
#         UNION ALL

#         SELECT COALESCE(SUM(item.qty), 0)
#         FROM `tabStock Entry` AS se
#         JOIN `tabStock Entry Detail` AS item ON se.name = item.parent
#         WHERE item.item_code = %s AND item.t_warehouse = %s
#             AND se.stock_entry_type = 'Material Transfer'
#     """, (item_code, warehouse, item_code, warehouse))

#     # Extract the first element of each tuple and then sum
#     return sum(entry[0] for entry in received_qty) or 0.0




# def get_quantity_sold(item_code, warehouse):
#     quantity_sold = frappe.db.sql("""
#         SELECT COALESCE(SUM(CASE WHEN sle.actual_qty < 0 THEN sle.actual_qty ELSE 0 END), 0)
#         FROM `tabStock Ledger Entry` AS sle
#         WHERE sle.item_code = %s AND sle.warehouse = %s
#     """, (item_code, warehouse))[0][0]

#     return abs(quantity_sold)



import frappe
from frappe import _
# from iteration_utilities import unique_everseen

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
    ]

def get_data(filters, columns):
    query_filters = {}

    # Check if filters are provided
    if filters:
        if filters.get("item_code"):
            query_filters["item_code"] = filters["item_code"]
        if filters.get("warehouse"):
            query_filters["warehouse"] = filters["warehouse"]
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
        item = ledger_entry.item_code
        spoilage_it = frappe.get_doc("Item",item)
        total_opening_stock = get_opening_stock(ledger_entry.item_code, ledger_entry.warehouse, ledger_entry.posting_date)
        received_qty = get_received_qty(ledger_entry.item_code, ledger_entry.warehouse)
        total_quantity_sold = get_quantity_sold(ledger_entry.item_code, ledger_entry.warehouse)
        spoilage_stock = get_spoilage_stock(spoilage_it.custom_spoilage_item, ledger_entry.warehouse)
        data = {
            "posting_date": ledger_entry.posting_date,
            "item_code": ledger_entry.item_code,
            "warehouse": ledger_entry.warehouse,
            "total_opening_stock": total_opening_stock,
            "received_qty": received_qty,
            "total_quantity_sold": total_quantity_sold,
            "spoilage_stock": spoilage_stock,  # Placeholder for spoilage stock (you may adjust this based on your logic)
            "expected_closing_stock": (total_opening_stock + received_qty) - (abs(total_quantity_sold) + 0.0),
            "system_stock": total_opening_stock,
            "difference": (total_opening_stock + received_qty) - (abs(total_quantity_sold) + 0.0) - total_opening_stock
        }
        # list(unique_everseen(data))
        result.append(data)
    return result


def get_opening_stock(item_code,warehouse,posting_date):
    opening_stock = frappe.db.sql("""
        SELECT COALESCE(SUM(item.qty), 0)
        FROM `tabStock Reconciliation` AS sr
        JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
        WHERE item.item_code = %s AND item.warehouse = %s AND sr.posting_date = %s
            -- AND sr.purpose = 'Opening Stock'
    """, (item_code, warehouse, posting_date))[0][0]

    return opening_stock or 0.0


def get_received_qty(item_code, warehouse):
    # Use a parameterized query to avoid SQL injection
    received_qty = frappe.db.sql("""
        SELECT COALESCE(SUM(item.qty), 0)
        FROM `tabStock Reconciliation` AS sr
        JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
        WHERE item.item_code = %s AND item.warehouse = %s
            AND sr.purpose = 'Stock Reconciliation'
        
        UNION ALL

        SELECT COALESCE(SUM(item.qty), 0)
        FROM `tabStock Entry` AS se
        JOIN `tabStock Entry Detail` AS item ON se.name = item.parent
        WHERE item.item_code = %s AND item.t_warehouse = %s
            AND se.stock_entry_type = 'Material Transfer'
    """, (item_code, warehouse, item_code, warehouse))

    # Extract the first element of each tuple and then sum
    return sum(entry[0] for entry in received_qty) or 0.0




def get_quantity_sold(item_code, warehouse):
    quantity_sold = frappe.db.sql("""
        SELECT COALESCE(SUM(CASE WHEN sle.actual_qty < 0 THEN sle.actual_qty ELSE 0 END), 0)
        FROM `tabStock Ledger Entry` AS sle
        WHERE sle.item_code = %s AND sle.warehouse = %s
    """, (item_code, warehouse))[0][0]

    return abs(quantity_sold)


def get_spoilage_stock(item_code, warehouse):
    spoilage_st = frappe.db.sql("""
        SELECT COALESCE(SUM(item.qty), 0)
        FROM `tabStock Reconciliation` AS sr
        JOIN `tabStock Reconciliation Item` AS item ON sr.name = item.parent
        WHERE item.item_code = %s AND item.warehouse = %s
            AND sr.purpose = 'Stock Reconciliation'
        
        UNION ALL

        SELECT COALESCE(SUM(item.qty), 0)
        FROM `tabStock Entry` AS se
        JOIN `tabStock Entry Detail` AS item ON se.name = item.parent
        WHERE item.item_code = %s AND item.t_warehouse = %s
            AND se.stock_entry_type = 'Material Transfer'
    """, (item_code, warehouse, item_code, warehouse))

    # Extract the first element of each tuple and then sum
    return sum(entry[0] for entry in spoilage_st) or 0.0