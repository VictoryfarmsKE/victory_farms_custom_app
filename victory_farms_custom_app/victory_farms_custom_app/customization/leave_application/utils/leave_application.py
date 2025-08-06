import frappe
from frappe import _
from frappe.utils import getdate

@frappe.whitelist()
def check_probation_and_restriction(employee, leave_type, from_date):
    emp = frappe.db.get_value("Employee", employee, ["probation_start_date", "probation_end_date"], as_dict=True)
    leave_type_details = frappe.db.get_value("Leave Type", leave_type, ["custom_restricted_in_probation"], as_dict=True)

    if not (emp and leave_type_details):
        return {"show_dialog": False}

    probation_start = getdate(emp.probation_start_date) if emp.probation_start_date else None
    probation_end = getdate(emp.probation_end_date) if emp.probation_end_date else None
    leave_from = getdate(from_date) if from_date else None

    if (
        leave_type_details.custom_restricted_in_probation
        and probation_start and probation_end and leave_from
        and probation_start <= leave_from <= probation_end
    ):
        return {"show_dialog": True}

    return {"show_dialog": False}
