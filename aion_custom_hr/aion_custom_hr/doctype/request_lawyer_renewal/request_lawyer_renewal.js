frappe.ui.form.on("Request Lawyer Renewal", {
    refresh: function(frm) {
        // زرار Send to Lawyer يظهر كان بعد Save و status Draft
        if (!frm.is_new() && frm.doc.status === "Draft") {
            frm.add_custom_button(__('Send to Lawyer'), function() {
                frm.email_doc();
                frm.set_value('status', 'Sent to Lawyer');
                frm.save();  // هنا Save آمن
            });
        }
        if (!frm.is_new() && frm.doc.status === "Completed") {
    frm.add_custom_button(__('Create Company Document'), function() {
        frappe.new_doc("Company Document", {
            "document_company_type": frm.doc.company_document,
            "attachement": frm.doc.final_document
        });
    });
}

        // تحديث checkbox حسب child table (على الفورم فقط)
        update_fulfilment_status(frm);

        // فلترة ديناميكية للـ Links المتعلقة بالمورد
        set_dynamic_supplier_filters(frm);
    },

    fulfilment_checklist_add: function(frm, cdt, cdn) {
        // وقت يضيف سطر جديد في الـ child → يتعمر filing_date
        let row = locals[cdt][cdn];
        row.filing_date = frappe.datetime.now_datetime();
        frm.refresh_field("fulfilment_checklist");
        update_fulfilment_status(frm);
    },

    fulfilment_checklist_remove: function(frm, cdt, cdn) {
        update_fulfilment_status(frm);
    },

    fulfilment_checklist_on_form_rendered: function(frm, cdt, cdn) {
        // وقت يتعمل render للسطر → نراقبو attach
        frappe.ui.form.on("Renewal Fulfilment Checklist", {
            attach: function(childfrm, cdt, cdn) {
                let row = locals[cdt][cdn];
                if (row.attach) {
                    row.filing_date = frappe.datetime.now_datetime();
                    frm.refresh_field("fulfilment_checklist");
                }
            }
        });
    }
});

// دالة مساعدة لتحديث checkbox
function update_fulfilment_status(frm) {
    if (frm.doc.fulfilment_checklist && frm.doc.fulfilment_checklist.length > 0) {
        frm.set_value("fulfilment_status", 1);
        frm.save();  // حفظ التغيير
    } else {
        frm.set_value("fulfilment_status", 0);
    }
    frm.refresh_field("fulfilment_status");
}

// دالة مساعدة لتطبيق فلترة ديناميكية حسب المورد
function set_dynamic_supplier_filters(frm) {
    const link_fields = ['purchase_invoice', 'purchase_order', 'supplier_quotation'];
    
    link_fields.forEach(field => {
        frm.set_query(field, function() {
            return {
                filters: {
                    supplier: frm.doc.supplier
                }
            };
        });
    });
}
