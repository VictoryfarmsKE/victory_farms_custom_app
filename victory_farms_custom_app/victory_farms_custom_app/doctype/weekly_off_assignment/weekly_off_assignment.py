# Copyright (c) 2024, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_weekday, getdate
from frappe.model.document import Document


class WeeklyOffAssignment(Document):
	def validate(self):
		if self.weekly_off_date < frappe.utils.today():
			frappe.throw(_("Past Dated entries are not allowed"))

	def on_submit(self):
		holiday_list = []

		for row in self.employee_details:
			if row.holiday_list not in holiday_list:
				holiday_list.append(row.holiday_list)

		for row in holiday_list:
			hd_doc = frappe.get_doc("Holiday List", row)
			existing_dates = [row.holiday_date for row in hd_doc.holidays]
			if self.weekly_off_date in existing_dates:
				continue

			hd_doc.append("holidays", {
				"holiday_date": self.weekly_off_date,
				"weekly_off": 1,
				"description": get_weekday(getdate(self.weekly_off_date))
			})
			hd_doc.flags.ignore_permissions = True
			hd_doc.save()
