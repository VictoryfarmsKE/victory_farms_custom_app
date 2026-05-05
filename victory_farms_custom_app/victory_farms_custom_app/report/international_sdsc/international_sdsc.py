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
			"fieldname": "debit_customer_id",
			"label": _("Debit Customer ID"),
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"fieldname": "debit_account",
			"label": _("Debit Account"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "payment_amount",
			"label": _("Payment Amount"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "transfer_currency",
			"label": _("Transfer Currency"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "effective_date",
			"label": _("Effective Date"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "beneficiary_type",
			"label": _("Beneficiary Type"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "beneficiary_name",
			"label": _("Beneficiary Name"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "beneficiary_account",
			"label": _("Beneficiary Account"),
			"fieldtype": "Data",
			"width": 190,
		},
		{
			"fieldname": "network_type",
			"label": _("Network Type"),
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"fieldname": "swift_code",
			"label": _("SWIFT Code"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "beneficiary_email_id",
			"label": _("Beneficiary Email ID"),
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"fieldname": "beneficiary_address_1",
			"label": _("Beneficiary Address 1"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "beneficiary_address_2",
			"label": _("Beneficiary Address 2"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "beneficiary_address_3",
			"label": _("Beneficiary Address 3"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "beneficiary_address_4",
			"label": _("Beneficiary Address 4"),
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"fieldname": "charge_type",
			"label": _("Charge Type"),
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"fieldname": "debit_narrative",
			"label": _("Debit Narrative"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "credit_narrative",
			"label": _("Credit Narrative"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "deal_reference_number",
			"label": _("Deal Reference Number"),
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"fieldname": "purpose_of_payment_code",
			"label": _("Purpose of Payment Code"),
			"fieldtype": "Data",
			"width": 190,
		},
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
			emp.name as employee_id,
			emp.employee_name,
			emp.custom_account_name,
			COALESCE(emp.bank_ac_no, ss.bank_account_no) as bank_account_no,
			COALESCE(NULLIF(emp.iban, ''), '') as swift_code,
			COALESCE(NULLIF(emp.prefered_email, ''), NULLIF(emp.company_email, ''), '0') as beneficiary_email_id,
			COALESCE(NULLIF(addr.address_line1, ''), '') as beneficiary_address_1,
			COALESCE(NULLIF(addr.address_line2, ''), '') as beneficiary_address_2,
			TRIM(CONCAT_WS(' ', NULLIF(addr.city, ''), NULLIF(addr.state, ''), NULLIF(addr.pincode, ''))) as beneficiary_address_3,
			COALESCE(NULLIF(addr.country, ''), '') as beneficiary_address_4
		FROM
			`tabSalary Slip` ss
		INNER JOIN
			`tabEmployee` emp ON emp.name = ss.employee
		LEFT JOIN
			`tabAddress` addr ON addr.name = COALESCE(NULLIF(emp.current_address, ''), NULLIF(emp.permanent_address, ''))
		WHERE
			ss.docstatus = 1
			AND emp.salary_currency = 'USD'
			AND emp.custom_transfer_type = 'International'
			AND ss.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY
			emp.employee_name
	"""

	results = frappe.db.sql(
		query,
		{
			"from_date": from_date,
			"to_date": to_date,
		},
		as_dict=True,
	)

	employee_payments = {}
	for row in results:
		emp_id = row.get("employee_id")

		custom_net = row.get("custom_net_pay_excluding_bonus")
		net_pay = row.get("net_pay", 0)
		payment_amount = float(net_pay or 0) if float(custom_net or 0) == 0 else float(custom_net)

		if emp_id not in employee_payments:
			employee_payments[emp_id] = {
				"posting_date": getdate(row.get("posting_date")),
				"employee_name": row.get("employee_name") or "",
				"custom_account_name": row.get("custom_account_name") or "",
				"bank_account_no": row.get("bank_account_no") or "",
				"swift_code": row.get("swift_code") or "",
				"beneficiary_email_id": row.get("beneficiary_email_id") or "0",
				"beneficiary_address_1": row.get("beneficiary_address_1") or "",
				"beneficiary_address_2": row.get("beneficiary_address_2") or "",
				"beneficiary_address_3": row.get("beneficiary_address_3") or "",
				"beneficiary_address_4": row.get("beneficiary_address_4") or "",
				"payment_amount": payment_amount,
			}
		else:
			employee_payments[emp_id]["payment_amount"] += payment_amount
			if getdate(row.get("posting_date")) > employee_payments[emp_id]["posting_date"]:
				employee_payments[emp_id]["posting_date"] = getdate(row.get("posting_date"))

	detail_rows = []
	for data in employee_payments.values():
		detail_rows.append(
			{
				"debit_customer_id": "541587",
				"debit_account": "5415870028",
				"payment_amount": "{:.2f}".format(data.get("payment_amount", 0)),
				"transfer_currency": "USD",
				"effective_date": data.get("posting_date").strftime("%d%m%Y"),
				"beneficiary_type": "A",
				"beneficiary_name": data.get("custom_account_name", ""),
				"beneficiary_account": data.get("bank_account_no", ""),
				"network_type": "S",
				"swift_code": data.get("swift_code", ""),
				"beneficiary_email_id": data.get("beneficiary_email_id", "0"),
				"beneficiary_address_1": data.get("beneficiary_address_1", ""),
				"beneficiary_address_2": data.get("beneficiary_address_2", ""),
				"beneficiary_address_3": data.get("beneficiary_address_3", ""),
				"beneficiary_address_4": data.get("beneficiary_address_4", ""),
				"charge_type": "OUR",
				"debit_narrative": "SAL",
				"credit_narrative": "SAL",
				"deal_reference_number": "",
				"purpose_of_payment_code": "",
			}
		)
	return detail_rows
