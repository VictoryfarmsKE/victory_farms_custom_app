import frappe
from frappe import _
from frappe.utils import today, add_days, flt, get_year_ending, month_diff, get_year_start, get_first_day, get_last_day

def auto_create_leave_allocation():
	if get_last_day(today()) == today():
		leave_type_list = frappe.db.get_all("Leave Type", {"custom_create_auto_allocation": 1, "is_earned_leave": 1}, pluck="name")

		for row in leave_type_list:
			frappe.enqueue(create_leave_allocation, queue="long", event="Create Leave Allocation", leave_type=row, is_earned_leave=1)

@frappe.whitelist()
def create_leave_allocation(leave_type, is_earned_leave=0):
	if isinstance(is_earned_leave, str):
		is_earned_leave = int(is_earned_leave)

	lt_data = frappe.db.get_value("Leave Type", leave_type, ["applicable_after", "max_leaves_allowed", "custom_based_on_employee_grade"], as_dict=1)
	employee_filters = {}
	if lt_data.custom_based_on_employee_grade:
		grade_list = frappe.db.get_all("Leave Grade", {"parent": leave_type}, pluck="employee_grade")
		if grade_list:
			employee_filters.update({"grade": ["in", grade_list]})

	employee_data = frappe.db.get_all("Employee", employee_filters, ["name", "date_of_joining"])

	from_date = get_year_start(today())

	to_date = get_year_ending(today())

	for employee in employee_data:
		employee_from_date = from_date
		allocated_leaves = flt(lt_data.max_leaves_allowed / 12, 2) if is_earned_leave else lt_data.max_leaves_allowed
		if not is_earned_leave and from_date < employee.date_of_joining < to_date:
			condition_value = month_diff(to_date, employee.date_of_joining) if get_first_day(employee.date_of_joining) == employee.date_of_joining else (month_diff(to_date, employee.date_of_joining) - 1)
			allocated_leaves = flt(allocated_leaves * condition_value / 12, 2)
			employee_from_date = employee.date_of_joining

		if from_date < employee.date_of_joining:
			employee_from_date = employee.date_of_joining
		update_new_leaves_allocated(employee.name, leave_type, employee_from_date, to_date, allocated_leaves)


def update_new_leaves_allocated(employee_name, leave_type, from_date, to_date, allocated_leaves):

	if leave_allocation := frappe.get_doc("Leave Allocation", {"employee": employee_name, "leave_type": leave_type, "to_date": to_date}):
		leave_allocation.new_leaves_allocated += allocated_leaves
		leave_allocation.add_comment(text=_("Auto Allocation of {0} Days has been added").format(allocated_leaves))
		leave_allocation.save()
	
	else:
		leave_allocation = frappe.new_doc("Leave Allocation")
		leave_allocation.employee = employee_name
		leave_allocation.leave_type = leave_type
		leave_allocation.from_date = from_date
		leave_allocation.to_date = to_date
		leave_allocation.new_leaves_allocated = allocated_leaves
		leave_allocation.carry_forward = True
		leave_allocation.add_comment(text=_("Auto Allocation of {0} Days has been added").format(allocated_leaves))
		leave_allocation.save()