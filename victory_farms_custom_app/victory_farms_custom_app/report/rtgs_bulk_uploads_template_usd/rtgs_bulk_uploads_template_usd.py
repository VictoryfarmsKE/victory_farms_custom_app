# Copyright (c) 2026, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data, None, None


def get_columns():
    return [
        {
            "fieldname": "effective_date",
            "label": _("Effective Date"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "bank_code",
            "label": _("Bank Code"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "blank_1",
            "label": _("Blank"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "beneficiary_account",
            "label": _("Beneficiary Account"),
            "fieldtype": "Data",
            "width": 170
        },
        {
            "fieldname": "beneficiary_name",
            "label": _("Beneficiary Name"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "static_value",
            "label": _("Static Value"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "blank_2",
            "label": _("Blank"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "transfer_currency",
            "label": _("Transfer Currency"),
            "fieldtype": "Data",
            "width": 130
        },
        {
            "fieldname": "payment_amount",
            "label": _("Payment Amount"),
            "fieldtype": "Data",
            "width": 130
        },
        {
            "fieldname": "credit_narrative",
            "label": _("Credit Narrative"),
            "fieldtype": "Data",
            "width": 130
        },
        {
            "fieldname": "beneficiary_address_1",
            "label": _("Beneficiary Address 1"),
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "beneficiary_address_2",
            "label": _("Beneficiary Address 2"),
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "beneficiary_address_3",
            "label": _("Beneficiary Address 3"),
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "purpose_of_payment_code",
            "label": _("Purpose of Payment Code"),
            "fieldtype": "Data",
            "width": 190
        }
    ]


def get_data(filters):

    if not filters:
        filters = {}
    
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    if not from_date or not to_date:
        frappe.throw(_("Please select From Date and To Date"))
    
    detail_rows = get_detail_rows(from_date, to_date)
    
    if not detail_rows:
        frappe.msgprint(_("No salary slips found for the selected date range"))
        return []

    return detail_rows


def get_detail_rows(from_date, to_date):
    query = """
        SELECT 
            ss.posting_date,
            ss.net_pay,
            ss.custom_net_pay_excluding_bonus,
            emp.custom_bank_code,
            COALESCE(emp.bank_ac_no, ss.bank_account_no) as bank_account_no,
            emp.employee_name,
            emp.name as employee_id
        FROM 
            `tabSalary Slip` ss
        INNER JOIN 
            `tabEmployee` emp ON emp.name = ss.employee
        WHERE
            ss.docstatus = 1 
            AND emp.salary_currency = 'USD'
            AND ss.posting_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY
            ss.posting_date,
            ss.employee_name
    """
    
    results = frappe.db.sql(query, {
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=True)
    
    employee_payments = {}
    for row in results:
        emp_id = row.get("employee_id")
        posting_date = getdate(row.get("posting_date"))
        aggregation_key = (emp_id, posting_date)

        custom_net = row.get("custom_net_pay_excluding_bonus")
        net_pay = row.get("net_pay", 0)

        payment_amount = float(net_pay or 0) if float(custom_net or 0) == 0 else float(custom_net)

        if aggregation_key not in employee_payments:
            employee_payments[aggregation_key] = {
                "posting_date": posting_date,
                "employee_name": row.get("employee_name") or "",
                "bank_account_no": row.get("bank_account_no") or "",
                "custom_bank_code": row.get("custom_bank_code") or "",
                "payment_amount": payment_amount,
            }
        else:
            employee_payments[aggregation_key]["payment_amount"] += payment_amount
    
    # Convert to list of formatted rows
    detail_rows = []
    for _, data in employee_payments.items():
        detail_rows.append({
            "effective_date": data.get("posting_date").strftime("%Y%m%d"),
            "bank_code": data.get("custom_bank_code", ""),
            "blank_1": "",
            "beneficiary_account": data.get("bank_account_no", ""),
            "beneficiary_name": data.get("employee_name", ""),
            "static_value": "BANK",
            "blank_2": "",
            "transfer_currency": "USD",
            "payment_amount": "{:.2f}".format(data.get("payment_amount", 0)),
            "credit_narrative": "SAL",
            "beneficiary_address_1": "KENYA",
            "beneficiary_address_2": "",
            "beneficiary_address_3": "",
            "purpose_of_payment_code": "SALA",
        })
    
    return detail_rows
