# Copyright (c) 2025, ard and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class itembarecodetest(Document):
    def validate(self):
        if self.barcode and not self.item_code:
            self.fetch_item_info()
    
    def fetch_item_info(self):
        """Fetch item information when barcode is entered"""
        if not self.barcode:
            return
        
        result = fetch_item_by_barcode(self.barcode)
        if result.get("success"):
            data = result.get("data")
            self.item_code = data.get("item_code")
            self.item_name = data.get("item_name")
            self.item_group = data.get("item_group")
            self.standard_rate = data.get("standard_rate", 0)
            self.last_scan_time = now()
            
            # Clear existing warehouse stock
            self.warehouse_stock_table = []
            
            # Add warehouse stock
            for stock in data.get("warehouse_stock", []):
                self.append("warehouse_stock_table", {
                    "warehouse": stock.get("warehouse"),
                    "warehouse_name": stock.get("warehouse_name"),
                    "actual_qty": stock.get("actual_qty", 0),
                    "reserved_qty": stock.get("reserved_qty", 0),
                    "projected_qty": stock.get("projected_qty", 0),
                    "available_qty": stock.get("available_qty", 0)
                })


@frappe.whitelist()
def fetch_item_by_barcode(barcode):
    """Fetch item information by barcode"""
    if not barcode:
        return {"success": False, "message": "Barcode is required"}
    
    try:
        # Search for item by barcode in Item Barcode table
        item_code = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")
        
        if not item_code:
            # If not found in Item Barcode, search in Item table directly
            item_code = frappe.db.get_value("Item", {"item_code": barcode}, "name")
        
        if not item_code:
            # Try searching by name or other fields
            item_code = frappe.db.get_value("Item", {"name": barcode}, "name")
        
        if not item_code:
            return {"success": False, "message": "Item not found for this barcode"}
        
        # Get item details
        item_doc = frappe.get_doc("Item", item_code)
        
        # Get warehouse stock with warehouse names
        warehouse_stock = frappe.db.sql("""
            SELECT 
                b.warehouse,
                w.warehouse_name,
                b.actual_qty,
                b.reserved_qty,
                b.projected_qty,
                (b.actual_qty - IFNULL(b.reserved_qty, 0)) as available_qty
            FROM `tabBin` b
            LEFT JOIN `tabWarehouse` w ON b.warehouse = w.name
            WHERE b.item_code = %s
            AND (b.actual_qty != 0 OR b.projected_qty != 0)
            ORDER BY b.warehouse
        """, (item_code,), as_dict=True)
        
        return {
            "success": True,
            "data": {
                "item_code": item_doc.item_code,
                "item_name": item_doc.item_name,
                "item_group": item_doc.item_group,
                "standard_rate": item_doc.standard_rate or 0,
                "warehouse_stock": warehouse_stock
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching item by barcode: {str(e)}")
        return {"success": False, "message": str(e)}
