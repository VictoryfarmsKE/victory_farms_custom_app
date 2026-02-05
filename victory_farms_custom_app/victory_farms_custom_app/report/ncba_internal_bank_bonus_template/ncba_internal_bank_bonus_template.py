# Copyright (c) 2026, Solufy and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import formatdate, today, flt

AppraisalPayout = frappe.qb.DocType("Appraisal Payout")
AppraisalPayoutItem = frappe.qb.DocType("Appraisal Payout Item")
Employee = frappe.qb.DocType("Employee")


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    
    # Get filtered appraisal payouts
    filtered_appraisal_payouts = get_appraisal_payouts(filters)
    if not filtered_appraisal_payouts:
        return columns, [], None, None
    
    # Get appraisal payout items and enriched data
    data = get_data(filtered_appraisal_payouts)
    
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


def get_data(filtered_appraisal_payouts):
    """
    Generate data rows matching CSV template format from appraisal payout data
    """
    payout_ids = [payout['name'] for payout in filtered_appraisal_payouts]
    
    if not payout_ids:
        return []
    
    # Get appraisal payout items
    detail_items = get_appraisal_payout_details(payout_ids)
    
    if not detail_items:
        frappe.msgprint(_("No appraisal payout data found for the selected criteria"))
        return []
    
    # Get employee bank information
    emp_ids = list({item['employee'] for item in detail_items if item.get('employee')})
    emp_bank_map = get_employee_bank_map(emp_ids)
    
    # Calculate file total
    file_total = sum(flt(item.get("total_bonus", 0)) for item in detail_items)
    
    # Build header rows
    header_row_1 = get_header_row_1(file_total)
    header_row_2 = get_header_row_2()
    
    # Build detail rows
    detail_rows = []
    for item in detail_items:
        emp = item.get("employee")
        emp_info = emp_bank_map.get(emp, {})
        
        detail_rows.append({
            "debit_customer_id": "{:.2f}".format(flt(item.get("total_bonus", 0))),  # Payment Amount
            "debit_account": "A",  # Beneficiary Type (Adhoc)
            "file_total": item.get("employee_name", ""),  # Beneficiary Name
            "currency": emp_info.get("bank_ac_no", ""),  # Beneficiary Account
            "effective_date": "INTERNAL",  # Payment Type
            "col6": "{}{}".format(
                emp_info.get("custom_bank_code") or "",
                emp_info.get("custom_branch_code") or ""
            ),  # Bank Code
            "col7": emp_info.get("prefered_email") or "0",  # Beneficiary Email
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


def get_appraisal_payouts(filters):
    """Query and filter Appraisal Payout records"""
    conditions = []

    if filters.get("start_date"):
        conditions.append(AppraisalPayout.start_date >= filters["start_date"])
    if filters.get("end_date"):
        conditions.append(AppraisalPayout.end_date <= filters["end_date"])
    if filters.get("company"):
        conditions.append(AppraisalPayout.company == filters["company"])
    if filters.get("payout_frequency"):
        conditions.append(AppraisalPayout.payout_frequency == filters["payout_frequency"])
    if filters.get("posting_date"):
        conditions.append(AppraisalPayout.posting_date == filters["posting_date"])

    query = frappe.qb.from_(AppraisalPayout).select(
        AppraisalPayout.name,
        AppraisalPayout.company,
        AppraisalPayout.payout_frequency,
        AppraisalPayout.start_date,
        AppraisalPayout.end_date,
        AppraisalPayout.posting_date
    ).where(AppraisalPayout.docstatus == 1)
    
    if conditions:
        for condition in conditions:
            query = query.where(condition)

    return query.run(as_dict=True)


def get_appraisal_payout_details(payout_ids):
    """Get appraisal payout item details"""
    if not payout_ids:
        return []

    return (
        frappe.qb.from_(AppraisalPayoutItem)
        .join(AppraisalPayout).on(AppraisalPayout.name == AppraisalPayoutItem.parent)
        .join(Employee).on(Employee.name == AppraisalPayoutItem.employee)
        .where(AppraisalPayoutItem.parent.isin(payout_ids))
        .where(AppraisalPayoutItem.total_bonus != 0)
        .where(Employee.bank_name.like('%NCBA%'))
        .select(
            AppraisalPayoutItem.employee,
            AppraisalPayoutItem.employee_name,
            AppraisalPayoutItem.department,
            AppraisalPayoutItem.total_bonus
        )
        .distinct()
        .run(as_dict=True)
    )


def get_employee_bank_map(employee_ids):
    """Get employee bank information mapped by employee ID"""
    if not employee_ids:
        return {}
    rows = frappe.db.sql(
        """
        SELECT name, employee_name, bank_ac_no, custom_bank_code, custom_branch_code, prefered_email
        FROM `tabEmployee`
        WHERE name IN %(emp_ids)s
        """,
        {"emp_ids": tuple(employee_ids)},
        as_dict=True,
    )
    return {r["name"]: r for r in rows}
