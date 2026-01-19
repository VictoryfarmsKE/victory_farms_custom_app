# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, get_last_day, getdate
from datetime import timedelta
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

	# Compute commercial amount by allocating days across calendar-month segments
	from_date = getdate(self.from_date)
	to_date = getdate(self.to_date)

	month_last_day = get_last_day(from_date)
	if month_last_day >= to_date:
		seg_start = from_date
		seg_end = to_date
		seg_calendar_days = (date_diff(seg_end, seg_start) + 1) if seg_end != seg_start else 1
		seg_days_in_month = get_last_day(seg_start).day
		seg_daily = gross_pay / seg_days_in_month if seg_days_in_month else gross_pay / 30
		total_amount = seg_calendar_days * seg_daily
	else:
		next_month_start = month_last_day + timedelta(days=1)
		# first segment
		seg1_calendar_days = (date_diff(month_last_day, from_date) + 1) if month_last_day != from_date else 1
		seg1_days_in_month = get_last_day(from_date).day
		seg1_daily = gross_pay / seg1_days_in_month if seg1_days_in_month else gross_pay / 30
		seg1_amount = seg1_calendar_days * seg1_daily
		# second segment
		seg2_calendar_days = (date_diff(to_date, next_month_start) + 1) if to_date != next_month_start else 1
		seg2_days_in_month = get_last_day(next_month_start).day
		seg2_daily = gross_pay / seg2_days_in_month if seg2_days_in_month else gross_pay / 30
		seg2_amount = seg2_calendar_days * seg2_daily
		total_amount = seg1_amount + seg2_amount

	self.commercial_amount = total_amount


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

	ads_doc.salary_component = self.salary_component

	if not ads_doc.salary_component:
		frappe.throw(_("Salary Component is Mandatory"))
	
	ads_doc.ref_doctype = self.doctype
	ads_doc.ref_docname = self.name

	ads_doc.save()
