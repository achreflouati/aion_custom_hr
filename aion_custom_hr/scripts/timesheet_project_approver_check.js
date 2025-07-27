frappe.ui.form.on('Timesheet', {
    project: function(frm) {
        if (frm.doc.project) {
            frappe.call({
                method: 'aion_custom_hr.api.timesheet.check_project_approver',
                args: {
                    project: frm.doc.project,
                    user: frappe.session.user
                },
                callback: function(r) {
                    if (!r.message.is_approver) {
                        frappe.msgprint('Vous n’êtes pas autorisé à approuver ce projet dans ce département.');
                    } else {
                        frappe.msgprint('Projets liés à cet employé : ' + r.message.projects.join(', '));
                    }
                }
            });
        }
    }
});
