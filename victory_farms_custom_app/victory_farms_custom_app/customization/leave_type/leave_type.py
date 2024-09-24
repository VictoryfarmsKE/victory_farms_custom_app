import frappe
import data
from frappe.utils import today, add_days, flt, get_year_ending, is_last_day_of_the_month


def auto_create_leave_allocation():
    if is_last_day_of_the_month(today()):
        leave_type_list = frappe.db.get_all("Leave Type", {"custom_create_auto_allocation": 1, "is_earned_leave": 1}, pluck = "name")

        for row in leave_type_list:
            create_leave_allocation(row)

@frappe.whitelist()
def create_leave_allocation(name):
    lt_data = frappe.db.get_value("Leave Type", name, ["applicable_after", "max_leaves_allowed", "custom_based_on_employee_grade"], as_dict= 1)
    employee_filters = {"date_of_joining" :["<=", add_days(today(), days = -(lt_data.applicable_after))]}
    if lt_data.custom_based_on_employee_grade:
        grade_list = frappe.db.get_all("Leave Grade", {"parent": name}, pluck = "employee_grade")
        if grade_list:
            employee_filters.update({"grade": ["in", grade_list]})
    employee_list = frappe.db.get_all("Employee", employee_filters, pluck = "name")

    for employee in employee_list:
        leave_all_doc = frappe.new_doc("Leave Allocation")
        leave_all_doc.employee = employee
        leave_all_doc.leave_type = name
        leave_all_doc.from_date = today()
        leave_all_doc.to_date = get_year_ending(today())
        leave_all_doc.new_leaves_allocated = flt(lt_data.max_leaves_allowed / 12, 2)
        leave_all_doc.save()