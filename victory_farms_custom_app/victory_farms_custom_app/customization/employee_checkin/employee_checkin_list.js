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
                        "nl_attendance_timesheet.nl_attendance_timesheet.customization.attendance.attendance.create_additional_salary",
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