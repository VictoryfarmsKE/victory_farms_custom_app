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
            "label": _("Employee"),
            "fieldname": "employee",
            "fieldtype": "link",
            "options": "Employee",
            "width": 250,
        },
        {
            "label": _("Member Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": _("Member Number (ID NUMBER)"),
            "fieldname": "national_id",
            "fieldtype": "Data",
            "options": "Employee",
            "width": 250,
        },
        {
            "label": _("KRA PIN"),
            "fieldname": "tax_id",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": _("Gross Salary"),
            "fieldname": "gross_pay",
            "fieldtype": "Currency",
            "width": 250,
        }
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
    
    query = (
        frappe.qb.from_(emp)
        .inner_join(salary_slip)
        .on(emp.name == salary_slip.employee)
        .select(
            emp.name.as_("employee"),
            emp.employee_name,
            emp.national_id,
            emp.tax_id,
            salary_slip.gross_pay,
            salary_slip.name.as_("salary_slip_name")
        )
        .where(salary_slip.docstatus == 1)
    )

    if filters.get("employee"):
        query = query.where(emp.name == filters["employee"])

    start_date = datetime(int(filters.get("year")), months.get(filters.get("month")), 1).date()
    end_date = frappe.utils.get_last_day(start_date)

    query = query.where(salary_slip.start_date >= start_date)
    query = query.where(salary_slip.end_date <= end_date)
    
    data = query.run(as_dict=True)

    # List of bonus components to fetch
    bonus_components = {
        "bonus_individual_quarterly": "Bonus Individual (Quarterly)",
        "bonus_department_quarterly": "Bonus Department (Quarterly)",
        "bonus_company_annual": "Bonus Company (Annual)",
        "bonus_individual_annual": "Bonus Individual (Annual)",
        "bonus_department_annual": "Bonus Department (Annual)",
    }

    for row in data:
        total_bonus = 0.0
        for field, component in bonus_components.items():
            bonus = frappe.db.get_value(
                "Salary Detail",
                {
                    "parent": row["salary_slip_name"],
                    "parenttype": "Salary Slip",
                    "salary_component": component
                },
                "amount"
            )
            row[field] = bonus or 0.0
            total_bonus += row[field]
        # Subtract total bonuses from gross_pay
        row["gross_pay"] = (row["gross_pay"] or 0.0) - total_bonus
        row.pop("salary_slip_name", None)

    return data