import frappe
import erpnext
from frappe.utils import add_days, cint
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry, remove_payrolled_employees, get_salary_structure, get_filtered_employees
from frappe.utils.data import getdate
from frappe import _

def get_filter_condition(filters):
    cond = ""
    for f in ["company", "branch", "department", "designation"]:
        if filters.get(f):
            cond += " and t1." + f + " = " + frappe.db.escape(filters.get(f))
    return cond

class CustomPayrollEntry(PayrollEntry):
    @frappe.whitelist()
    def fill_employee_details(self):
        filters = self.make_filters()

        # --- Custom: Salary Structure Multiselect ---
        values = frappe.db.get_all("Salary Structure Multiselect", {"parent": self.name}, pluck="salary_structure")
        if values:
            # Override the salary structure filter
            filters["salary_structures"] = values

        # --- Custom: Multi-currency Employees ---
        if erpnext.get_company_currency(self.company) != self.currency:
            filters["salary_currency"] = self.currency

        # Call the standard employee list logic
        employees = self.custom_get_employee_list(filters=filters, as_dict=True, ignore_match_conditions=True)
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
            frappe.throw(error_msg, title=_("No employees found"))

        self.set("employees", employees)
        self.number_of_employees = len(self.employees)
        self.update_employees_with_withheld_salaries()

        return self.get_employees_with_unmarked_attendance()

    def custom_get_employee_list(self, filters, as_dict=True, ignore_match_conditions=True):
        # Use salary_structures if set by multiselect, else use default
        if filters.get("salary_structures"):
            sal_struct = filters["salary_structures"]
        else:
            sal_struct = get_salary_structure(
                filters.company,
                filters.currency,
                filters.salary_slip_based_on_timesheet,
                filters.get("payroll_frequency"),
            )
        if not sal_struct:
            return []

        emp_list = get_filtered_employees(
            sal_struct,
            filters,
            fields=None,
            as_dict=as_dict,
            ignore_match_conditions=ignore_match_conditions,
        )

        # --- Custom: Remove employees with wrong SSA applied ---
        emp_list = self.remove_wrong_ssa_applied(emp_list, filters.start_date, filters.end_date)
        # Remove employees already payrolled
        if as_dict:
            employees_to_check = {emp.employee: emp for emp in emp_list}
        else:
            employees_to_check = {emp[0]: emp for emp in emp_list}
        return remove_payrolled_employees(employees_to_check, filters.start_date, filters.end_date)

    def remove_wrong_ssa_applied(self, emp_list, start_date, end_date):
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

    def should_add_component_to_accrual_jv(self, component_type: str, item: dict) -> bool:
        add_component_to_accrual_jv = True
        if component_type == "earnings":
            is_flexible_benefit, only_tax_impact, ignore_for_jv = frappe.get_cached_value(
                "Salary Component", item["salary_component"], ["is_flexible_benefit", "only_tax_impact", "ignore_for_jv"]
            )
            if (cint(is_flexible_benefit) and cint(only_tax_impact)) or cint(ignore_for_jv):
                add_component_to_accrual_jv = False
        return add_component_to_accrual_jv

    # If you need to further customize period logic, override this as well:
    def get_payroll_dates_for_employee(self, employee_details: dict) -> tuple[str, str]:
        start_date = self.start_date
        if employee_details.date_of_joining and employee_details.date_of_joining > getdate(self.start_date):
            start_date = employee_details.date_of_joining

        end_date = self.end_date
        if employee_details.relieving_date and employee_details.relieving_date < getdate(self.end_date):
            end_date = employee_details.relieving_date

        return start_date, end_date