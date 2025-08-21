import frappe
import erpnext
from frappe.utils import add_days, cint, get_link_to_form, flt
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from frappe.utils.data import getdate
from frappe import _


class CustomPayrollEntry(PayrollEntry):

    def get_parent_cost_center(self, employee):
        emp_cost_center = frappe.db.get_value(
            "Employee", employee, "payroll_cost_center"
        )
        if not emp_cost_center:
            frappe.throw(_("No Cost Center set for Employee {0}").format(employee))

        while emp_cost_center:
            cost_center = frappe.db.get_value(
                "Cost Center",
                emp_cost_center,
                ["custom_is_payroll_cost_center", "is_group", "name", "parent_cost_center"],
                as_dict=True,
            )
            if not cost_center.parent_cost_center:
                break
        
            if not cost_center:
                break

            if cost_center.custom_is_payroll_cost_center:
                return cost_center.name
        
            emp_cost_center = cost_center.parent_cost_center

    def get_salary_component_account(self, employee, salary_component):
        emp_cost_center = self.get_parent_cost_center(employee)
        if emp_cost_center:
            account = frappe.db.get_value(
                "Salary Component Account",
                {
                    "parent": salary_component,
                    "company": self.company,
                    "custom_cost_center": emp_cost_center,
                },
                "account",
                cache=True,
            )
        else:
            account = frappe.db.get_value(
                "Salary Component Account",
                {
                    "parent": salary_component,
                    "company": self.company
                },
                "account",
                cache=True,
            )

        if not account:
            frappe.throw(
                _("Please set account in Salary Component {0}").format(
                    get_link_to_form("Salary Component", salary_component)
                )
            )

        return account

    def get_salary_component_total(
        self,
        component_type=None,
        employee_wise_accounting_enabled=False,
    ):
        salary_components = self.get_salary_components(component_type)
        if salary_components:
            component_dict = {}

            for item in salary_components:
                if not self.should_add_component_to_accrual_jv(component_type, item):
                    continue

                employee_cost_centers = self.get_payroll_cost_centers_for_employee(
                    item.employee, item.salary_structure
                )
                employee_advance = self.get_advance_deduction(component_type, item)

                for cost_center, percentage in employee_cost_centers.items():
                    amount_against_cost_center = flt(item.amount) * percentage / 100

                    if employee_advance:
                        self.add_advance_deduction_entry(
                            item,
                            amount_against_cost_center,
                            cost_center,
                            employee_advance,
                        )
                    else:
                        key = (item.employee, item.salary_component, cost_center)
                        component_dict[key] = (
                            component_dict.get(key, 0) + amount_against_cost_center
                        )

                    if employee_wise_accounting_enabled:
                        self.set_employee_based_payroll_payable_entries(
                            component_type, item.employee, amount_against_cost_center
                        )

            account_details = self.get_account(component_dict=component_dict)

            return account_details

    def get_account(self, component_dict=None):
        account_dict = {}
        for key, amount in component_dict.items():
            employee, component, cost_center = key
            account = self.get_salary_component_account(employee, component)
            accounting_key = (account, cost_center)

            account_dict[accounting_key] = account_dict.get(accounting_key, 0) + amount

        return account_dict

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
                & (Employee.status == "Active")
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
                error_msg += "<br>" + _("Department: {0}").format(
                    frappe.bold(self.department)
                )
            if self.designation:
                error_msg += "<br>" + _("Designation: {0}").format(
                    frappe.bold(self.designation)
                )
            if self.start_date:
                error_msg += "<br>" + _("Start date: {0}").format(
                    frappe.bold(self.start_date)
                )
            if self.end_date:
                error_msg += "<br>" + _("End date: {0}").format(
                    frappe.bold(self.end_date)
                )
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
                and t1.status = 'Active'
        %s order by t2.from_date desc
        """
        % cond,
        {
            "salary_currency": salary_currency,
            "end_date": end_date,
            "payroll_payable_account": payroll_payable_account,
        },
        as_dict=True,
    )