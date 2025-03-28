// Copyright (c) 2025, Solufy and contributors
// For license information, please see license.txt

frappe.ui.form.on("Annual Appraisal", {
    refresh(frm) {
        frm.add_custom_button(
            __("Get Data"),
            function () {
                frm.call({
                    doc: frm.doc,
                    method: "get_department_data",
                    callback: function (r) {
                        if (r.message) {
                            row.unit_price = r.message
                            frm.refresh_fields("items")
                        }
                    },
                });
            },
        );
    },
});


// frappe.ui.form.on("Quarterly Department Details", {
//     pass
// });