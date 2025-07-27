frappe.ui.form.on('Attendance', {
    refresh: function(frm) {
        // Optionally, you can add logic to show/hide or style the status field
    },
    total_late_minutes: function(frm) {
        update_status(frm);
    },
    total_early_exit_minutes: function(frm) {
        update_status(frm);
    }
});

function update_status(frm) {
    if ((frm.doc.total_late_minutes > 0 || frm.doc.total_early_exit_minutes > 0) && frm.doc.status !== 'Assume as Absent') {
        frm.set_value('status', 'Assume as Absent');
        frappe.show_alert(__('Status set to Assume as Absent due to lateness or early exit.'));
    }
}
