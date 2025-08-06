frappe.ui.form.on("Leave Application", {
  status: async function (frm) {
    if (frm.doc.status !== "Approved") return;

    const { message } = await frappe.call({
      method: "victory_farms_custom_app.victory_farms_custom_app.customization.leave_application.utils.leave_application.check_probation_and_restriction",
      args: {
        employee: frm.doc.employee,
        leave_type: frm.doc.leave_type,
        from_date: frm.doc.from_date,
      },
    });

    if (message && message.show_dialog) {
      const confirm = await new Promise((resolve) => {
        frappe.confirm(
          __("This employee is under probation and not allowed to take leave. Do you still want to approve?"),
          () => resolve(true),
          () => resolve(false)
        );
      });

      if (confirm) {
        frm.save()
        frappe.show_alert({ message: __("Leave Status is set to Approved"), indicator: 'green' });
      } else {
        frm.set_value("status", "Open");
        frm.save()
        frappe.show_alert({ message: __("Leave status reset to Open"), indicator: 'orange' });
      }
    }
  }
});

