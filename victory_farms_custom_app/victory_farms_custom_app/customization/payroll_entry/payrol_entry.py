import frappe
import erpnext
from frappe.utils import add_days, cint, get_link_to_form, flt
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from frappe.utils.data import getdate
from frappe import _
import erpnext
from frappe.utils import add_days, cint, get_link_to_form, flt
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry, remove_payrolled_employees, get_salary_structure

def get_filter_condition(filters):
	cond = ""
	for f in ["company", "branch", "department", "designation"]:
		if filters.get(f):
			cond += " and t1." + f + " = " + frappe.db.escape(filters.get(f))
	return cond

def get_joining_relieving_condition(start_date, end_date):
	cond = f"""
		and ifnull(t1.date_of_joining, '1900-01-01') <= '{end_date}'
		and ifnull(t1.relieving_date, '2199-12-31') >= '{start_date}'
	"""
	return cond


def get_parent_cost_center(self, employee):
	emp_cost_center = frappe.db.get_value(
		"Employee", employee, "payroll_cost_center"
	)
	if not emp_cost_center:
		frappe.throw(_("No Cost Center set for Employee {0}").format(employee))

	return emp_cost_center
	# while emp_cost_center:
	#     cost_center = frappe.db.get_value(
	#         "Cost Center",
	#         emp_cost_center,
	#         ["custom_is_payroll_cost_center", "is_group", "name", "parent_cost_center"],
	#         as_dict=True,
	#     )
	#     if not cost_center.parent_cost_center:
	#         break
	
	#     if not cost_center:
	#         break

	#     if cost_center.custom_is_payroll_cost_center:
	#         return cost_center.name
	
	#     emp_cost_center = cost_center.parent_cost_center

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
	if not account:
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
	process_payroll_accounting_entry_based_on_employee=False,
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

				if process_payroll_accounting_entry_based_on_employee:
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
	
	def make_journal_entry(
		self,
		accounts,
		currencies,
		payroll_payable_account=None,
		voucher_type="Journal Entry",
		user_remark="",
		submitted_salary_slips: list | None = None,
		submit_journal_entry=False,
		employee_wise_accounting_enabled=False,
	) -> str:
		multi_currency = 0
		if len(currencies) > 1:
			multi_currency = 1

		journal_entry = frappe.new_doc("Journal Entry")
		journal_entry.voucher_type = voucher_type
		journal_entry.user_remark = user_remark
		journal_entry.company = self.company
		journal_entry.posting_date = self.posting_date
		journal_entry.party_not_required = True if not employee_wise_accounting_enabled else False

		journal_entry.set("accounts", accounts)
		journal_entry.multi_currency = multi_currency

		if voucher_type == "Journal Entry":
			journal_entry.title = payroll_payable_account

		account_data = {}
		last_index = 0
		for row in journal_entry.accounts:
			if row.get("credit_in_account_currency") and row.get("credit_in_account_currency", 0) > 0:
				if account_data.get(row.account):
					account_data[row.get("account")][1] += row.get("credit_in_account_currency")
				else:
					account_data[row.get("account")] = [row.idx, row.get("credit_in_account_currency")]
			last_index = row.idx
			
		# account_data = {row.get("account"): [row.idx, row.get("credit_in_account_currency")] for row in accounts if row.get("credit_in_account_currency", 0) > 0}

		add_sc_com = frappe.db.get_all("Salary Component", {"type": "Deduction", "do_not_include_in_total": 1, "custom_debit_account": ["is", "set"]}, ["name", "custom_debit_account"])
		

		value = 0
		total_debit_amount = 0
		if add_sc_com:
			for row in add_sc_com:
				account = self.get_salary_component_account(row.name)
				if account in account_data.keys():
					amt = account_data.get(account)[1]/2
					value += amt
					debit_amount = account_data.get(account)[1] / 2
					journal_entry.append("accounts", {
						"account": row.custom_debit_account,
						"debit_in_account_currency": debit_amount,
						"credit_in_account_currency": 0,
						"cost_center": self.cost_center
					})
					total_debit_amount += debit_amount
		for i in journal_entry.accounts:
			if i.idx == last_index:
				i.credit_in_account_currency += value
		journal_entry.save(ignore_permissions=True)
		
		try:
			if submit_journal_entry:
				journal_entry.submit()

			if submitted_salary_slips:
				self.set_journal_entry_in_salary_slips(submitted_salary_slips, jv_name=journal_entry.name)

		except Exception as e:
			if type(e) in (str, list, tuple):
				frappe.msgprint(e)

			self.log_error("Journal Entry creation against Salary Slip failed")
			raise

		return journal_entry
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