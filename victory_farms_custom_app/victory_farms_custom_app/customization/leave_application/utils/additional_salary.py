import frappe
from frappe import _
from frappe.utils import flt, get_last_day, date_diff, getdate
from datetime import timedelta, date
from victory_farms_custom_app.victory_farms_custom_app.customization.leave_allocation.leave_allocation import get_assigned_salary_structure_assignment

def create_additional_salary(self):
	if self.status != "Approved":
		return

	# Check if Leave Type is "Unpaid Leave" and Employee Grade contains "H"
	employee_grade = frappe.db.get_value("Employee", self.employee, "grade")
 
	if self.leave_type == "Unpaid Leave" and employee_grade and ("H" in employee_grade or "P" in employee_grade):
		frappe.msgprint(
			msg="Additional Salary will not be created for 'Unpaid Leave' when the employee grade contains 'H' or 'P'.",
			title="Notice",
			indicator="orange"
		)
		return

	salary_component = frappe.db.get_value("Leave Type", self.leave_type, "custom_salary_component")

	if not salary_component:
		return
	
	gross_pay, currency = frappe.db.get_value("Employee", self.employee, ["ctc", "salary_currency"])

	from_date = getdate(self.from_date)
	to_date = getdate(self.to_date)

	def _next_25(d):
		"""Return the 25th of d's month if d.day <= 25, else the 25th of the next month."""
		if d.day <= 25:
			return d.replace(day=25)
		if d.month == 12:
			return date(d.year + 1, 1, 25)
		return date(d.year, d.month + 1, 25)

	payroll_map = {}
	anchor_date = from_date
	while anchor_date <= to_date:
		n25 = _next_25(anchor_date)
		cycle_end = min(n25, to_date)
		pd = n25  # payroll date is always the 25th of this cycle

		is_full_cycle = (anchor_date.day == 26) and (cycle_end == n25)
		if is_full_cycle:
			seg_amount = flt(gross_pay, 2)
		else:
			cycle_days = date_diff(cycle_end, anchor_date) + 1
			days_in_month = get_last_day(anchor_date).day
			seg_amount = flt(cycle_days * gross_pay / days_in_month, 2)

		payroll_map[pd] = flt((payroll_map.get(pd) or 0.0) + seg_amount, 2)

		if cycle_end >= to_date:
			break
		anchor_date = cycle_end + timedelta(days=1)

	# create/update Additional Salary documents for each payroll_date
	for pd, amt in payroll_map.items():
		add_doc_name = frappe.db.get_value("Additional Salary", {"docstatus": 0, "ref_doctype": "Leave Application", "ref_docname": self.name, "salary_component": salary_component, "payroll_date": pd})
		if not add_doc_name:
			add_doc_name = frappe.db.get_value("Additional Salary", {"docstatus": 0, "employee": self.employee, "salary_component": salary_component, "payroll_date": pd})

		if add_doc_name:
			ads_doc = frappe.get_doc("Additional Salary", add_doc_name)
			if ads_doc.ref_doctype == "Leave Application" and ads_doc.ref_docname == self.name:
				ads_doc.amount = amt
			else:
				ads_doc.amount = (ads_doc.amount or 0) + amt
		else:
			ads_doc = frappe.new_doc("Additional Salary")
			ads_doc.employee = self.employee
			ads_doc.salary_component = salary_component
			ads_doc.currency = currency
			ads_doc.payroll_date = pd
			ads_doc.amount = amt
			ads_doc.ref_doctype = "Leave Application"
			ads_doc.ref_docname = self.name

		ads_doc.save()
		# ads_doc.submit()

def create_reverse_jv(self):
	if not frappe.db.get_value("Leave Type", self.leave_type, "custom_create_liability_entries"):
		return
	
	liability_accounts = frappe.get_cached_value("Company", self.company, ["custom_leave_liability_account", "custom_leave_expense_account"], as_dict=True)

	if not liability_accounts.get("custom_leave_liability_account") or not liability_accounts.get("custom_leave_expense_account"):
		frappe.throw(_("Please set the default debit and credit accounts in Company"))
	
	assigned_ssa = get_assigned_salary_structure_assignment(self.employee, frappe.utils.today())

	base_amount = frappe.db.get_value("Salary Structure Assignment", assigned_ssa, "base") / 30

	actual_amount = self.total_leave_days * base_amount
	
	jv_doc = frappe.new_doc("Journal Entry")
	jv_doc.voucher_type = "Journal Entry"
	jv_doc.company = self.company
	jv_doc.posting_date = frappe.utils.today()

	jv_doc.cheque_no = self.name
	jv_doc.cheque_date = frappe.utils.today()

	jv_doc.append("accounts", {
		"account": liability_accounts.custom_leave_liability_account,
		"debit_in_account_currency": actual_amount
	})
	jv_doc.append("accounts", {
		"account": liability_accounts.custom_leave_expense_account,
		"credit_in_account_currency": actual_amount
	})
	jv_doc.save()