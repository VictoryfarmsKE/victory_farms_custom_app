# import frappe
# from frappe import _
# from frappe.utils import date_diff, get_last_day
# from frappe.model.document import Document
# from frappe import _


# def check_last_date(self, *args, **kwargs): 
#     add_salary = frappe.get_doc("Additional Salary", self.name)
#     salary_compo = frappe.db.get_value("Salary Component", add_salary.salary_component, "is_for_store_deduction")

#     if salary_compo == True:
#         get_last_day(frappe.utils.nowdate())
#         frappe.throw(_(f"Additional Salary Only be Submitted on Last day of the Month"))

