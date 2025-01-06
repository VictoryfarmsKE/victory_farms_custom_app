import frappe
import json
from datetime import datetime, timedelta
from frappe.utils import get_datetime, add_to_date


def validate(self, method):
	pass
	# check_existing_logs(self)


def check_existing_logs(self):
	if not self.shift:
		return

	shift_data = frappe.db.get_value(
		"Shift Type",
		self.shift,
		[
			"start_time",
			"end_time",
			"begin_check_in_before_shift_start_time",
			"allow_check_out_after_shift_end_time",
		],
		as_dict=1,
	)

	previous_log = frappe.db.get_all(
		"Employee Checkin",
		{
			"employee": self.employee,
			"name": ["!=", self.name],
			"time": ["<", self.time],
		},
		["name", "log_type"],
		order_by="time DESC",
		limit=1,
	)

	next_log = frappe.db.get_all(
		"Employee Checkin",
		{
			"employee": self.employee,
			"name": ["!=", self.name],
			"time": [">", self.time],
		},
		["name", "log_type"],
		order_by="time",
		limit=1,
	)
	
	if not previous_log and self.log_type == "OUT":
		return

	if not next_log and self.log_type == "IN":
		return

	if self.log_type == "OUT" and previous_log[0].log_type == "OUT":
		create_auto_in_out_log(self, shift_data, "IN")

	elif self.log_type == "IN" and next_log[0].log_type == "IN":
		create_auto_in_out_log(self, shift_data, "OUT")


def create_auto_in_out_log(self, shift_data, log_type):
	self.time = get_datetime(self.time)
	curr_date = self.time.date()

	days = - 1 if log_type == "IN" else 1
	shift_time = shift_data.start_time if log_type == "IN" else shift_data.end_time

	date_of_in = curr_date if shift_data.start_time < shift_data.end_time else curr_date + timedelta(days = days)

	new_checkin = frappe.new_doc("Employee Checkin")
	new_checkin.log_type = log_type
	new_checkin.time = datetime.combine(date_of_in,datetime.strptime(str(shift_time), '%H:%M:%S').time())
	new_checkin.employee = self.employee
	new_checkin.custom_auto_created = 1
	new_checkin.save()

def create_missing_values(selected_values):
	if not selected_values:
		return
	
	if isinstance(selected_values, str):
		selected_values = json.loads(selected_values)
	
	shift_data = frappe._dict()
	for row in selected_values:
		curr_log = frappe.db.get_value("Employee Checkin", row, ["name", "employee", "shift", "time", "log_type"], as_dict= 1)

		prev_log = frappe.db.get_value("Employee Checkin", {"name": ["!=", curr_log.name], "employee": curr_log.employee, "time": [">=", curr_log.time]}, ["name", "employee", "shift", "time", "log_type"], order_by="time desc", as_dict= 1)
		if prev_log and curr_log.log_type == prev_log.log_type:
			if not shift_data.get(prev_log.shift):
				field_name = "end_time" if curr_log.log_type == "IN" else "start_time"
				shift_data[prev_log.shift] = frappe.db.get_value("Shift", prev_log.shift, field_name)
			date = curr_log.time.date()
			time = curr_log.time.time()
			new_date = datetime.combine(date,datetime.strptime(str(shift_data[prev_log.shift]), '%H:%M:%S').time())
			if curr_log.log_type == "IN":
				if new_date.time() < time:
					new_date += timedelta(days=1)
				prev_log["new_time"] = new_date
				create_logs(prev_log, "OUT")
			else:
				if new_date.time() > time:
					new_date += timedelta(days= - 1)
				prev_log["new_time"] = new_date
				create_logs(prev_log, "IN")

def create_logs(log, log_type):
	ec_doc = frappe.new_doc("Employee Checkin")
	ec_doc.employee = log.employee
	ec_doc.log_type = log_type
	ec_doc.time = log.new_time
	ec_doc.shift = log.shift
	ec_doc.save()