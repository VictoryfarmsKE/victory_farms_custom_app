import frappe
from frappe import _
from datetime import datetime

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters) if filters else []
    return columns, data

def get_columns():
    return [
        {
            "label": _("Payroll Number"),
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 200,
        },
        {
            "label": _("First Name"),
            "fieldname": "first_name",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Last Name"),
            "fieldname": "last_name",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Phone"),
            "fieldname": "cell_number",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("National ID"),
            "fieldname": "national_id",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("KRA PIN"),
            "fieldname": "tax_id",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("NHIF No"),
            "fieldname": "shif_no",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Gross Salary"),
            "fieldname": "gross_pay",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Contribution Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 200,
        },
    ]
def get_data(filters):
    months = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }

    emp = frappe.qb.DocType("Employee")
    salary_slip = frappe.qb.DocType("Salary Slip")
    deduction = frappe.qb.DocType("Salary Detail")

    query = (
        frappe.qb.from_(emp)
        .inner_join(salary_slip)
        .on(emp.name == salary_slip.employee)
        .inner_join(deduction)
        .on(salary_slip.name == deduction.parent)
        .select(
            (emp.name.as_("employee")),
            (emp.employee_name),
            (emp.tax_id),
            (emp.first_name),
            (emp.last_name),
            (emp.cell_number),
            (emp.national_id),
            (emp.tax_id),
            (emp.shif_no),
            (salary_slip.gross_pay),
            (deduction.amount),
            (deduction.name)
        )
        .where(deduction.salary_component == "Social Health Insurance Fund")
    )

    if filters.get("employee"):
        query = query.where(emp.name == filters["employee"])

    start_date = datetime(
        int(filters.get("year")), months.get(filters.get("month")), 1
    ).date()
    end_date = frappe.utils.get_last_day(start_date)

    query = query.where(salary_slip.start_date == start_date)
    query = query.where(salary_slip.end_date == end_date)

    data = query.run(as_dict=True)

    return data
