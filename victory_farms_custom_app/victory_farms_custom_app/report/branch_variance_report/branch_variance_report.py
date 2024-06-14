# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from itertools import filterfalse
from erpnext.stock.utils import get_stock_balance
from erpnext.stock.stock_ledger import get_previous_sle
from frappe.query_builder.functions import CombineDatetime
from erpnext.stock.doctype.inventory_dimension.inventory_dimension import get_inventory_dimensions
from erpnext.stock.doctype.warehouse.warehouse import apply_warehouse_filter



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
            'label': _('Current Stock'),
            'fieldtype': 'Data',
            'width': 120,
            'align': 'right'
        },
        {
            'fieldname': 'difference',
            'label': _('Variance'),
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
    # Check if filters are provided
    if not filters or (filters and (not filters.get("from_date") or not filters.get("to_date") or  not filters.get("company"))):
        return []

    # Check if filters are provided
    from_date = str(filters.get("from_date"))
    to_date = str(filters.get("to_date"))
    where_cnd = ''
    if filters.get("item_code"):
        where_cnd += " and sle.item_code ='%s' " % filters["item_code"]
    if filters.get("custom_item_group"):
        where_cnd += " and sle.custom_item_group ='%s' " % filters["custom_item_group"]
    if filters.get("warehouse"):
        where_cnd += " and sle.warehouse ='%s' " % filters["warehouse"]
    if filters.get("company"):
        where_cnd += " and sle.company ='%s' " % filters["company"]

    vf_stock_balance_dict = {
            "posting_date": '',
            "item_code": '',
            "warehouse": '',
            "total_opening_stock": 0.0,
            "received_qty": 0.0,
            "total_quantity_sold": 0.0,
            "spoilage_stock": 0.0,
            "expected_closing_stock": 0.0,
            "system_stock": 0.0,
            "difference": 0.0
        }
    start_date = datetime.now()
    print ('Fetching all Item warehouse data = ', datetime.now())
    query_results = frappe.db.sql("""
    SELECT
        sle.item_code,
        sle.warehouse
    FROM
        `tabStock Ledger Entry` AS sle
    WHERE
        sle.is_cancelled!='1' and
        sle.docstatus = '1'
        %s
    Group by
        sle.item_code,
        sle.warehouse
    """ % (where_cnd))

    result_data = {}
    for qr_res in query_results:
        item_code = qr_res[0] or ''
        warehouse = qr_res[1] or ''
        stock_product_key = 'P%s-W%s-D%s' % (item_code, warehouse, to_date)
        qr_res_data = dict(vf_stock_balance_dict)
        qr_res_data.update({
            'item_code': item_code,
            'warehouse': warehouse,
            'posting_date': to_date
            })
        result_data[stock_product_key] = qr_res_data

    print ('Fetching movement between selected dates = ', datetime.now())
    query_balance_results = list(frappe.db.sql("""
    SELECT
        sle.item_code,
        sle.warehouse,
        sle.posting_date,
        sle.voucher_type,
        sle.actual_qty,
        sle.qty_after_transaction,
        sle.posting_datetime,
        sle.creation,
        sle.voucher_no
    FROM
        `tabStock Ledger Entry` AS sle
    WHERE
        sle.is_cancelled!='1' and
        sle.docstatus = '1' and
        sle.posting_date >= %%s and
        sle.posting_date <= %%s
        %s
    """ % where_cnd, (from_date, to_date)))
    query_voucher_sp_results = list(frappe.db.sql("""
    SELECT
        name
    FROM
        `tabStock Entry` AS se
    WHERE
        stock_entry_type = 'Repack - Spoilage'
    """))
    voucher_spoilage_list = [query_voucher_sp_res[0] for query_voucher_sp_res in query_voucher_sp_results]

    query_balance_results_dict_list = []
    for qr_bal_res in query_balance_results:
        if qr_bal_res[8] in voucher_spoilage_list:
            continue
        query_balance_results_dict_list.append({
            'item_code': qr_bal_res[0],
            'warehouse': qr_bal_res[1],
            'posting_date': qr_bal_res[2],
            'voucher_type': qr_bal_res[3],
            'actual_qty': qr_bal_res[4],
            'spoilage_qty': 0,
            'qty_after_transaction': qr_bal_res[5],
            'posting_datetime': qr_bal_res[6],
            'creation': qr_bal_res[7]
            })

    print ('Fetching Repack Spoilage data with selected dates = ', datetime.now())
    query_spoilage_results = list(frappe.db.sql("""
    SELECT
        sle.item_code,
        sle.warehouse,
        sle.posting_date,
        sle.voucher_type,
        sle.actual_qty,
        sle.qty_after_transaction,
        sle.posting_datetime,
        sle.creation
    FROM
        `tabStock Ledger Entry` AS sle
        INNER JOIN `tabStock Entry` AS se ON se.name = sle.voucher_no
        INNER JOIN `tabStock Entry Detail` AS sed ON sed.parent = se.name and
                                    sed.s_warehouse=sle.warehouse and
                                    sed.item_code=sle.item_code
    WHERE
        sle.is_cancelled!='1' and
        se.stock_entry_type = 'Repack - Spoilage' and
        sed.s_warehouse is not NULL and
        sle.docstatus = '1' and
        sle.posting_date >= %%s and
        sle.posting_date <= %%s
        %s
    """ % where_cnd, (from_date, to_date)))
    for query_spoilage_res in query_spoilage_results:
        query_balance_results_dict_list.append({
            'item_code': query_spoilage_res[0],
            'warehouse': query_spoilage_res[1],
            'posting_date': query_spoilage_res[2],
            'voucher_type': query_spoilage_res[3],
            'actual_qty': 0,
            'spoilage_qty': abs(query_spoilage_res[4] or 0),
            'qty_after_transaction': query_spoilage_res[5],
            'posting_datetime': query_spoilage_res[6],
            'creation': query_spoilage_res[7]
            })

    query_balance_results_list  = sorted(query_balance_results_dict_list, key=lambda x: (x['item_code'], 
                                                                                    x['warehouse'],
                                                                                    x['posting_datetime'],
                                                                                    x['creation']))


    last_closing_item_wh_stock_date = prev_item_wh_key = current_item_wh_key = ''
    dummy_key = 'Pdummy_item_not_check-Wdummy_wh_not_check'
    query_balance_results_list.append({
            'item_code': 'dummy_item_not_check',
            'warehouse': 'dummy_wh_not_check',
            'posting_date': False,
            'voucher_type': False,
            'actual_qty': 0,
            'spoilage_qty': 0,
            'qty_after_transaction': 0,
            'posting_datetime': False,
            'creation': False
    })
    all_item_wh_first_move_date_data = {}

    for qr_balance_res in query_balance_results_list:
        item_code = qr_balance_res['item_code'] or ''
        warehouse = qr_balance_res['warehouse'] or ''
        posting_date = str(qr_balance_res['posting_date']) or ''
        voucher_type = qr_balance_res['voucher_type'] or ''
        actual_qty = qr_balance_res['actual_qty'] or 0
        qty_after_transaction = qr_balance_res['qty_after_transaction'] or 0

        current_item_wh_key = 'P%s-W%s' % (item_code, warehouse)
        stock_product_key = 'P%s-W%s-D%s' % (item_code, warehouse, posting_date)

        if prev_item_wh_key and prev_item_wh_key != current_item_wh_key and \
           last_closing_item_wh_stock_date != to_date:
            prev_stock_product_key = '%s-D%s' % (prev_item_wh_key, last_closing_item_wh_stock_date)
            last_stock_product_key = '%s-D%s' % (prev_item_wh_key, to_date)
            prev_system_stock = result_data[prev_stock_product_key]['system_stock']
            result_data[last_stock_product_key].update({
                'total_opening_stock': prev_system_stock,
                'system_stock': prev_system_stock
                })

        if dummy_key == current_item_wh_key:
            continue

        if not result_data.get(stock_product_key):
            qr_bl_res_data = dict(vf_stock_balance_dict)
            qr_bl_res_data.update({
                'item_code': item_code,
                'warehouse': warehouse,
                'posting_date': posting_date,
                })
            result_data[stock_product_key] = qr_bl_res_data

        if not all_item_wh_first_move_date_data.get(current_item_wh_key):
            all_item_wh_first_move_date_data[current_item_wh_key] = posting_date

        if prev_item_wh_key == current_item_wh_key and posting_date != last_closing_item_wh_stock_date:
            prev_stock_product_key = '%s-D%s' % (prev_item_wh_key, last_closing_item_wh_stock_date)
            result_data[stock_product_key]['total_opening_stock'] = result_data[prev_stock_product_key]['system_stock']

        last_closing_item_wh_stock_date = posting_date

        if voucher_type != 'Stock Reconciliation':
            result_data[stock_product_key][actual_qty > 0 and 'received_qty' or 'total_quantity_sold'] += abs(actual_qty)
        result_data[stock_product_key]['spoilage_stock'] +=  qr_balance_res['spoilage_qty'] or 0
        result_data[stock_product_key]['system_stock'] = qty_after_transaction

        prev_item_wh_key = current_item_wh_key

    print ('Fetching Opening Stock data = ', datetime.now())
    query_last_results = list(
        frappe.db.sql("""
    SELECT
        sle.item_code,
        sle.warehouse,
        sle.qty_after_transaction,
        sle.posting_datetime,
        sle.creation
    FROM
        `tabStock Ledger Entry` AS sle
    Join
        (
        select
            sle_sub.item_code,
            sle_sub.warehouse,
            max(sle_sub.posting_datetime) as posting_datetime,
            max(sle_sub.creation) as creation
        from
            `tabStock Ledger Entry` AS sle_sub
        where
            sle_sub.is_cancelled!='1' and
            sle_sub.docstatus = '1' and
            sle_sub.posting_date < %%s
            %s
        group by
            sle_sub.item_code,
            sle_sub.warehouse
        ) msle
    WHERE
        msle.item_code = sle.item_code and 
        msle.warehouse = sle.warehouse and
        msle.posting_datetime = sle.posting_datetime and
        msle.creation = sle.creation and
        sle.is_cancelled!='1' and
        sle.docstatus = '1' and
        sle.posting_date < %%s
        %s
    """ % (where_cnd.replace('sle.', 'sle_sub.'), where_cnd),
        (from_date, from_date)))

    query_last_results_dict_list = []
    for qr_lst_res in query_last_results:
        query_last_results_dict_list.append({
            'item_code': qr_lst_res[0],
            'warehouse': qr_lst_res[1],
            'qty_after_transaction': qr_lst_res[2],
            'posting_datetime': qr_lst_res[3],
            'creation': qr_lst_res[4]
            })
    query_last_results_list  = sorted(query_last_results_dict_list, key=lambda x: (x['item_code'], 
                                                                                   x['warehouse'],
                                                                                   x['posting_datetime'],
                                                                                   x['creation']))
    for query_last_res in query_last_results_list:
        stock_product_key = 'P%s-W%s' % (query_last_res['item_code'], query_last_res['warehouse'])
        last_item_wh_date = all_item_wh_first_move_date_data.get(stock_product_key) or False
        update_vals = {'total_opening_stock': query_last_res['qty_after_transaction'] or 0.0,}
        if not last_item_wh_date:
            last_item_wh_date = to_date
            update_vals['system_stock'] = query_last_res['qty_after_transaction'] or 0.0
        stock_product_key += '-D%s' % last_item_wh_date
        result_data[stock_product_key].update(update_vals)

    for item_wh_key, balance_values in result_data.items():
        expected_closing_stock = round(result_data[item_wh_key]['total_opening_stock'] + \
                            result_data[item_wh_key]['received_qty'] - \
                            result_data[item_wh_key]['total_quantity_sold'] - \
                            result_data[item_wh_key]['spoilage_stock'], 3)
        result_data[item_wh_key]['expected_closing_stock'] = expected_closing_stock
        result_data[item_wh_key]['difference'] = round(expected_closing_stock - result_data[item_wh_key]['system_stock'], 3)

    print ('Report execution done with start time and end time = ', start_date, datetime.now())
    return list(sorted(list(result_data.values()), key=lambda x: x['posting_date'], reverse=False))
