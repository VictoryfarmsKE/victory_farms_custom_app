frappe.ui.form.on('Stock Entry Detail', {
	custom_get_weights_: function(frm, cnd, cdt) {
           $.ajax({
	type: 'POST',
	url: "http:localhost:5000/get_weight_scale",
	data: {},
	success: function (data, status, xhr) {
		console.log("/////////////", data)

                if (data.error == ''){
		$.each(frm.doc.items || [], function(i, v) {
			console.log("//////////////////", cdt, v.name)
			if (cdt == v.name){
			   frappe.model.set_value(v.doctype, v.name, "qty", data.data)
			}

		})}

	},
	error: function (xhr, status, error) {
		console.log(xhr);
		console.log(status);
		console.log(error);
	}
});
	}
})
