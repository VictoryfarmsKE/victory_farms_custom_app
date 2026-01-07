import frappe
from frappe import _
from frappe.utils import flt

def after_insert(self, method):
    if not self.custom_create_individual_holiday_list:
        return

    create_holiday_list(self)

def validate(self, method):
    # Validate department details weightage
    if self.custom_department_details:
        remaining_weightage = 100
        length = len(self.custom_department_details)
        for row in self.custom_department_details:
            if not row.weightage:
                row.weightage = remaining_weightage / length
     
            length -= 1
            remaining_weightage -= row.weightage
    
    # Validate group company weights sum to 100% when custom_appraisal_on_group is enabled
    if self.get("custom_appraisal_on_group"):
        group_companies = self.get("custom_group_company_details") or []
        
        if not group_companies:
            frappe.throw(
                _("When 'Appraisal on Group' is enabled, you must define at least one company in 'Group Company Details'.")
            )
        
        total_weight = sum(flt(row.weight) for row in group_companies)
        
        if flt(total_weight, 2) != 100.0:
            frappe.throw(
                _("Group company weights must sum to 100%. Current total: {0}%").format(flt(total_weight, 2))
            )

@frappe.whitelist()
def create_holiday_list(doc):
    if isinstance(doc, str):
        doc = frappe.get_doc("Employee", doc)

    today = frappe.utils.today()

    if template_holiday_list := frappe.db.get_value("Holiday List", {"custom_template_holiday_list": 1, "from_date": ["<=", today], "to_date": [">=", today]}):
        template_doc = frappe.get_doc("Holiday List", template_holiday_list)

        holiday_list_name = f"{doc.name} - {template_doc.name}"

        if frappe.db.exists("Holiday List", holiday_list_name):
            doc.db_set("holiday_list", holiday_list_name)
            return

        emp_holiday_doc = frappe.copy_doc(template_doc)
        emp_holiday_doc.holiday_list_name = holiday_list_name
        emp_holiday_doc.custom_template_holiday_list = 0
        emp_holiday_doc.flags.ignore_permissions = True
        emp_holiday_doc.save()
        doc.db_set("holiday_list", emp_holiday_doc.name)


@frappe.whitelist()
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
    emp_holiday_doc.employee = emp
    emp_holiday_doc.fiscal_year = template_doc.custom_fiscal_year
    emp_holiday_doc.flags.ignore_permissions = True
    emp_holiday_doc.save()
    frappe.db.set_value("Employee", emp, "holiday_list", emp_holiday_doc.name)