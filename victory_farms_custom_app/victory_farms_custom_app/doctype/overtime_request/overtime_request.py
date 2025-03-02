# Copyright (c) 2025, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_fiscal_year
from datetime import datetime
from pypika import Criterion
from nl_attendance_timesheet.controllers.generate_overtime_timesheets import calculate_holiday_hours, create_new_timesheet, get_from_time_and_hours


class OvertimeRequest(Document):
	def on_submit(self):
		if not self.employee_list:
			return
		
		SETTINGS_DOCTYPE = 'Navari Custom Payroll Settings'
		overtime_15 = frappe.db.get_single_value(SETTINGS_DOCTYPE, 'overtime_15_activity')
		overtime_20 = frappe.db.get_single_value(SETTINGS_DOCTYPE, 'overtime_20_activity')

		for row in self.employee_list:
			if isinstance(row.end_time, str):
				row.end_time = datetime.strptime(row.end_time, "%H:%M:%S")
			self.create_timesheet(row, overtime_15, overtime_20)
	
	def create_timesheet(self, row, overtime_15, overtime_20):
		attendance = frappe.qb.DocType("Attendance")
		employee = frappe.qb.DocType("Employee")
		shift_type = frappe.qb.DocType("Shift Type")

		conditions = [attendance.docstatus == 1, attendance.status == "Present", employee.name == row.employee_id, attendance.attendance_date == self.overtime_date]

		query = frappe.qb.from_(attendance) \
			.inner_join(employee) \
			.on(employee.name == attendance.employee) \
			.left_join(shift_type) \
			.on(attendance.shift == shift_type.name) \
			.select(
			attendance.employee.as_("employee"),
			attendance.employee_name.as_("employee_name"),
			attendance.name.as_("name"),
			attendance.shift.as_("shift"),
			attendance.attendance_date.as_("attendance_date"),
			attendance.in_time.as_("in_time"),
			attendance.out_time.as_("out_time"),
			attendance.working_hours.as_("working_hours"),
			employee.company.as_("company"),
			employee.department.as_("department"),
			shift_type.start_time.as_("shift_start_time"),
			shift_type.end_time.as_("shift_end_time"),
			shift_type.min_hours_to_include_a_break,
			shift_type.unpaid_breaks_minutes.as_("unpaid_breaks_minutes"),
		).where(Criterion.all(conditions))

		attendance_records = query.run(as_dict=True)

		fiscal_year = None

		holiday_data= frappe._dict()
		for entry in attendance_records:
			change_hours = row.end_time.hour
			minutes = row.end_time.minute
			entry.out_time = entry.out_time.replace(hour=change_hours, minute=minutes)
			if not holiday_data.get(entry.employee):
				date = entry.in_time.date() or entry.out_time.date()
				if not fiscal_year:
					fiscal_year = get_fiscal_year(date)[0]
				holiday_data[entry.employee] = frappe.db.get_value("Holiday List", {"custom_employee": entry.employee, "custom_fiscal_year": fiscal_year})
			if holiday_data.get(entry.employee):
				holiday_dates = frappe.db.get_all('Holiday', filters={'parent': holiday_data[entry.employee]}, pluck='holiday_date')
				if entry.attendance_date in holiday_dates:
					total_work_duration = calculate_holiday_hours(entry)
					if total_work_duration:
						create_new_timesheet(entry.employee, entry.employee_name, entry.company, entry.department,
											overtime_20, entry.in_time, entry.working_hours, entry.name)
				else:
					from_time, hours = get_from_time_and_hours(entry)
					if from_time and hours:
						create_new_timesheet(entry.employee, entry.employee_name, entry.company, entry.department,
											overtime_15, from_time, hours, entry.name)
			else:
				from_time, hours = get_from_time_and_hours(entry)
				if from_time and hours:
					create_new_timesheet(entry.employee, entry.employee_name, entry.company, entry.department, overtime_15,
										from_time, hours, entry.name)