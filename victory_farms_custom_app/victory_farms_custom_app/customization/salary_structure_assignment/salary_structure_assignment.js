console.log("called")
frappe.ui.form.on("Salary Structure Assignment", {
    custom_foreign_base: function(frm){
        if (frm.doc.custom_exchange_rate && frm.doc.custom_foreign_base){
            frappe.model.set_value(frm.doc.doctype, frm.doc.name, "base", frm.doc.custom_foreign_base * frm.doc.custom_exchange_rate)
        }
    },
    custom_exchange_rate: function(frm){
        if (frm.doc.custom_exchange_rate && frm.doc.custom_foreign_base){
            frappe.model.set_value(frm.doc.doctype, frm.doc.name, "base", frm.doc.custom_foreign_base * frm.doc.custom_exchange_rate)
        }
    }
})