import frappe

def after_insert(self, method):
    if not self.custom_create_individual_holiday_list:
        return

    create_holiday_list(self)

def create_holiday_list(self):
    today = frappe.utils.today()
    if template_holiday_list := frappe.db.get_value("Holiday List", {"custom_template_holiday_list": 1, "from_date": ["<=", today], "to_date": [">=", today]}):
        template_doc = frappe.get_doc("Holiday List", template_holiday_list)
        emp_holiday_doc = frappe.copy_doc(template_doc)
        emp_holiday_doc.holiday_list_name = f"{self.name} - {template_doc.name}"
        emp_holiday_doc.custom_template_holiday_list = 0
        emp_holiday_doc.flags.ignore_permissions = True
        emp_holiday_doc.save()
        self.db_set("holiday_list", emp_holiday_doc.name)


def create_holiday_list_for_new_year():
    today = frappe.utils.today()
    if template_holiday_list := frappe.db.get_value("Holiday List", {"custom_template_holiday_list": 1, "from_date": ["<=", today], "to_date": [">=", today]}):
        employee_list = frappe.db.get_all("Employee", {"custom_create_individual_holiday_list": 1, "status": "Active"}, pluck = "name")
        template_doc = frappe.get_doc("Holiday List", template_holiday_list)
        for emp in employee_list:
            frappe.enqueue(duplicate_holiday_list, queue="default", job_name = f"Creating Holiday list for {emp}", template_doc = template_doc, emp = emp)

def duplicate_holiday_list(template_doc, emp):
    holiday_list_name = f"{emp} - {template_doc.name}"
    if frappe.db.exists("Holiday List", holiday_list_name):
        return

    emp_holiday_doc = frappe.copy_doc(template_doc)
    emp_holiday_doc.holiday_list_name = holiday_list_name
    emp_holiday_doc.custom_template_holiday_list = 0
    emp_holiday_doc.flags.ignore_permissions = True
    emp_holiday_doc.save()
    frappe.db.set_value("Employee", emp, "holiday_list", emp_holiday_doc.name)