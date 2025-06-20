import frappe
from frappe import _
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

def on_submit(self, method = None):
    older_ssa = frappe.db.sql(
		"""
		select name from `tabSalary Structure Assignment`
		where employee=%(employee)s
		and docstatus = 1
		and %(on_date)s >= from_date and name != %(name)s order by from_date desc limit 1""",
		{
			"employee": self.employee,
			"on_date": frappe.utils.today(),
            "name": self.name
		},
	)

    if not older_ssa:
        return
        
    older_ssa = older_ssa[0][0]
    older_base = frappe.db.get_value("Salary Structure Assignment", older_ssa, "base")
    diffrence = self.base - older_base

    leave_type_list = frappe.db.get_all("Leave Type", {"custom_create_liability_entries": 1}, pluck= "name")
    liability_accounts = frappe.get_cached_value("Company", self.company, ["custom_leave_liability_account", "custom_leave_expense_account"], as_dict=True)
    if not liability_accounts.get("custom_leave_liability_account") or not liability_accounts.get("custom_leave_expense_account"):
        frappe.throw(_("Please set the default debit and credit accounts in Company"))

    for leave_type in leave_type_list:
        remaining_leaves = get_leave_balance_on(
                self.employee,
                leave_type,
                frappe.utils.today(),
            )

        if remaining_leaves < 0:
            continue

        jv_amount = remaining_leaves * (diffrence / 30)
        if jv_amount != 0:

            jv_doc = frappe.new_doc("Journal Entry")
            jv_doc.voucher_type = "Journal Entry"
            jv_doc.company = self.company
            jv_doc.posting_date = frappe.utils.today()
            jv_doc.cheque_no = self.name
            jv_doc.cheque_date = frappe.utils.today()

            jv_doc.append("accounts", {
                "account": liability_accounts.custom_leave_liability_account,
                "credit_in_account_currency": jv_amount
            })
            jv_doc.append("accounts", {
                "account": liability_accounts.custom_leave_expense_account,
                "debit_in_account_currency": jv_amount
            })
            jv_doc.save()
            # jv_doc.submit()