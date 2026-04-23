# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, add_months


def _has_store_deduction_detail(ads_doc, store_deduction_name):
	return any(
		(row.store_deduction == store_deduction_name)
		for row in (ads_doc.get("custom_store_deduction_details") or [])
	)

class StoreDeduction(Document):
	def on_submit(self):
		salary_component = frappe.db.get_value("Salary Component", {"is_for_store_deduction": 1})
		# Ensure period_of_payment has a sensible default before dividing
		if not self.period_of_payment:
			self.period_of_payment = 5 if self.item_cost > 1000 else 1
			self.db_set("period_of_payment", self.period_of_payment)

		# per-period cost (guard division)
		per_period_cost = (self.item_cost / self.period_of_payment) if (self.period_of_payment and self.period_of_payment > 0) else self.item_cost

		# If posting was after 25th, first deduction rolls to next month's 25th
		posting_date = getdate(self.posting_date)
		if posting_date.day > 25:
			first_payroll = getdate(add_months(posting_date, 1)).replace(day=25)
		else:
			first_payroll = posting_date.replace(day=25)

		# Create only the first-period Additional Salary on submit; cron will create later periods
		ads_name = frappe.db.get_value("Additional Salary", {"docstatus": 0, "payroll_date": first_payroll, "salary_component": salary_component, "employee": self.employee})
		if ads_name:
			ads_doc = frappe.get_doc("Additional Salary", ads_name)
			if _has_store_deduction_detail(ads_doc, self.name):
				return
			ads_doc.amount = (ads_doc.amount or 0) + per_period_cost
		else:
			ads_doc = frappe.new_doc("Additional Salary")
			ads_doc.salary_component = salary_component
			ads_doc.employee = self.employee
			ads_doc.payroll_date = first_payroll
			ads_doc.currency = "KES"
			ads_doc.amount = per_period_cost
			ads_doc.overwrite_salary_structure_amount = 1

		# initialize remaining_payments (P-1) and compute balances
		self.db_set("remaining_payments", max(0, int(self.period_of_payment) - 1))
		opening_balance = int(self.period_of_payment) * per_period_cost
		closing_balance = (int(self.period_of_payment) - 1) * per_period_cost

		ads_doc.append("custom_store_deduction_details", {
			"store_deduction": self.name,
			"item_cost": self.item_cost,
			"item": self.item,
			"opening_balance": opening_balance,
			"closing_balance": closing_balance
		})
		ads_doc.save()


def create_remaining_payments():
	from frappe.utils import today, getdate
	# run only between the 20th and 24th of the month
	todays_date = today()
	if not (20 <= getdate(todays_date).day <= 24):
		return

	ads_list = frappe.db.get_all("Store Deduction", {"remaining_payments": [">", 0], "docstatus": 1}, pluck = "name")
	salary_component = frappe.db.get_value("Salary Component", {"is_for_store_deduction": 1})
	for row in ads_list:
		sd_doc = frappe.get_doc("Store Deduction", row)
		emp_data = frappe.db.get_value("Employee", sd_doc.employee, ["salary_currency", "relieving_date", "status"], as_dict = 1)
		if emp_data.status == "Inactive":
			continue
		# per-period cost
		if sd_doc.period_of_payment and sd_doc.period_of_payment > 1:
			per_period = sd_doc.item_cost / sd_doc.period_of_payment
		else:
			per_period = sd_doc.item_cost

		# payroll_date is the 25th of current month unless relieving_date
		if emp_data.relieving_date:
			payroll_date = emp_data.relieving_date
		else:
			payroll_date = getdate(todays_date).replace(day=25)

		if ads_name:= frappe.db.get_value("Additional Salary", {"docstatus": 0, "payroll_date": payroll_date, "salary_component": salary_component, "employee": sd_doc.employee}):
			ads_doc = frappe.get_doc("Additional Salary", ads_name)
			if _has_store_deduction_detail(ads_doc, row):
				continue
			ads_doc.amount = (ads_doc.amount or 0) + (per_period if not emp_data.relieving_date else per_period * sd_doc.remaining_payments)

		else:
			ads_doc = frappe.new_doc("Additional Salary")
			ads_doc.salary_component = salary_component
			ads_doc.employee = sd_doc.employee
			ads_doc.payroll_date = payroll_date
			ads_doc.currency = "KES"
			ads_doc.amount = per_period if not emp_data.relieving_date else per_period * sd_doc.remaining_payments
			ads_doc.overwrite_salary_structure_amount = 1
		try:
			opening_balance = sd_doc.remaining_payments * per_period
			if not emp_data.relieving_date:
				closing_balance = (sd_doc.remaining_payments - 1) * per_period
			else:
				closing_balance = 0
			ads_doc.append("custom_store_deduction_details", {
				"store_deduction": row,
				"item_cost": sd_doc.item_cost,
				"item": sd_doc.item,
				"opening_balance": opening_balance,
				"closing_balance": closing_balance
			})
			ads_doc.save()
			if not emp_data.relieving_date:
				sd_doc.db_set("remaining_payments", sd_doc.remaining_payments - 1)
			else:
				sd_doc.db_set("remaining_payments", 0)
		except Exception as e:
			frappe.log_error(title = f"Additional Salary Generation error for {sd_doc.employee}", message = f"{e}")
