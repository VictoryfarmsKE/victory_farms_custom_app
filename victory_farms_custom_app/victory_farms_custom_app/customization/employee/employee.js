frappe.ui.form.on("Employee", {
    refresh: function (frm) {
        if (frm.doc.custom_create_individual_holiday_list && !frm.doc.holiday_list) {
            frm.add_custom_button(
                __("Create Holiday List"),
                function () {
                    frappe.call({
                        method: "victory_farms_custom_app.victory_farms_custom_app.customization.employee.employee.create_holiday_list",
                        args: {
                            doc: frm.doc.name
                        },
                        freeze: true,
                        freeze_message: __("Creating Holiday List"),
                        callback: function () {
                            frappe.msgprint(__("Holiday List is created for Employee"))
                            frm.reload_doc()
                        },
                    });
                },
            );
        }
    }
})