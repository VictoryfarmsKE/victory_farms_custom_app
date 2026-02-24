import frappe
from frappe import _

def on_submit(self, method = None):
	create_journal_entry(self, self.new_leaves_allocated)

def on_update_after_submit(self, method = None):
	if not self.leave_type or not self.has_value_changed("new_leaves_allocated"):
		return
	
	if not frappe.db.get_value("Leave Type", self.leave_type, "custom_create_liability_entries"):
		return

	previous = self.get_doc_before_save()
	previous_leave_balance = previous.get("new_leaves_allocated")

	diff_balance = self.new_leaves_allocated - previous_leave_balance

	create_journal_entry(self, diff_balance)

def create_journal_entry(self, diff_balance):
	liability_accounts = frappe.get_cached_value("Company", self.company, ["custom_leave_liability_account", "custom_leave_expense_account"], as_dict=True)

	if not liability_accounts.get("custom_leave_liability_account") or not liability_accounts.get("custom_leave_expense_account"):
		frappe.throw(_("Please set the default debit and credit accounts in Company"))

	assigned_ssa = get_assigned_salary_structure_assignment(self.employee, frappe.utils.today())

	if not assigned_ssa:
		return

	base_amount = frappe.db.get_value("Salary Structure Assignment", assigned_ssa, "base")

	if not base_amount:
		return

	base_amount = base_amount / 30

	actual_amount = diff_balance * base_amount

	jv_doc = frappe.new_doc("Journal Entry")
	jv_doc.voucher_type = "Journal Entry"
	jv_doc.company = self.company
	jv_doc.posting_date = frappe.utils.today()

	jv_doc.cheque_no = self.name
	jv_doc.cheque_date = frappe.utils.today()

	jv_doc.append("accounts", {
		"account": liability_accounts.custom_leave_liability_account,
		"credit_in_account_currency": actual_amount
	})
	jv_doc.append("accounts", {
		"account": liability_accounts.custom_leave_expense_account,
		"debit_in_account_currency": actual_amount
	})
	jv_doc.save()

	self.append("custom_journal_entries", {
		"journal_entry": jv_doc.name,
		"amount": actual_amount
	})

def get_assigned_salary_structure_assignment(employee, on_date):
	if not employee or not on_date:
		return None
	salary_structure = frappe.db.sql(
		"""
		select name from `tabSalary Structure Assignment`
		where employee=%(employee)s
		and docstatus = 1
		and %(on_date)s >= from_date order by from_date desc limit 1""",
		{
			"employee": employee,
			"on_date": on_date,
		},
	)
	return salary_structure[0][0] if salary_structure else None