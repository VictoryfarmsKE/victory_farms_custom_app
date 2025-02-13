frappe.ui.form.on("Leave Type", {
    refresh: function(frm){
        frm.add_custom_button(__("Create Leave Allocation"), function () {
            frappe.call({
                method: "victory_farms_custom_app.victory_farms_custom_app.customization.leave_type.leave_type.create_leave_allocation",
                args: { leave_type: frm.doc.name, is_earned_leave: frm.doc.is_earned_leave},
                freeze: true,
                freeze_message: __("Creating Leave Allocations"),
                callback: function () {
                    frappe.msgprint(__("Leave Allocation has been generated."));
                },
            });
        });
    }
})