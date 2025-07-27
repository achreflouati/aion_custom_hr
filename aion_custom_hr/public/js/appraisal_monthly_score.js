frappe.ui.form.on('Appraisal', {
    refresh: function(frm) {
        // console.log('Appraisal form refreshed');
        frappe.call({
            method: 'aion_custom_hr.api.update_monthly_appraisal_score_handler.update_monthly_appraisal_score_handler',
            args: { doc: frm.doc },
            callback: function() {
                // frappe.msgprint('Le score mensuel a été mis à jour (refresh).');
            }
        });
    },
    final_score: function(frm) {
        // console.log('final_score changed:', frm.doc.final_score);
        frappe.call({
            method: 'aion_custom_hr.api.update_monthly_appraisal_score_handler.update_monthly_appraisal_score_handler',
            args: { doc: frm.doc },
            callback: function() {
                // frappe.msgprint('Le score mensuel a été mis à jour.');
            }
        });
    },
    total_score: function(frm) {
        // console.log('total_score changed:', frm.doc.total_score);
        frappe.call({
            method: 'aion_custom_hr.api.update_monthly_appraisal_score_handler.update_monthly_appraisal_score_handler',
            args: { doc: frm.doc },
            callback: function() {
                // frappe.msgprint('Le score mensuel a été mis à jour.');
            }
        });
    }
});
