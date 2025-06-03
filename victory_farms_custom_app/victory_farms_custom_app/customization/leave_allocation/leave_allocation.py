import frappe
from frappe import _

def validate(self, method = None):
	if not self.leave_type or not self.has_value_changed("new_leaves_allocated"):
		return
	
	if not frappe.db.get_value("Leave Type", self.leave_type, "custom_create_liability_entries"):
		return

	liability_accounts = frappe.get_cached_value("Company", self.company, ["custom_default_debit_account", "custom_default_credit_account"], as_dict=True)

	if not liability_accounts.get("custom_default_debit_account") or not liability_accounts.get("custom_default_credit_account"):
		frappe.throw(_("Please set the default debit and credit accounts in Company"))

	previous = self.get_doc_before_save()
	previous_leave_balance = previous.get("new_leaves_allocated")

	diff_balance = self.new_leaves_allocated - previous_leave_balance

	assigned_ssa = get_assigned_salary_structure_assignment(self.employee, frappe.utils.today())

	base_amount = frappe.db.get_value("Salary Structure Assignment", assigned_ssa, "base") / 30

	actual_amount = diff_balance * base_amount

	jv_doc = frappe.new_doc("Journal Entry")
	jv_doc.voucher_type = "Journal Entry"
	jv_doc.company = self.company
	jv_doc.posting_date = frappe.utils.today()

	jv_doc.cheque_no = self.name
	jv_doc.cheque_date = frappe.utils.today()

	jv_doc.append("accounts", {
		"account": liability_accounts.custom_default_debit_account,
		"debit_in_account_currency": actual_amount
	})
	jv_doc.append("accounts", {
		"account": liability_accounts.custom_default_credit_account,
		"credit_in_account_currency": actual_amount
	})
	jv_doc.save()

	self.append("custom_liability_jv", {
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