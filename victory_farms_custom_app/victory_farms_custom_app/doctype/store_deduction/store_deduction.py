# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_first_day, today

class StoreDeduction(Document):
	def on_submit(self):
		salary_component = frappe.db.get_value("Salaty Componet")
		
		payroll_date = get_first_day(self.posting_date)

		if ads_name:= frappe.db.get_value("Additional salary", {"docstatus": 0, "from_date": payroll_date, "salary_component": salary_component, "employee": self.employee}):
			ads_doc = frappe.get_doc("Additional Salary", ads_name)
			ads_doc.amount += self.item_cost
			ads_doc.save()
			self.db_set("remaining_payments", self.remaining_payments - 1)
		
		else:
			ads_doc = frappe.new_doc("Additional Salary")
			ads_doc.salary_component = "test"
			ads_doc.employee = self.employee
			ads_doc.payroll_date = payroll_date
			ads_doc.currency = frappe.db.get_value("Employee", self.employee, "salary_currency")
			ads_doc.amount = self.item_cost
			ads_doc.overwrite_salary_structure_amount = 1
			ads_doc.save()

			self.db_set("remaining_payments", self.period_of_payment - 1)


def create_remaining_payments():
	ads_list = frappe.db.get_all("Store Deduction", {"remaining_payments": [">", 0], "docstatus": 1}, pluck = "name")
	payroll_date = get_first_day(today())
	for row in ads_list:
		sd_doc = frappe.get_doc("Store Deduction", row)
		ads_doc = frappe.new_doc("Additional Salary")
		ads_doc.salary_component = "test"
		ads_doc.employee = sd_doc.employee
		ads_doc.payroll_date = payroll_date
		ads_doc.currency = frappe.db.get_value("Employee", sd_doc.employee, "salary_currency")
		ads_doc.amount = sd_doc.item_cost
		ads_doc.overwrite_salary_structure_amount = 1
		ads_doc.save()

		sd_doc.db_set("remaining_payments", sd_doc.period_of_payment - 1)