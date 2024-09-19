frappe.ui.form.on('Stock Entry Detail', {
	custom_get_weights_: function (frm, cnd, cdt) {
		$.ajax({
			type: 'POST',
			url: "http:localhost:5000/get_weight_scale",
			data: {},
			success: function (data, status, xhr) {
				if (data.error == '') {
					$.each(frm.doc.items || [], function (i, v) {
						if (cdt == v.name) {
							frappe.model.set_value(v.doctype, v.name, "qty", data.data)
						}

					})
				}

			},
			error: function (xhr, status, error) {
				console.error(xhr);
				console.error(status);
				console.error(error);
			}
		});
	}
})
