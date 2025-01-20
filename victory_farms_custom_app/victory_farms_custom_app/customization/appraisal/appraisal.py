import frappe
from frappe.utils import flt
from frappe import _

def before_validate(self, method):
    for row in self.goals:
        if isinstance(row.score, float) and (row.score != round(row.score)):
            frappe.throw(_("Row {0}: Round Precision are only allowed in Goals Score").format(row.idx))