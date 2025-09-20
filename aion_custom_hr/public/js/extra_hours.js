frappe.ui.form.on('Extra Hours', {
    refresh: function(frm) {
        // Ajouter le bouton "Load Attendances" si le document est nouveau
        if (true) {
            frm.add_custom_button(__('Load Attendances'), function() {
                load_attendances_for_extra_hours(frm);
            }, __('Actions'));
        }
        
        // Ajouter le bouton "Approve" si le statut est en attente
        if (frm.doc.approval_status === 'Pending Approval') {
            frm.add_custom_button(__('Approve'), function() {
                approve_extra_hours_record(frm, 'Approved');
            }, __('Actions'));
            
            frm.add_custom_button(__('Reject'), function() {
                approve_extra_hours_record(frm, 'Rejected');
            }, __('Actions'));
        }
        
        // Ajouter le bouton "Submit for Approval" si le statut est Draft
        if (frm.doc.approval_status === 'Draft') {
            frm.add_custom_button(__('Submit for Approval'), function() {
                submit_for_approval(frm);
            }, __('Actions'));
        }
        
        // Ajouter des indicateurs de couleur selon le statut
        if (frm.doc.approval_status) {
            frm.dashboard.add_indicator(__('Status: {0}', [frm.doc.approval_status]), 
                get_status_color(frm.doc.approval_status));
        }
        
        // Afficher les totaux dans le dashboard
        if (frm.doc.total_extra_hours) {
            frm.dashboard.add_indicator(__('Total Extra Hours: {0}', [frm.doc.total_extra_hours]), 'blue');
        }
        if (frm.doc.total_approved_extra_hours) {
            frm.dashboard.add_indicator(__('Approved Extra Hours: {0}', [frm.doc.total_approved_extra_hours]), 'green');
        }
    },
    
    employee: function(frm) {
        // Effacer les données précédentes quand l'employé change
        if (frm.doc.employee) {
            frm.clear_table('extra_hours_details');
            frm.refresh_field('extra_hours_details');
        }
    },
    
    from_date: function(frm) {
        validate_date_range(frm);
    },
    
    to_date: function(frm) {
        validate_date_range(frm);
    }
});

// Event pour la table des détails
frappe.ui.form.on('Extra Hours Detail', {
    approved_extra_hours: function(frm, cdt, cdn) {
        calculate_totals(frm);
    },
    
    status: function(frm, cdt, cdn) {
        calculate_totals(frm);
    },
    
    extra_hours_details_remove: function(frm) {
        calculate_totals(frm);
    }
});

function load_attendances_for_extra_hours(frm) {
    if (!frm.doc.employee || !frm.doc.from_date || !frm.doc.to_date) {
        frappe.msgprint(__('Please select Employee, From Date and To Date first'));
        return;
    }
    
    frappe.show_progress(__('Loading Attendances...'), 50, 100, __('Please wait'));
    
    frappe.call({
        method: 'aion_custom_hr.extra_hours.load_extra_hours_for_period',
        args: {
            employee: frm.doc.employee,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date
        },
        callback: function(r) {
            frappe.hide_progress();
            
            if (r.message) {
                // Effacer les données existantes
                frm.clear_table('extra_hours_details');
                
                // Ajouter les nouvelles données
                r.message.forEach(function(detail) {
                    let row = frm.add_child('extra_hours_details');
                    row.attendance_date = detail.attendance_date;
                    row.attendance_name = detail.attendance_name;
                    row.shift_type = detail.shift_type;
                    row.check_in = detail.check_in;
                    row.check_out = detail.check_out;
                    row.worked_hours = detail.worked_hours;
                    row.standard_hours = detail.standard_hours;
                    row.extra_hours = detail.extra_hours;
                    row.approved_extra_hours = detail.approved_extra_hours;
                    row.status = detail.status;
                    row.comments = detail.comments;
                });
                
                frm.refresh_field('extra_hours_details');
                calculate_totals(frm);
                
                frappe.msgprint(__('Attendances loaded successfully. {0} records found.', 
                    [r.message.length]));
            } else {
                frappe.msgprint(__('No attendances found for the selected period'));
            }
        },
        error: function(r) {
            frappe.hide_progress();
            frappe.msgprint(__('Error loading attendances: {0}', [r.message]));
        }
    });
}

function submit_for_approval(frm) {
    if (!frm.doc.extra_hours_details || frm.doc.extra_hours_details.length === 0) {
        frappe.msgprint(__('Please load attendances first'));
        return;
    }
    
    frappe.confirm(
        __('Are you sure you want to submit this Extra Hours record for approval?'),
        function() {
            frm.set_value('approval_status', 'Pending Approval');
            frm.save();
        }
    );
}

function approve_extra_hours_record(frm, status) {
    let title = status === 'Approved' ? __('Approve Extra Hours') : __('Reject Extra Hours');
    
    frappe.prompt([
        {
            fieldname: 'comments',
            fieldtype: 'Text',
            label: __('Comments'),
            reqd: status === 'Rejected'
        }
    ], function(data) {
        frappe.call({
            method: 'aion_custom_hr.extra_hours.approve_extra_hours',
            args: {
                extra_hours_name: frm.doc.name,
                approval_status: status,
                approval_comments: data.comments || ''
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.msgprint(__(r.message.message));
                    frm.reload_doc();
                } else {
                    frappe.msgprint(__('Error: {0}', [r.message.message]));
                }
            }
        });
    }, title);
}

function calculate_totals(frm) {
    let total_worked_hours = 0;
    let total_standard_hours = 0;
    let total_extra_hours = 0;
    let total_approved_extra_hours = 0;
    
    frm.doc.extra_hours_details.forEach(function(detail) {
        total_worked_hours += detail.worked_hours || 0;
        total_standard_hours += detail.standard_hours || 0;
        total_extra_hours += detail.extra_hours || 0;
        
        if (detail.status === 'Approved') {
            total_approved_extra_hours += detail.approved_extra_hours || 0;
        }
    });
    
    frm.set_value('total_worked_hours', Math.round(total_worked_hours * 100) / 100);
    frm.set_value('total_standard_hours', Math.round(total_standard_hours * 100) / 100);
    frm.set_value('total_extra_hours', Math.round(total_extra_hours * 100) / 100);
    frm.set_value('total_approved_extra_hours', Math.round(total_approved_extra_hours * 100) / 100);
}

function validate_date_range(frm) {
    if (frm.doc.from_date && frm.doc.to_date) {
        if (frm.doc.from_date > frm.doc.to_date) {
            frappe.msgprint(__('From Date cannot be greater than To Date'));
            frm.set_value('to_date', '');
        }
    }
}

function get_status_color(status) {
    switch(status) {
        case 'Draft':
            return 'grey';
        case 'Pending Approval':
            return 'orange';
        case 'Approved':
            return 'green';
        case 'Rejected':
            return 'red';
        default:
            return 'blue';
    }
}
