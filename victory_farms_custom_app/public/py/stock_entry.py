import frappe


def stock_entry(doc,event):
	if doc.docstatus == 0:
		lsit = []
		if doc.stock_entry_type == "Repack Spoilage":
			doc.set("custom_item_summery", [])
			for d in doc.get("items"):
				if d.s_warehouse:
					lsit.append({"item": d.item_code,
									"qty": d.qty
								})
		for d in doc.get("items"):
			wr_list = frappe.db.get_list('Warehouse',filters={'warehouse_type': 'Spoilage','name':d.t_warehouse},fields=['warehouse_type'],as_list=True)
			if wr_list:
				for ls in lsit:
					doc.append(
						"custom_item_summery",
						{
							"item": ls["item"],
							"qty": ls["qty"]
						},
					)