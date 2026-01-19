import frappe
from frappe import _
from frappe.utils import flt, get_last_day, date_diff, getdate
from datetime import timedelta
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
		return  # Prevent additional salary creation

	salary_component = frappe.db.get_value("Leave Type", self.leave_type, "custom_salary_component")

	if not salary_component:
		return
	
	gross_pay, currency = frappe.db.get_value("Employee", self.employee, ["ctc", "salary_currency"])

	daily_pay = gross_pay / 30

	date_range = {}

	# Ensure from_date and to_date are date objects
	from_date = getdate(self.from_date)
	to_date = getdate(self.to_date)

	month_last_day = get_last_day(from_date)
	next_month_last_date = None
	if month_last_day >= to_date:
		date_range.update({month_last_day: [from_date, to_date]})
	else:
		next_month_start_date = month_last_day + timedelta(days=1)
		next_month_last_date = get_last_day(to_date)
		date_range.update({month_last_day: [from_date, month_last_day], next_month_last_date: [next_month_start_date, to_date]})

	total_leave_days = getattr(self, "total_leave_days", None)
	if total_leave_days is None:
		total_leave_days = (date_diff(to_date, from_date) + 1) if to_date != from_date else 1


	total_calendar_days = (date_diff(to_date, from_date) + 1) if to_date != from_date else 1

	for row in date_range:
		seg_start, seg_end = date_range[row][0], date_range[row][1]
		seg_calendar_days = (date_diff(seg_end, seg_start) + 1) if seg_end != seg_start else 1

		if len(date_range) == 1:
			seg_leave_days = total_leave_days
		else:
			seg_leave_days = (total_leave_days * seg_calendar_days) / float(total_calendar_days)

		amount = flt(seg_leave_days * daily_pay, self.precision)

		add_doc_name = frappe.db.get_value("Additional Salary", {"docstatus": 0, "ref_doctype": "Leave Application", "ref_docname": self.name, "salary_component": salary_component, "payroll_date": row})
		if not add_doc_name:
			add_doc_name = frappe.db.get_value("Additional Salary", {"docstatus": 0, "employee": self.employee, "salary_component": salary_component, "payroll_date": row})

		if add_doc_name:
			ads_doc = frappe.get_doc("Additional Salary", add_doc_name)
			ads_doc.amount = amount
		else:
			ads_doc = frappe.new_doc("Additional Salary")
			ads_doc.employee = self.employee
			ads_doc.salary_component = salary_component
			ads_doc.currency = currency
			ads_doc.payroll_date = row
			ads_doc.amount = amount
			ads_doc.ref_doctype = "Leave Application"
			ads_doc.ref_docname = self.name
		# ads_doc.ref_doctype = "Leave Application"
		# ads_doc.ref_docname = self.name

		ads_doc.save()
		ads_doc.submit()

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