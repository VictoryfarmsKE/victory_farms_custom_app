frappe.ui.form.on("Holiday List", {
    refresh: function (frm) {
        if (frm.doc.custom_template_holiday_list) {
            frm.add_custom_button(
                __("Create Holiday List"),
                function () {
                    frappe.call({
                        method: "victory_farms_custom_app.victory_farms_custom_app.customization.employee.employee.create_holiday_list_for_new_year",
                        freeze: true,
                        freeze_message: __("Creating Holiday List"),
                        callback: function () {
                            frappe.msgprint(__("Holiday List creation is in enqueue"))
                        },
                    });
                },
            );
        }
    }
})