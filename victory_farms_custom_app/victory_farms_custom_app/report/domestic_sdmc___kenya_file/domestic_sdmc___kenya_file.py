# Copyright (c) 2026, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import formatdate, today


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data, None, None


def get_columns():
    return [
        {
            "fieldname": "debit_customer_id",
            "label": _("Debit Customer ID"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "debit_account",
            "label": _("Debit Account"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "file_total",
            "label": _("File Total"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "currency",
            "label": _("Currency"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "effective_date",
            "label": _("Effective Date"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "col6",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col7",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col8",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col9",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col10",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col11",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col12",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col13",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col14",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col15",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col16",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col17",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "col18",
            "label": _(""),
            "fieldtype": "Data",
            "width": 50
        }
    ]


def get_data(filters):
    """
    Generate data rows matching CSV template format
    """
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
    
    # Calculate file total
    file_total = sum(float(row.get("debit_customer_id", 0)) for row in detail_rows)
    
    # Build first header row
    header_row_1 = get_header_row_1(file_total)
    
    # Build second header row 
    header_row_2 = get_header_row_2()
    
    data = [header_row_1, header_row_2] + detail_rows
    
    return data


def get_header_row_1(file_total):
    """
    Generate the first header row (summary information)
    """
    return {
        "debit_customer_id": "541587",
        "debit_account": "5415870015",
        "file_total": "{:.2f}".format(file_total),
        "currency": "KES",
        "effective_date": formatdate(today(), "ddMMyyyy"),
        "col6": "",
        "col7": "",
        "col8": "",
        "col9": "",
        "col10": "",
        "col11": "",
        "col12": "",
        "col13": "",
        "col14": "",
        "col15": "",
        "col16": "",
        "col17": "",
        "col18": ""
    }


def get_header_row_2():
    """
    Generate the second header row (column headers for detail rows)
    """
    return {
        "debit_customer_id": "Payment Amount",
        "debit_account": "Beneficiary Type",
        "file_total": "Beneficiary Name",
        "currency": "Beneficiary Account",
        "effective_date": "Payment Type",
        "col6": "Bank Code",
        "col7": "Beneficiary Email",
        "col8": "Payment Description 1",
        "col9": "Payment Description 2",
        "col10": "Payment Description 3",
        "col11": "Payment Description 4",
        "col12": "Debit Narrative",
        "col13": "Credit Narrative",
        "col14": "Purpose Code",
        "col15": "Deal Reference",
        "col16": "Beneficiary Address 1",
        "col17": "Beneficiary Address 2",
        "col18": "Beneficiary Address 3"
    }


def get_detail_rows(from_date, to_date):
    query = """
        SELECT 
            ss.net_pay,
            ss.custom_net_pay_excluding_bonus,
            ss.employee_name,
            ss.bank_account_no,
            emp.custom_bank_code,
            emp.custom_branch_code,
            emp.bank_name,
            emp.prefered_email,
            emp.name as employee_id
        FROM 
            `tabSalary Slip` ss
        INNER JOIN 
            `tabEmployee` emp ON emp.name = ss.employee
        WHERE
            ss.docstatus = 1 
            AND emp.salary_currency = 'KES'
            AND ss.posting_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY
            ss.employee_name
    """
    
    results = frappe.db.sql(query, {
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=True)
    
    employee_payments = {}
    for row in results:
        emp_id = row.get("employee_id")

        custom_net = row.get("custom_net_pay_excluding_bonus")
        net_pay = row.get("net_pay", 0)

        payment_amount = net_pay if float(custom_net or 0) == 0 else float(custom_net)

        if emp_id not in employee_payments:
            employee_payments[emp_id] = row
            employee_payments[emp_id]["payment_amount"] = payment_amount
        else:
            employee_payments[emp_id]["payment_amount"] += payment_amount
    
    # Convert to list of formatted rows
    detail_rows = []
    for emp_id, data in employee_payments.items():
        bank_name = (data.get("bank_name") or "").lower()
        payment_type = "INTERNAL" if "ncba" in bank_name else "PESALINK"

        detail_rows.append({
            "debit_customer_id": "{:.2f}".format(data.get("payment_amount", 0)),  # Payment Amount
            "debit_account": "A",  # Beneficiary Type (Adhoc)
            "file_total": data.get("employee_name", ""),  # Beneficiary Name
            "currency": data.get("bank_account_no", ""),  # Beneficiary Account
            "effective_date": payment_type,  # Payment Type
            "col6": "{}{}".format(
                data.get("custom_bank_code") or "",
                data.get("custom_branch_code") or ""
            ),  # Bank Code
            "col7": data.get("prefered_email") or "0",  # Beneficiary Email
            "col8": "0",  # Payment Description 1
            "col9": "0",  # Payment Description 2
            "col10": "0",  # Payment Description 3
            "col11": "0",  # Payment Description 4
            "col12": "0",  # Debit Narrative
            "col13": "0",  # Credit Narrative
            "col14": "0",  # Purpose Code
            "col15": "",  # Deal Reference
            "col16": "0",  # Beneficiary Address 1
            "col17": "0",  # Beneficiary Address 2
            "col18": "0"   # Beneficiary Address 3
        })
    
    return detail_rows
