import frappe
from frappe import _
from frappe.utils import today, add_days, flt, get_year_ending, month_diff, get_year_start, get_first_day, get_last_day
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on


def auto_create_leave_allocation():
	if str(get_last_day(today())) == str(today()):
		leave_type_list = frappe.db.get_all("Leave Type", {"custom_create_auto_allocation": 1, "is_earned_leave": 1}, pluck="name")
		for row in leave_type_list:
			frappe.enqueue(create_leave_allocation, queue="long", event="Create Leave Allocation", leave_type=row, is_earned_leave=1)

@frappe.whitelist()
def create_leave_allocation(leave_type, is_earned_leave=0):
	if isinstance(is_earned_leave, str):
		is_earned_leave = int(is_earned_leave)

	lt_data = frappe.db.get_value("Leave Type", leave_type, ["applicable_after", "custom_max_active_allowed_leaves as max_leaves_allowed", "custom_based_on_employee_grade",], as_dict=1)
	max_allowed_leaves = lt_data.max_leaves_allowed
	employee_filters = {"status": "Active"}
	if lt_data.custom_based_on_employee_grade:
		grade_list = frappe.db.get_all("Leave Grade", {"parent": leave_type}, pluck="employee_grade")
		if grade_list:
			employee_filters.update({"grade": ["in", grade_list]})

	employee_data = frappe.db.get_all("Employee", employee_filters, ["name", "date_of_joining"])

	from_date = get_year_start(today())

	to_date = get_year_ending(today())

	for employee in employee_data:
		employee_from_date = from_date
		allocated_leaves = flt(max_allowed_leaves / 12, 2) if is_earned_leave else max_allowed_leaves
		if not is_earned_leave and from_date < employee.date_of_joining < to_date:
			condition_value = month_diff(to_date, employee.date_of_joining) if get_first_day(employee.date_of_joining) == employee.date_of_joining else (month_diff(to_date, employee.date_of_joining) - 1)
			allocated_leaves = flt(allocated_leaves * condition_value / 12, 2)
			employee_from_date = employee.date_of_joining

		if from_date < employee.date_of_joining:
			employee_from_date = employee.date_of_joining
		try:
			update_new_leaves_allocated(employee.name, leave_type, employee_from_date, to_date, allocated_leaves, max_allowed_leaves)
		except Exception as e:
			frappe.log_error(title = "Leave Allocation Error", message = f"{e}")


def update_new_leaves_allocated(employee_name, leave_type, from_date, to_date, allocated_leaves, max_allowed_leaves):

	# Look for an existing Leave Allocation for this employee, leave type and period
	existing = frappe.get_all(
		"Leave Allocation",
		filters={"employee": employee_name, "leave_type": leave_type, "to_date": to_date},
		fields=["name"],
		limit_page_length=1,
	)

	if existing:
		leave_allocation = frappe.get_doc("Leave Allocation", existing[0].name)

		remaining_leaves = get_leave_balance_on(
			employee_name,
			leave_type,
			leave_allocation.from_date,
			to_date=leave_allocation.to_date,
			consider_all_leaves_in_the_allocation_period=True,
		)

		new_leaves_total = remaining_leaves + allocated_leaves
		extra_leave = allocated_leaves
		if new_leaves_total > max_allowed_leaves:
			extra_leave = max_allowed_leaves - remaining_leaves
			leave_allocation.new_leaves_allocated = leave_allocation.new_leaves_allocated + extra_leave
		else:
			leave_allocation.new_leaves_allocated += allocated_leaves

		leave_allocation.add_comment(text=_("Auto Allocation of {0} Days has been added").format(extra_leave))
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
 

def create_allocations_for_new_employee(doc, method=None):
	"""Create initial leave allocations for a newly created employee.

	This hook is intended to be called from `doc_events` on Employee `after_insert`.
	It will attempt to find common leave types (annual, sick full-day, sick half-day,
	and parental leave) and create allocations for the employee for the remainder
	of the current year (from the employee's date_of_joining).
	"""
	if not getattr(doc, "name", None):
		return

	employee_name = doc.name
	doj = getattr(doc, "date_of_joining", None) or today()
	gender = getattr(doc, "gender", "").lower()

	year_start = get_year_start(doj)
	year_end = get_year_ending(doj)

	# Exact Leave Type names to consider
	leave_type_names = {
		"annual": "Annual Leave",
		"sick_full": "Sick Leave - Full Days",
		"sick_half": "Sick Leave - Half Days",
		"maternity": "Maternity Leave",
		"paternity": "Paternity Leave",
	}

	# Determine which parental type to allocate based on gender
	parental_key = "maternity" if gender in ("female", "f") else "paternity"

	# Build list of leave type names we will query (only those relevant)
	requested = [leave_type_names["annual"], leave_type_names["sick_full"], leave_type_names["sick_half"], leave_type_names[parental_key]]

	# Fetch leave type rows in a single DB call
	lt_rows = frappe.get_all(
		"Leave Type",
		filters={"name": ["in", requested]},
		fields=["name", "custom_max_active_allowed_leaves", "is_earned_leave"],
	)
	lt_map = {row.name: row for row in lt_rows}

	# Standard defaults
	defaults = {"Sick Leave - Full Days": 7, "Sick Leave - Half Days": 7, "Maternity Leave": 90, "Paternity Leave": 14, "Annual Leave": 0}

	# Iterate requested leave types (stable order) and allocate
	for lt_name in requested:
		try:
			if lt_name not in lt_map:
				# skip missing leave types
				continue

			row = lt_map[lt_name]
			max_allowed = row.custom_max_active_allowed_leaves or defaults.get(lt_name, 0)
			is_earned = bool(row.is_earned_leave)

			# Calculate allocation:
			if is_earned:
				allocated = flt(max_allowed / 12, 2)
				employee_from_date = doj
			else:
				allocated = max_allowed
				employee_from_date = year_start
				if lt_name == "Annual Leave" and year_start < doj < year_end:
					months = month_diff(year_end, doj) if get_first_day(doj) == doj else (month_diff(year_end, doj) - 1)
					allocated = flt((allocated * months) / 12, 2)
					employee_from_date = doj

			update_new_leaves_allocated(employee_name, lt_name, employee_from_date, year_end, allocated, max_allowed)
		except Exception as e:
			frappe.log_error(title="New Employee Leave Allocation Error", message=f"{employee_name} / {lt_name}: {e}")


def create_allocations_for_new_employee_from_name(docname):
	"""Helper to call allocation function by docname (safe for background jobs)."""
	try:
		doc = frappe.get_doc("Employee", docname)
	except Exception:
		return
	create_allocations_for_new_employee(doc)


def enqueue_create_allocations_for_new_employee(doc, method=None):
	"""Enqueue the allocation job to avoid long-running locks during Employee creation."""
	try:
		frappe.enqueue(
			method="victory_farms_custom_app.victory_farms_custom_app.customization.leave_type.leave_type.create_allocations_for_new_employee_from_name",
			queue="long",
			timeout=600,
			docname=doc.name,
		)
	except Exception as e:
		frappe.log_error(title="Enqueue Allocation Failed", message=str(e))
		try:
			create_allocations_for_new_employee(doc)
		except Exception:
			pass