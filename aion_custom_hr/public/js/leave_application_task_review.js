frappe.ui.form.on('Leave Application', {
    employee: function(frm) {
        if (frm.doc.employee) {
            load_employee_tasks(frm);
        } else {
            frm.clear_table('employee_tasks');
            frm.refresh_field('employee_tasks');
        }
    },
    
    refresh: function(frm) {
        // Charger les tâches si l'employé est sélectionné mais pas de tâches
        if (frm.doc.employee && (!frm.doc.employee_tasks || frm.doc.employee_tasks.length === 0)) {
            load_employee_tasks(frm);
        }
        
        // Ajouter bouton de rechargement
        if (frm.doc.employee && frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Reload Tasks'), function() {
                reload_employee_tasks(frm);
            }, __('Actions'));
        }
        
        // Afficher le résumé des tâches
        update_tasks_summary(frm);
        
        // Colorer les lignes selon les décisions
        color_task_rows(frm);
    },
    
    before_save: function(frm) {
        // Vérifier les décisions avant sauvegarde
        check_task_decisions(frm);
    }
});

frappe.ui.form.on('Task hr view', {
    approved_: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        // Alerte de changement
        let color = row.approved_ === 'approved' ? 'green' : 
                   row.approved_ === 'rejected' ? 'red' : 'orange';
        
        frappe.show_alert({
            message: `Task "${row.subject_of_task}" marked as ${row.approved_}`,
            indicator: color
        });
        
        // Mettre à jour le résumé
        setTimeout(() => {
            update_tasks_summary(frm);
            color_task_rows(frm);
        }, 100);
        
        // Mettre à jour automatiquement le statut de la demande
        update_leave_status_from_tasks(frm);
    }
});

function load_employee_tasks(frm) {
    if (!frm.doc.employee) return;
    
    frappe.show_alert(__('Loading employee tasks...'));
    
    frappe.call({
        method: 'aion_custom_hr.api.task_hr_manager.get_employee_tasks',
        args: {
            employee: frm.doc.employee
        },
        callback: function(r) {
            console.log('API Response:', r);
            if (r.message && r.message.length > 0) {
                console.log('Tasks found:', r.message);
                
                // Vider le table actuel
                frm.clear_table('employee_tasks');
                
                // Ajouter chaque tâche
                r.message.forEach(function(task, index) {
                    console.log(`Adding task ${index + 1}:`, task);
                    
                    let child = frm.add_child('employee_tasks');
                    console.log('Child created:', child);
                    
                    // Remplir les champs obligatoires en premier
                    child.task_manger_hr = task.name || '';
                    child.approved_ = 'pending';
                    
                    // Puis les autres champs
                    child.subject_of_task = task.subject || 'No Subject';
                    child.status = task.status || 'Open';
                    child.progress = task.progress ? task.progress.toString() : '0';
                    child.employee = task.employee || frm.doc.employee;
                    child.department = task.department || '';
                    child.work_assignment_approver = task.work_assignment_approver || '';
                    
                    console.log('Child filled:', child);
                });
                
                // Rafraîchir le champ
                frm.refresh_field('employee_tasks');
                console.log('Field refreshed, current table:', frm.doc.employee_tasks);
                
                frappe.show_alert({
                    message: `Loaded ${r.message.length} tasks for review`,
                    indicator: 'green'
                });
                
                // Vérifier si les données sont bien là
                setTimeout(() => {
                    console.log('Final table state:', frm.doc.employee_tasks);
                    update_tasks_summary(frm);
                }, 500);
                
            } else {
                console.log('No tasks found');
                frappe.show_alert({
                    message: 'No active tasks found for this employee',
                    indicator: 'blue'
                });
            }
        },
        error: function(r) {
            console.error('Error loading tasks:', r);
            frappe.msgprint(__('Error loading tasks: ' + (r.message || 'Unknown error')));
        }
    });
}

function reload_employee_tasks(frm) {
    frappe.call({
        method: 'aion_custom_hr.api.task_hr_manager.reload_employee_tasks',
        args: {
            leave_application: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frm.reload_doc();
                frappe.show_alert({
                    message: 'Tasks reloaded successfully',
                    indicator: 'green'
                });
            }
        }
    });
}

