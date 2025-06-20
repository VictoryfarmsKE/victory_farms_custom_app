import frappe
import erpnext
from frappe.utils import add_days, cint
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
			is_flexible_benefit, only_tax_impact, ignore_for_jv = frappe.get_cached_value(
				"Salary Component", item["salary_component"], ["is_flexible_benefit", "only_tax_impact", "ignore_for_jv"]
			)
			if (cint(is_flexible_benefit) and cint(only_tax_impact)) or cint(ignore_for_jv):
				add_component_to_accrual_jv = False

		return add_component_to_accrual_jv 
		
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