# Copyright (c) 2026, Solufy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	return OvertimeHoursReport(filters).run()


class OvertimeHoursReport:
	"""Overtime Hours Report Based On Timesheet (entry-level)

	This report lists each Timesheet Detail entry (ttd) with start/end times,
	activity type and hours. It requires `docstatus` filter and validates dates.
	"""

	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})

		self.from_date = getdate(self.filters.from_date)
		self.to_date = getdate(self.filters.to_date)

		self.validate_filters()
		self.validate_dates()
  
	def validate_filters(self):
		if not self.filters.get("docstatus"):
			frappe.throw(_("Please select Document Status"))

		ds_map = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
		if self.filters.docstatus not in ds_map:
			frappe.throw(_("Invalid Document Status. Choose Draft, Submitted or Cancelled."))

		self.docstatus = ds_map[self.filters.docstatus]

	def validate_dates(self):
		self.day_span = (self.to_date - self.from_date).days

		if self.day_span <= 0:
			frappe.throw(_("From Date must come before To Date"))


	def run(self):
		self.generate_columns()
		self.generate_data()
		self.generate_report_summary()
		self.generate_chart_data()

		return self.columns, self.data, None, self.chart, self.report_summary

	def generate_columns(self):
		self.columns = [
			{"label": _("Timesheet"), "fieldname": "timesheet", "fieldtype": "Link", "options": "Timesheet", "width": 200},
			{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 200},
			{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
			{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 200},
			{"label": _("Start Time"), "fieldname": "start_time", "fieldtype": "Datetime", "width": 200},
			{"label": _("End Time"), "fieldname": "end_time", "fieldtype": "Datetime", "width": 200},
			{"label": _("Activity Type"), "fieldname": "activity_type", "fieldtype": "Data", "width": 200},
			# {"label": _("OT Rate"), "fieldname": "ot_rate", "fieldtype": "Data", "width": 80}
			{"label": _("Hours"), "fieldname": "hours", "fieldtype": "Float", "width": 100},
			{"label": _("Notes"), "fieldname": "notes", "fieldtype": "Data", "width": 200},
		]

	def generate_filtered_time_logs(self):
		additional_filters = ""
		if self.filters.get("employee"):
			additional_filters += f" AND tt.employee = {self.filters.get('employee')!r}"
		if self.filters.get("company"):
			additional_filters += f" AND tt.company = {self.filters.get('company')!r}"
		if self.filters.get("activity_type"):
			additional_filters += f" AND ttd.activity_type = {self.filters.get('activity_type')!r}"

		docstatus_cond = f"AND tt.docstatus = {int(self.docstatus)}"

		self.filtered_time_logs = frappe.db.sql(
			f"""
			SELECT
				tt.employee AS employee,
				tt.name AS timesheet,
				tt.note AS notes,
				ttd.from_time AS start_time,
				ttd.to_time AS end_time,
				ttd.activity_type AS activity_type,
				ttd.hours AS hours
			FROM `tabTimesheet Detail` AS ttd
			JOIN `tabTimesheet` AS tt
				ON ttd.parent = tt.name
			WHERE tt.employee IS NOT NULL
			AND tt.start_date BETWEEN '{self.filters.from_date}' AND '{self.filters.to_date}'
			AND tt.end_date BETWEEN '{self.filters.from_date}' AND '{self.filters.to_date}'
			{docstatus_cond}
			{additional_filters}
		""",
		)

	@staticmethod
	def _classify_ot_rate(activity_type):
		"""Return '2.0x', '1.5x' or '' based on the activity type name."""
		if not activity_type:
			return ""
		name = activity_type.lower()
		if "2.0" in name or "double" in name:
			return "2.0x"
		if "1.5" in name or "time and a half" in name:
			return "1.5x"
		return ""

	def generate_data(self):
		self.generate_filtered_time_logs()

		self.data = []
		total_hours = 0.0
		ot_1_5_hours = 0.0
		ot_2_0_hours = 0.0
		unique_employees = set()

		for emp, timesheet, notes, start_time, end_time, activity_type, hours in self.filtered_time_logs:
			row = frappe._dict()
			row["employee"] = emp
			row["timesheet"] = timesheet
			row["start_time"] = start_time
			row["end_time"] = end_time
			row["activity_type"] = activity_type
			row["ot_rate"] = self._classify_ot_rate(activity_type)
			row["hours"] = flt(hours, 2)
			row["notes"] = notes
			row["employee_name"] = frappe.db.get_value("Employee", emp, "employee_name")
			row["department"] = frappe.db.get_value("Employee", emp, "department")

			self.data.append(row)

			total_hours += row["hours"]
			unique_employees.add(emp)
			if row["ot_rate"] == "1.5x":
				ot_1_5_hours += row["hours"]
			elif row["ot_rate"] == "2.0x":
				ot_2_0_hours += row["hours"]

		if self.filters.get("department"):
			self.data = [r for r in self.data if r.get("department") == self.filters.department]

		if self.filters.get("activity_type"):
			needle = (self.filters.get("activity_type") or "").strip().lower()
			if needle:
				self.data = [r for r in self.data if r.get("activity_type") and needle in (r.get("activity_type") or "").lower()]

		self.data.sort(key=lambda r: (r.get("employee") or "", r.get("start_time") or ""))

		self._total_hours = flt(total_hours, 2)
		self._ot_1_5_hours = flt(ot_1_5_hours, 2)
		self._ot_2_0_hours = flt(ot_2_0_hours, 2)
		self._unique_employee_count = len(unique_employees)

	def generate_report_summary(self):
		self.report_summary = []

		if not self.data:
			return

		self.report_summary = [
			{"value": self._total_hours, "label": _("Total OT Hours"), "datatype": "Float"},
			{"value": self._ot_1_5_hours, "label": _("OT @ 1.5x Hours"), "datatype": "Float"},
			{"value": self._ot_2_0_hours, "label": _("OT @ 2.0x Hours"), "datatype": "Float"},
			{"value": self._unique_employee_count, "label": _("Employees on OT"), "datatype": "Int"},
		]

	def generate_chart_data(self):
		# Aggregate OT hours per employee 
		emp_ot = {}
		for r in self.data:
			emp = r.get("employee_name") or r.get("employee") or "Unknown"
			emp_ot.setdefault(emp, {"1.5x": 0.0, "2.0x": 0.0})
			rate = r.get("ot_rate")
			if rate in ("1.5x", "2.0x"):
				emp_ot[emp][rate] += flt(r.get("hours"), 2)

		# Limit to 30 employees with the hieghst total OT hours
		sorted_emps = sorted(emp_ot.keys(), key=lambda e: emp_ot[e]["1.5x"] + emp_ot[e]["2.0x"], reverse=True)[:30]

		self.chart = {
			"data": {
				"labels": sorted_emps,
				"datasets": [
					{"name": _("OT @ 1.5x"), "values": [emp_ot[e]["1.5x"] for e in sorted_emps]},
					{"name": _("OT @ 2.0x"), "values": [emp_ot[e]["2.0x"] for e in sorted_emps]},
				],
			},
			"type": "bar",
			"barOptions": {"stacked": True},
		}
