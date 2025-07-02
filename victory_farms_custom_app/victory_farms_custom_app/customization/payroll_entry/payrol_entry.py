import frappe
from frappe import _
import erpnext
from frappe.utils import add_days, cint
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry, get_joining_relieving_condition, get_emp_list, remove_payrolled_employees, get_salary_structure

def get_filter_condition(filters):
    cond = ""
    for f in ["company", "branch", "department", "designation"]:
        if filters.get(f):
            cond += " and t1." + f + " = " + frappe.db.escape(filters.get(f))
    return cond

class CustomPayrollEntry(PayrollEntry):
    def get_emp_list(self):
        """
        Returns list of active employees based on selected criteria
        and for which salary structure exists
        """
        self.check_mandatory()
        filters = self.make_filters()
        cond = get_filter_condition(filters)
        cond += get_joining_relieving_condition(self.start_date, self.end_date)

        if values := frappe.db.get_all("Salary Structure Multiselect", {"parent": self.name}, pluck = "salary_structure"):
            sal_struct = values
        else:
            sal_struct = get_salary_structure(
                self.company, self.currency, self.salary_slip_based_on_timesheet, self.payroll_frequency
            )

        if erpnext.get_company_currency(self.company) != self.currency:
            cond += "and t1.salary_currency = %(salary_currency)s "
            cond += "and t2.payroll_payable_account = %(payroll_payable_account)s "
            cond += "and %(from_date)s >= t2.from_date"
            emp_list = get_other_currency_emp(cond, self.currency, self.end_date, self.payroll_payable_account)
            return emp_list
    
        if sal_struct:
            cond += "and t2.salary_structure IN %(sal_struct)s "
            cond += "and t2.payroll_payable_account = %(payroll_payable_account)s "
            cond += "and %(from_date)s >= t2.from_date"
            emp_list = get_emp_list(sal_struct, cond, self.end_date, self.payroll_payable_account)
            emp_list = remove_wrong_ssa_applied(emp_list, self.start_date, self.end_date)
            emp_list = remove_payrolled_employees(emp_list, self.start_date, self.end_date)
            return emp_list
    
    def should_add_component_to_accrual_jv(self, component_type: str, item: dict) -> bool:
        add_component_to_accrual_jv = True
        if component_type == "earnings":
            is_flexible_benefit, only_tax_impact, ignore_for_jv, do_not_include_in_total = frappe.get_cached_value(
                "Salary Component", item["salary_component"], ["is_flexible_benefit", "only_tax_impact", "ignore_for_jv", "do_not_include_in_total"]
            )
            if (cint(is_flexible_benefit) and cint(only_tax_impact)) or (cint(ignore_for_jv) and cint(do_not_include_in_total)):
                add_component_to_accrual_jv = False

        if component_type == "deductions":
            do_not_include_in_total, ignore_for_jv = frappe.get_cached_value(
                "Salary Component", item["salary_component"], ["do_not_include_in_total", "ignore_for_jv"]
            )
            if (cint(do_not_include_in_total) and cint(ignore_for_jv)):
                add_component_to_accrual_jv = False

        return add_component_to_accrual_jv 
    
    def make_accrual_jv_entry(self):
        frappe.log_error(title="Called Je", message="Called")
        self.check_permission("write")
        process_payroll_accounting_entry_based_on_employee = frappe.db.get_single_value(
            "Payroll Settings", "process_payroll_accounting_entry_based_on_employee"
        )
        self.employee_based_payroll_payable_entries = {}
        self._advance_deduction_entries = []

        earnings = (
            self.get_salary_component_total(
                component_type="earnings",
                process_payroll_accounting_entry_based_on_employee=process_payroll_accounting_entry_based_on_employee,
            )
            or {}
        )

        deductions = (
            self.get_salary_component_total(
                component_type="deductions",
                process_payroll_accounting_entry_based_on_employee=process_payroll_accounting_entry_based_on_employee,
            )
            or {}
        )

        payroll_payable_account = self.payroll_payable_account
        jv_name = ""
        precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")

        if earnings or deductions:
            journal_entry = frappe.new_doc("Journal Entry")
            journal_entry.voucher_type = "Journal Entry"
            journal_entry.user_remark = _("Accrual Journal Entry for salaries from {0} to {1}").format(
                self.start_date, self.end_date
            )
            journal_entry.company = self.company
            journal_entry.posting_date = self.posting_date
            accounting_dimensions = get_accounting_dimensions() or []

            accounts = []
            currencies = []
            payable_amount = 0
            multi_currency = 0
            company_currency = erpnext.get_company_currency(self.company)

            # Earnings
            for acc_cc, amount in earnings.items():
                payable_amount = self.get_accounting_entries_and_payable_amount(
                    acc_cc[0],
                    acc_cc[1] or self.cost_center,
                    amount,
                    currencies,
                    company_currency,
                    payable_amount,
                    accounting_dimensions,
                    precision,
                    entry_type="debit",
                    accounts=accounts,
                )

            # Deductions
            for acc_cc, amount in deductions.items():
                payable_amount = self.get_accounting_entries_and_payable_amount(
                    acc_cc[0],
                    acc_cc[1] or self.cost_center,
                    amount,
                    currencies,
                    company_currency,
                    payable_amount,
                    accounting_dimensions,
                    precision,
                    entry_type="credit",
                    accounts=accounts,
                )

            payable_amount = self.set_accounting_entries_for_advance_deductions(
                accounts,
                currencies,
                company_currency,
                accounting_dimensions,
                precision,
                payable_amount,
            )

            # Payable amount
            if process_payroll_accounting_entry_based_on_employee:
                """
                employee_based_payroll_payable_entries = {
                        'HR-EMP-00004': {
                                        'earnings': 83332.0,
                                        'deductions': 2000.0
                                },
                        'HR-EMP-00005': {
                                'earnings': 50000.0,
                                'deductions': 2000.0
                        }
                }
                """
                for employee, employee_details in self.employee_based_payroll_payable_entries.items():
                    payable_amount = employee_details.get("earnings", 0) - employee_details.get(
                        "deductions", 0
                    )

                    payable_amount = self.get_accounting_entries_and_payable_amount(
                        payroll_payable_account,
                        self.cost_center,
                        payable_amount,
                        currencies,
                        company_currency,
                        0,
                        accounting_dimensions,
                        precision,
                        entry_type="payable",
                        party=employee,
                        accounts=accounts,
                    )

            else:
                payable_amount = self.get_accounting_entries_and_payable_amount(
                    payroll_payable_account,
                    self.cost_center,
                    payable_amount,
                    currencies,
                    company_currency,
                    0,
                    accounting_dimensions,
                    precision,
                    entry_type="payable",
                    accounts=accounts,
                )

            journal_entry.set("accounts", accounts)
            if len(currencies) > 1:
                multi_currency = 1
            journal_entry.multi_currency = multi_currency
            journal_entry.title = payroll_payable_account
            account_data = {row.account: row.debit_in_account_currency for row in accounts if row.debit_in_account_currency > 0}

            add_sc_com = frappe.db.get_all("Salary Component", {"type": "Deduction", "do_not_include_in_total": 1, "custom_debit_account": ["is", "set"]}, ["name", "custom_debit_account"])

            if add_sc_com:
                for row in add_sc_com:
                    account = self.get_salary_component_account(row.name)
                    journal_entry.append("accounts", {
                        "account": row.custom_debit_account,
                        "debit_in_account_currency": account_data.get(account, 0),
                        "credit_in_account_currency": 0,
                        "cost_center": self.cost_center
                    })
                journal_entry.save()

            try:
                journal_entry.submit()
                jv_name = journal_entry.name
                self.update_salary_slip_status(jv_name=jv_name)
            except Exception as e:
                if type(e) in (str, list, tuple):
                    frappe.msgprint(e)
                raise

        return jv_name

    # def make_journal_entry(self,accounts,currencies,payroll_payable_account=None,voucher_type="Journal Entry",user_remark="",submitted_salary_slips: list | None = 	None,submit_journal_entry=False,) -> str:
    #     multi_currency = 0
    #     if len(currencies) > 1:
    #         multi_currency = 1

    #     journal_entry = frappe.new_doc("Journal Entry")
    #     journal_entry.voucher_type = voucher_type
    #     journal_entry.user_remark = user_remark
    #     journal_entry.company = self.company
    #     journal_entry.posting_date = self.posting_date

    #     journal_entry.set("accounts", accounts)
    #     journal_entry.multi_currency = multi_currency

    #     if voucher_type == "Journal Entry":
    #         journal_entry.title = payroll_payable_account

    #     account_data = {row.account: row.debit_in_account_currency for row in accounts if row.debit_in_account_currency > 0}

    #     add_sc_com = frappe.db.get_all("Salary Component", {"type": "Deduction", "do_not_include_in_total": 1, "custom_debit_account": ["is", "set"]}, ["name", "custom_debit_account"])

    #     if add_sc_com:
    #         for row in add_sc_com:
    #             account = self.get_salary_component_account(row.name)
    #             journal_entry.append("accounts", {
    #                 "account": row.custom_debit_account,
    #                 "debit_in_account_currency": account_data.get(account, 0),
    #                 "credit_in_account_currency": 0,
    #                 "cost_center": self.cost_center
    #             })

    #     journal_entry.save(ignore_permissions=True)
    #     try:
    #         if submit_journal_entry:
    #             journal_entry.submit()

    #         if submitted_salary_slips:
    #             self.set_journal_entry_in_salary_slips(submitted_salary_slips, jv_name=journal_entry.name)

    #     except Exception as e:
    #         if type(e) in (str, list, tuple):
    #             frappe.msgprint(e)

    #         self.log_error("Journal Entry creation against Salary Slip failed")
    #         raise

    #     return journal_entry
        
def remove_wrong_ssa_applied(emp_list, start_date, end_date):
    start_date = add_days(start_date, 1)
    new_emp_list = []
    for employee_details in emp_list:
        if not frappe.db.exists(
            "Salary Structure Assignment",
            {
                "employee": employee_details.employee,
                "from_date": ["between", [start_date, end_date]],
                "docstatus": 1,
            },
        ):
            new_emp_list.append(employee_details)

    return new_emp_list

def get_other_currency_emp(cond, salary_currency, end_date, payroll_payable_account):
    return frappe.db.sql(
        """
            select
                distinct t1.name as employee, t1.employee_name, t1.department, t1.designation
            from
                `tabEmployee` t1, `tabSalary Structure Assignment` t2
            where
                t1.name = t2.employee
                and t2.docstatus = 1
                and t1.status != 'Inactive'
        %s order by t2.from_date desc
        """
        % cond,
        {
            "salary_currency": salary_currency,
            "from_date": end_date,
            "payroll_payable_account": payroll_payable_account,
        },
        as_dict=True,
    )