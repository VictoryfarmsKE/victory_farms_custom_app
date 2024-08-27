frappe.ui.form.on("Additional Salary", {
    get_employee_currency: function (frm) {
        frappe.db.get_value('Employee', frm.doc.employee, "salary_currency", function(r) {
            if (r.salary_currency){
                frm.set_value("currency", r.salary_currency);
            }
        });
	},
})