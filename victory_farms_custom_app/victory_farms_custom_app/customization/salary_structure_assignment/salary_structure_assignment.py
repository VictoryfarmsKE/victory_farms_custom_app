import frappe
from frappe import _

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
    if diffrence != 0:
        liability_accounts = frappe.get_cached_value("Company", self.company, ["custom_default_debit_account", "custom_default_credit_account"], as_dict=True)

        if not liability_accounts.get("custom_default_debit_account") or not liability_accounts.get("custom_default_credit_account"):
            frappe.throw(_("Please set the default debit and credit accounts in Company"))
        jv_doc = frappe.new_doc("Journal Entry")
        jv_doc.voucher_type = "Journal Entry"
        jv_doc.company = self.company
        jv_doc.posting_date = frappe.utils.today()
        jv_doc.cheque_no = self.name
        jv_doc.cheque_date = frappe.utils.today()

        jv_doc.append("accounts", {
            "account": liability_accounts.custom_default_debit_account,
            "debit_in_account_currency": diffrence
        })
        jv_doc.append("accounts", {
            "account": liability_accounts.custom_default_credit_account,
            "credit_in_account_currency": diffrence
        })
        jv_doc.save()
        jv_doc.submit()

        self.append("custom_journal_entries", {
            "journal_entry": jv_doc.name,
            "amount": diffrence
        })