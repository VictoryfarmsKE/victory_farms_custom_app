import frappe
from frappe.utils import today, add_days, flt, get_year_ending, month_diff, get_year_start, get_first_day, get_last_day

def auto_create_leave_allocation():
	if get_last_day(today()) == today():
		leave_type_list = frappe.db.get_all("Leave Type", {"custom_create_auto_allocation": 1, "is_earned_leave": 1}, pluck = "name")

		for row in leave_type_list:
			frappe.enqueue(create_leave_allocation, queue = "long", event = "Create Leave Allocation", leave_type = row, is_earned_leave = 1)

@frappe.whitelist()
def create_leave_allocation(leave_type, is_earned_leave = 0):
	if isinstance(is_earned_leave, str):
		is_earned_leave = int(is_earned_leave)

	lt_data = frappe.db.get_value("Leave Type", leave_type, ["applicable_after", "max_leaves_allowed", "custom_based_on_employee_grade"], as_dict= 1)
	employee_filters = {"date_of_joining" :["<=", add_days(today(), days = -(lt_data.applicable_after))]}
	if lt_data.custom_based_on_employee_grade:
		grade_list = frappe.db.get_all("Leave Grade", {"parent": leave_type}, pluck = "employee_grade")
		if grade_list:
			employee_filters.update({"grade": ["in", grade_list]})
	employee_data = frappe.db.get_all("Employee", employee_filters, ["name", "date_of_joining"])

	if get_last_day(today()) == today():
		from_date = add_days(today(), days = 1) if is_earned_leave else get_year_start(today())
	else:
		from_date = get_first_day(today()) if is_earned_leave else get_year_start(today())

	to_date = get_last_day(from_date) if is_earned_leave else get_year_ending(today())

	for employee in employee_data:
		employee_from_date = from_date
		allocated_leaves = flt(lt_data.max_leaves_allowed / 12, 2) if is_earned_leave else lt_data.max_leaves_allowed
		if not is_earned_leave and from_date < employee.date_of_joining < to_date:
			condition_value = month_diff(to_date, employee.date_of_joining) if get_first_day(employee.date_of_joining) == employee.date_of_joining else (month_diff(to_date, employee.date_of_joining) - 1)
			allocated_leaves = flt(allocated_leaves * condition_value / 12, 2)
			employee_from_date = employee.date_of_joining

		if frappe.db.get_value("Leave Allocation", {"employee": employee.name, "leave_type": leave_type, "from_date": employee_from_date}):
			continue

		leave_all_doc = frappe.new_doc("Leave Allocation")
		leave_all_doc.employee = employee.name
		leave_all_doc.leave_type = leave_type
		leave_all_doc.from_date = employee_from_date
		leave_all_doc.to_date = to_date
		leave_all_doc.carry_forward = 1 if is_earned_leave else 0
		leave_all_doc.new_leaves_allocated = allocated_leaves
		try:
			leave_all_doc.save()
		except Exception as e:
			frappe.log_error(title = f"Not able to perform Leave Allocation for {employee.name}", message = f"{e}")