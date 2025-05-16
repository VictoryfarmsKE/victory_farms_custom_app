import frappe
from frappe.utils import flt, get_last_day, date_diff
from datetime import timedelta

def create_additional_salary(self):
    if self.status != "Approved":
        return

    # Check if Leave Type is "Unpaid Leave" and Employee Grade contains "H"
    employee_grade = frappe.db.get_value("Employee", self.employee, "grade")
    if self.leave_type == "Unpaid Leave" and employee_grade and "H" in employee_grade:
        frappe.msgprint(
            msg="Additional Salary will not be created for 'Unpaid Leave' when the employee grade contains 'H'.",
            title="Notice",
            indicator="orange"
        )
        return  # Prevent additional salary creation

    salary_component = frappe.db.get_value("Leave Type", self.leave_type, "custom_salary_component")

    if not salary_component:
        return
    
    gross_pay, currency = frappe.db.get_value("Employee", self.employee, ["ctc", "salary_currency"])

    daily_pay = gross_pay / 30

    date_range = {}

    month_last_day = get_last_day(self.from_date)
    next_month_last_date = None
    if month_last_day >= self.to_date:
        date_range.update({month_last_day : [self.from_date, self.to_date]})
    else:
        next_month_start_date = month_last_day + timedelta(days = 1)
        next_month_last_date = get_last_day(self.to_date)
        date_range.update({month_last_day : [self.from_date, month_last_day], next_month_last_date : [next_month_start_date, self.to_date]})

    for row in date_range:
        leave_days = (date_diff(date_range[row][1], date_range[row][0]) + 1 )if date_range[row][1] != date_range[row][0] else 1

        if add_doc_name := frappe.db.get_value("Additional Salary", {"docstatus": 0, "employee": self.employee, "salary_component": salary_component, "payroll_date": row}):
            ads_doc = frappe.get_doc("Additional Salary", add_doc_name)
            ads_doc.amount += flt(leave_days * daily_pay, self.precision)
        else:
            ads_doc = frappe.new_doc("Additional Salary")
            ads_doc.employee = self.employee
            ads_doc.salary_component = salary_component
            ads_doc.currency = currency
            ads_doc.payroll_date = row
            ads_doc.amount = flt(leave_days * daily_pay, self.precision)
        # ads_doc.ref_doctype = "Leave Application"
        # ads_doc.ref_docname = self.name

        ads_doc.save()
    # ads_doc.submit()