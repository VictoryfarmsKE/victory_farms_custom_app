import frappe

def stock_entry(doc, event):
    if doc.docstatus != 0:
        return

    # Only process for Repack Spoilage type
    if doc.stock_entry_type != "Repack Spoilage":
        return

    doc.set("custom_item_summery", [])
    list_items = []
    for d in doc.get("items"):
        if d.s_warehouse:
            list_items.append({
                "item": d.item_code,
                "qty": d.qty
            })
    for d in doc.get("items"):
        if d.t_warehouse:
            wr_list = frappe.db.exists('Warehouse', {
                'warehouse_type': 'Spoilage',
                'name': d.t_warehouse
            })
            if wr_list:
                for item in list_items:
                    doc.append("custom_item_summery", {
                        "item": item["item"],
                        "qty": item["qty"]
                    })
                break 