# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, get_last_day
from frappe.model.document import Document

class CommercialHolidayPay(Document):
	def validate(self):
		update_days(self)
		update_amounts(self)

	def on_submit(self):
		create_additional_salary(self)


def update_days(self):
	if not self.from_date:
		return

	if self.to_date < self.from_date:
		frappe.throw(_("From date can not be less than to date"))

	if self.from_date == self.to_date:
		self.number_of_days = 1
		return

	self.number_of_days = date_diff(self.to_date, self.from_date) + 1


def update_amounts(self):
	if not self.number_of_days:
		return

	gross_pay = frappe.db.get_value("Employee", self.employee, "ctc")

	if not gross_pay:
		grade = frappe.db.get_value("Employee", self.employee, "grade")

		if not grade:
			frappe.throw(_("Grade is not Assigned to the Employee"))

		gross_pay = frappe.db.get_value("Grade", grade, "default_base_pay")

	
	if not gross_pay:
		frappe.throw(_("Gross Pay not found"))

	gross_pay_per_day = gross_pay / 30

	self.commercial_amount = self.number_of_days * gross_pay_per_day


def create_additional_salary(self):
	if not self.number_of_days:
		return
	
	payroll_date = get_last_day(self.to_date or self.posting_date)
	
	relieving_date = frappe.db.get_value("Employee", self.employee, "relieving_date")
	
	if relieving_date and payroll_date > relieving_date:
		payroll_date = relieving_date

	ads_doc = frappe.new_doc("Additional Salary")
	ads_doc.employee = self.employee
	ads_doc.payroll_date = payroll_date
	ads_doc.currecy = self.currency
	ads_doc.amount = self.commercial_amount
	ads_doc.override_salary_structure_amount = 1

	ads_doc.salary_component = frappe.db.get_single_value("Payroll Settings", "custom_commercial_holiday_component")

	if not ads_doc.salary_component:
		frappe.throw(_("Salary Component is not defined in Payroll Setting"))
	
	ads_doc.ref_doctype = self.doctype
	ads_doc.ref_docname = self.name

	ads_doc.save()
