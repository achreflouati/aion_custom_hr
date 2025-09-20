frappe.ui.form.on("Fuel Management", {
    refresh: function(frm) {
        calculate_total(frm);
        
        if (!frm.is_new()) {
            frm.add_custom_button(__('Add Multiple'), function() {
                add_multiple_coupons(frm);
            });
        }
    },

    fuel_coupons_add: function(frm, cdt, cdn) {
        calculate_total(frm);
    },

    fuel_coupons_remove: function(frm, cdt, cdn) {
        calculate_total(frm);
    }
});

function calculate_total(frm) {
    let total = 0;
    if (frm.doc.fuel_coupons) {
        frm.doc.fuel_coupons.forEach(coupon => {
            total += flt(coupon.coupon_value);
        });
    }
    frm.set_value('total_value', total);
}

function add_multiple_coupons(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('Add Multiple Coupons'),
        fields: [
            {
                fieldname: 'number_of_coupons',
                label: __('How many coupons?'),
                fieldtype: 'Int',
                default: 1,
                reqd: 1
            },
            {
                fieldname: 'coupon_value',
                label: __('Value per coupon'),
                fieldtype: 'Currency',
                reqd: 1
            }
        ],
        primary_action: function(values) {
            add_coupons_bulk(frm, values);
            dialog.hide();
        }
    });

    dialog.show();
}

function add_coupons_bulk(frm, values) {
    const today = frappe.datetime.get_today();
    
    for (let i = 0; i < values.number_of_coupons; i++) {
        let child = frm.add_child('fuel_coupons');
        child.coupon_date = today;
        child.coupon_value = values.coupon_value;
    }
    
    frm.refresh_field('fuel_coupons');
    calculate_total(frm);
}