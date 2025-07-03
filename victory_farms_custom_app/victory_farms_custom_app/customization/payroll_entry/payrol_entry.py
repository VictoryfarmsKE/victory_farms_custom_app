import frappe
import erpnext
from frappe.utils import add_days, cint
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from frappe.utils.data import getdate
from frappe import _

class CustomPayrollEntry(PayrollEntry):
    @frappe.whitelist()
    def fill_employee_details(self):
        filters = self.make_filters()

        # Get all salary currencies for employees matching the other filters
        Employee = frappe.qb.DocType("Employee")
        employee_currency_list = (
            frappe.qb.from_(Employee)
            .select(Employee.salary_currency)
            .where(
                (Employee.company == self.company)
                & (Employee.status != "Inactive")
                & (Employee.salary_currency == filters.currency)
            )
            .groupby(Employee.salary_currency)
        ).run(pluck=True)

        employees = []
        for salary_currency in employee_currency_list:
            cond = "and t1.salary_currency = '{0}'".format(salary_currency)
            if self.branch:
                cond += " and t1.branch = '{0}'".format(self.branch)
            if self.department:
                cond += " and t1.department = '{0}'".format(self.department)
            if self.designation:
                cond += " and t1.designation = '{0}'".format(self.designation)
            frappe.log_error(f"SQL condition for currency {salary_currency}: {cond}")

            emp_list = get_other_currency_emp(
                cond,
                salary_currency,
                self.end_date,
                self.payroll_payable_account,
            )
            employees += emp_list

        self.set("employees", [])
        if not employees:
            error_msg = _(
                "No employees found for the mentioned criteria:<br>Company: {0}<br> Currency: {1}<br>Payroll Payable Account: {2}"
            ).format(
                frappe.bold(self.company),
                frappe.bold(self.currency),
                frappe.bold(self.payroll_payable_account),
            )
            if self.branch:
                error_msg += "<br>" + _("Branch: {0}").format(frappe.bold(self.branch))
            if self.department:
                error_msg += "<br>" + _("Department: {0}").format(frappe.bold(self.department))
            if self.designation:
                error_msg += "<br>" + _("Designation: {0}").format(frappe.bold(self.designation))
            if self.start_date:
                error_msg += "<br>" + _("Start date: {0}").format(frappe.bold(self.start_date))
            if self.end_date:
                error_msg += "<br>" + _("End date: {0}").format(frappe.bold(self.end_date))
            frappe.log_error(f"Throwing error: {error_msg}")
            frappe.throw(error_msg, title=_("No employees found"))

        self.set("employees", employees)
        self.number_of_employees = len(self.employees)
        self.update_employees_with_withheld_salaries()
        return self.get_employees_with_unmarked_attendance()
    
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


