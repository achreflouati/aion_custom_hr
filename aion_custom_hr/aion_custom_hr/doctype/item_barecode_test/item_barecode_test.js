// Copyright (c) 2025, ard and contributors
// For license information, please see license.txt

frappe.ui.form.on("item barecode test", {
    refresh(frm) {
        // Auto-focus sur le champ barcode
        setTimeout(() => {
            frm.set_focus('barcode');
        }, 500);
    },
    
    barcode: function(frm) {
        // Auto-fetch dès que le code-barre est modifié
        if (frm.doc.barcode && frm.doc.barcode.length > 2) {
            // Délai court pour éviter les appels multiples pendant la saisie
            if (frm.barcode_timeout) {
                clearTimeout(frm.barcode_timeout);
            }
            
            frm.barcode_timeout = setTimeout(() => {
                frm.trigger('fetch_item_info');
            }, 300);
        } else {
            // Vider les champs si le code-barre est supprimé
            frm.trigger('clear_item_info');
        }
    },
    
    fetch_item_info: function(frm) {
        if (!frm.doc.barcode) return;
        
        frappe.call({
            method: 'aion_custom_hr.aion_custom_hr.doctype.item_barecode_test.item_barecode_test.fetch_item_by_barcode',
            args: {
                barcode: frm.doc.barcode
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    const data = r.message.data;
                    
                    // Remplir les champs item
                    frm.set_value('item_code', data.item_code);
                    frm.set_value('item_name', data.item_name);
                    frm.set_value('item_group', data.item_group);
                    frm.set_value('standard_rate', data.standard_rate);
                    frm.set_value('last_scan_time', frappe.datetime.now_datetime());
                    
                    // Remplir la table stock
                    frm.clear_table('warehouse_stock_table');
                    if (data.warehouse_stock) {
                        data.warehouse_stock.forEach(function(stock) {
                            let row = frm.add_child('warehouse_stock_table');
                            row.warehouse = stock.warehouse;
                            row.warehouse_name = stock.warehouse_name;
                            row.actual_qty = stock.actual_qty;
                            row.reserved_qty = stock.reserved_qty;
                            row.projected_qty = stock.projected_qty;
                            row.available_qty = stock.available_qty;
                        });
                    }
                    frm.refresh_field('warehouse_stock_table');
                    
                    // Afficher notification de succès
                    frappe.show_alert({
                        message: __('Item trouvé: {0}', [data.item_name]),
                        indicator: 'green'
                    });
                    
                } else {
                    // Vider les champs si item non trouvé
                    frm.trigger('clear_item_info');
                    frappe.show_alert({
                        message: __('Aucun item trouvé pour ce code-barre'),
                        indicator: 'orange'
                    });
                }
            },
            error: function() {
                frm.trigger('clear_item_info');
                frappe.show_alert({
                    message: __('Erreur lors de la recherche'),
                    indicator: 'red'
                });
            }
        });
    },
    
    clear_item_info: function(frm) {
        frm.set_value('item_code', '');
        frm.set_value('item_name', '');
        frm.set_value('item_group', '');
        frm.set_value('standard_rate', 0);
        frm.clear_table('warehouse_stock_table');
        frm.refresh_field('warehouse_stock_table');
    }
});

// Support pour validation avec Enter
frappe.ui.form.on('item barecode test', 'barcode', function(frm) {
    if (frm.doc.barcode) {
        // Trigger fetch après une courte pause
        setTimeout(() => {
            frm.trigger('fetch_item_info');
        }, 100);
    }
});