function update_tasks_summary(frm) {
    if (!frm.doc.employee_tasks || frm.doc.employee_tasks.length === 0) {
        return;
    }
    
    let approved = 0;
    let rejected = 0;
    let pending = 0;
    let total = frm.doc.employee_tasks.length;
    
    frm.doc.employee_tasks.forEach(function(task) {
        switch(task.approved_) {
            case 'approved':
                approved++;
                break;
            case 'rejected':
                rejected++;
                break;
            default:
                pending++;
        }
    });
    
    let summary_html = `
        <div class="row">
            <div class="col-sm-3">
                <div class="badge badge-success">${approved} Approved</div>
            </div>
            <div class="col-sm-3">
                <div class="badge badge-danger">${rejected} Rejected</div>
            </div>
            <div class="col-sm-3">
                <div class="badge badge-warning">${pending} Pending</div>
            </div>
            <div class="col-sm-3">
                <div class="badge badge-info">${total} Total</div>
            </div>
        </div>
    `;
    
    frm.set_df_property('tasks_summary', 'options', summary_html);
    frm.refresh_field('tasks_summary');
}

function color_task_rows(frm) {
    if (!frm.doc.employee_tasks) return;
    
    setTimeout(function() {
        frm.doc.employee_tasks.forEach(function(task, index) {
            let row_selector = `[data-idx="${index + 1}"]`;
            let row = frm.fields_dict.employee_tasks.grid.wrapper.find(row_selector);
            
            if (row.length > 0) {
                row.removeClass('task-approved task-rejected task-pending');
                
                switch(task.approved_) {
                    case 'approved':
                        row.addClass('task-approved');
                        break;
                    case 'rejected':
                        row.addClass('task-rejected');
                        break;
                    default:
                        row.addClass('task-pending');
                }
            }
        });
    }, 300);
}

function update_leave_status_from_tasks(frm) {
    if (!frm.doc.employee_tasks || frm.doc.employee_tasks.length === 0) return;
    
    let approved = 0;
    let rejected = 0;
    let total = frm.doc.employee_tasks.length;
    
    frm.doc.employee_tasks.forEach(function(task) {
        if (task.approved_ === 'approved') approved++;
        if (task.approved_ === 'rejected') rejected++;
    });
    
    let status_message = '';
    let alert_color = 'blue';
    
    if (rejected > 0) {
        status_message = `⚠️ Leave will be REJECTED (${rejected} task(s) rejected)`;
        alert_color = 'red';
        frm.dashboard.set_headline_alert(status_message, 'red');
    } else if (approved === total) {
        status_message = `✅ Leave will be APPROVED (All ${approved} tasks approved)`;
        alert_color = 'green';
        frm.dashboard.set_headline_alert(status_message, 'green');
    } else {
        status_message = `⏳ Review in progress (${approved}/${total} approved)`;
        alert_color = 'orange';
        frm.dashboard.set_headline_alert(status_message, 'orange');
    }
    
    frappe.show_alert({
        message: status_message,
        indicator: alert_color
    });
}

function check_task_decisions(frm) {
    if (!frm.doc.employee_tasks || frm.doc.employee_tasks.length === 0) return;
    
    let has_decisions = false;
    let decisions_summary = {};
    
    frm.doc.employee_tasks.forEach(function(task) {
        if (task.approved_ && task.approved_ !== 'pending') {
            has_decisions = true;
            decisions_summary[task.approved_] = (decisions_summary[task.approved_] || 0) + 1;
        }
    });
    
    if (has_decisions) {
        let message = 'Task decisions: ';
        Object.keys(decisions_summary).forEach(function(decision) {
            message += `${decisions_summary[decision]} ${decision}, `;
        });
        
        frappe.msgprint({
            title: 'Task Review Summary',
            message: message.slice(0, -2),
            indicator: 'blue'
        });
    }
}

// CSS pour colorer les lignes
$(document).ready(function() {
    if (!$('#task-review-styles').length) {
        let style = `
            <style id="task-review-styles">
                .task-approved { background-color: #e8f5e8 !important; }
                .task-rejected { background-color: #fdeaea !important; }
                .task-pending { background-color: #fff3cd !important; }
            </style>
        `;
        $('head').append(style);
    }
});
