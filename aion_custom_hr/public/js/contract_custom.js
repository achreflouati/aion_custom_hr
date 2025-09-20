frappe.ui.form.on("Contract", {
    refresh: function(frm) {
        // Vérifier si la checkbox est cochée et afficher le bouton
        if (frm.doc.requires_fuel_coupons == 1 && !frm.is_new()) {
            frm.add_custom_button(__('Create Fuel Coupon'), function() {
                create_fuel_management_from_contract(frm);
            }, __('Fuel Management'));
        }
        
        // Bouton pour voir les Fuel Management existants
        if (frm.doc.requires_fuel_coupons == 1 && !frm.is_new()) {
            frm.add_custom_button(__('View Fuel Records'), function() {
                view_existing_fuel_management(frm);
            }, __('Fuel Management'));
        }
    },

    custom_does_job_require_fuel_coupons: function(frm) {
        // Rafraîchir pour montrer/cacher les boutons quand la checkbox change
        frm.refresh();
    },
    
    employee: function(frm) {
        // Rafraîchir pour montrer/cacher les boutons quand l'employé change
        if (frm.doc.requires_fuel_coupons == 1) {
            frm.refresh();
        }
    }
});

function create_fuel_management_from_contract(frm) {
    // Créer un nouveau Fuel Management avec les infos du contrat
    frappe.new_doc("Fuel Management", {
        "employee": frm.doc.party_name,
        "contract": frm.doc.name,
        "department": frm.doc.department,
        "designation": frm.doc.designation,
        "year": new Date().getFullYear(),
        "month": get_current_month(),
        "status": "Draft"
    });
}

function view_existing_fuel_management(frm) {
    // Voir les Fuel Management existants pour ce contrat
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Fuel Management",
            filters: {"contract": frm.doc.name},
            fields: ["name", "month", "year", "total_value", "status"],
            order_by: "creation desc"
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                // Ouvrir le dernier Fuel Management
                frappe.set_route('Form', 'Fuel Management', r.message[0].name);
            } else {
                frappe.msgprint(__('No Fuel Management records found for this contract.'));
            }
        }
    });
}

function get_current_month() {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December'];
    return months[new Date().getMonth()];
}