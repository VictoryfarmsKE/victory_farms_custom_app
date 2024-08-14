import frappe
from frappe.utils import flt
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

class CustomSalarySlip(SalarySlip):
	def add_structure_components(self, component_type):
		self.data, self.default_data = self.get_data_for_eval()

		timesheet_component = frappe.db.get_value(
			"Salary Structure", self.salary_structure, "salary_component"
		)

		for struct_row in self._salary_structure_doc.get(component_type):
			if self.salary_slip_based_on_timesheet and struct_row.salary_component == timesheet_component:
				continue
			amount = self.eval_condition_and_formula(struct_row, self.data)
			# if struct_row.parentfield == "deductions" and struct_row.salary_component == "Insurance Relief":
			# 	frappe.throw(f"{amount}")
			if struct_row.statistical_component:
				# update statitical component amount in reference data based on payment days
				# since row for statistical component is not added to salary slip

				self.default_data[struct_row.abbr] = flt(amount)
				if struct_row.depends_on_payment_days:
					joining_date, relieving_date = self.get_joining_and_relieving_dates()
					payment_days_amount = (
						flt(amount) * flt(self.payment_days) / cint(self.total_working_days)
						if self.total_working_days
						else 0
					)
					self.data[struct_row.abbr] = flt(payment_days_amount, struct_row.precision("amount"))

			else:
				# default behavior, the system does not add if component amount is zero
				# if remove_if_zero_valued is unchecked, then ask system to add component row
				remove_if_zero_valued = frappe.get_cached_value(
					"Salary Component", struct_row.salary_component, "remove_if_zero_valued"
				)

				default_amount = 0

				for row in self.get(component_type):
					if not amount and row.get("salary_component") == struct_row.salary_component:
						self.remove(row)

				if (
					amount
					or (struct_row.amount_based_on_formula and amount is not None)
					or (not remove_if_zero_valued and amount is not None and not self.data[struct_row.abbr])
				):
					default_amount = self.eval_condition_and_formula(struct_row, self.default_data)
					self.update_component_row(
						struct_row,
						amount,
						component_type,
						data=self.data,
						default_amount=default_amount,
						remove_if_zero_valued=remove_if_zero_valued,
					)

	def update_component_row(
		self,
		component_data,
		amount,
		component_type,
		additional_salary=None,
		is_recurring=0,
		data=None,
		default_amount=None,
		remove_if_zero_valued=None,
	):
		component_row = None
		for d in self.get(component_type):
			if d.salary_component != component_data.salary_component:
				continue

			if (not d.additional_salary and (not additional_salary or additional_salary.overwrite)) or (
				additional_salary and additional_salary.name == d.additional_salary
			):
				component_row = d
				break

		if additional_salary and additional_salary.overwrite:
			# Additional Salary with overwrite checked, remove default rows of same component
			self.set(
				component_type,
				[
					d
					for d in self.get(component_type)
					if d.salary_component != component_data.salary_component
					or (d.additional_salary and additional_salary.name != d.additional_salary)
					or d == component_row
				],
			)

		if not component_row:
			if not (amount or default_amount) and remove_if_zero_valued:
				return

			component_row = self.append(component_type)
			for attr in (
				"depends_on_payment_days",
				"salary_component",
				"abbr",
				"do_not_include_in_total",
				"is_tax_applicable",
				"is_flexible_benefit",
				"variable_based_on_taxable_salary",
				"exempted_from_income_tax",
			):
				component_row.set(attr, component_data.get(attr))

		if additional_salary:
			if additional_salary.overwrite:
				component_row.additional_amount = flt(
					flt(amount) - flt(component_row.get("default_amount", 0)),
					component_row.precision("additional_amount"),
				)
			else:
				component_row.default_amount = 0
				component_row.additional_amount = amount

			component_row.is_recurring_additional_salary = is_recurring
			component_row.additional_salary = additional_salary.name
			component_row.deduct_full_tax_on_selected_payroll_date = (
				additional_salary.deduct_full_tax_on_selected_payroll_date
			)
		else:
			component_row.default_amount = default_amount or amount
			component_row.additional_amount = 0
			component_row.deduct_full_tax_on_selected_payroll_date = (
				component_data.deduct_full_tax_on_selected_payroll_date
			)

		component_row.amount = amount

		self.update_component_amount_based_on_payment_days(component_row, remove_if_zero_valued)

		if data:
			data[component_row.abbr] = component_row.amount

		if component_data.get("salary_component") and frappe.db.get_value("Salary Component", component_data.get("salary_component"), "custom_is_negative_component"):
			component_row.amount *= -1

def before_validate(self, method):
	update_to_date(self)

def update_to_date(self):
	relieving_date = frappe.db.get_value("Employee", self.employee, "relieving_date")

	if not relieving_date or frappe.utils.getdate(self.posting_date) < relieving_date:
		return
	
	self.end_date = relieving_date