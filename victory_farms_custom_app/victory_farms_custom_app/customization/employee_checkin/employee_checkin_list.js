frappe.listview_settings["Employee Checkin"] = {
    onload: function (list_view) {
		list_view.page.add_inner_button(__("Create Remaining Logs"), function () {
            selected_values = list_view.get_checked_items();
            checkins = []
            selected_values.forEach(element => {
                checkins.push(element.name)
            });
            if (checkins){
                frappe.call({
                    method:
                        "victory_farms_custom_app.victory_farms_custom_app.customization.employee_checkin.employee_checkin.create_missing_values",
                    args: {
                        selected_values: checkins
                    },
                    freeze: true,
                    freeze_message: __("Creatig remaining logs in background"),
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.msgprint(__("Creatig remaining logs in background"))
                        }
                    },
                });
            }
        })
    }
}