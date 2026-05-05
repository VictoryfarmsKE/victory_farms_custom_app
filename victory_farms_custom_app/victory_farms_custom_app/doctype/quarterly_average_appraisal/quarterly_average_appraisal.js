// Copyright (c) 2026, Solufy and contributors
// For license information, please see license.txt

frappe.ui.form.on("Quarterly Average Appraisal", {
    refresh(frm) {
        if (frm.doc && frm.doc.docstatus === 0) {
            frm.add_custom_button(
                __("Get Data"),
                function () {
                    frm.call({
                        doc: frm.doc,
                        method: "get_department_data",
                        callback: function (r) {
                            frm.dirty();
                        },
                    });
                },
            );
        }
    },

    employee(frm) {
        // Fetch bonus potential fields when employee changes
        if (frm.doc.employee) {
            frappe.db.get_value("Employee", frm.doc.employee, 
                ["bonus_potential", "custom_department_bonus_potential_", "custom_companygroup_bonus", "department"],
                function(r) {
                    if (r) {
                        frm.set_value("bonus_potential", r.bonus_potential || 0);
                        frm.set_value("bonus_potential_department", r.custom_department_bonus_potential_ || 0);
                        frm.set_value("department", r.department || "");
                        frm.refresh_fields();
                    }
                }
            );
        } else {
            frm.set_value("bonus_potential", 0);
            frm.set_value("bonus_potential_department", 0);
            frm.set_value("department", "");
            frm.refresh_fields();
        }
    },

    onload(frm) {
        // Fetch latest bonus potential values on form load for existing documents
        if (frm.doc.employee && !frm.is_new()) {
            frappe.db.get_value("Employee", frm.doc.employee, 
                ["bonus_potential", "custom_department_bonus_potential_", "custom_companygroup_bonus"],
                function(r) {
                    if (r) {
                        if (frm.doc.bonus_potential != r.bonus_potential ||
                            frm.doc.bonus_potential_department != r.custom_department_bonus_potential_) {
                            
                            frm.set_value("bonus_potential", r.bonus_potential || 0);
                            frm.set_value("bonus_potential_department", r.custom_department_bonus_potential_ || 0);
                        }
                    }
                }
            );
        }
    }
});