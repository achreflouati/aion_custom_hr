// Auto-calculation for Shift Type Penalty System
// Calcul automatique des pénalités en temps réel

frappe.ui.form.on('Shift Type', {
    // Période 1
    coefficient_penalty_period_1: function(frm) {
        calculate_penalty(frm, 1);
    },
    late_entry_assume_as_absent_1: function(frm) {
        calculate_penalty(frm, 1);
    },
    early_exit_assume_as_absent_1: function(frm) {
        calculate_penalty(frm, 1);
    },
    
    // Période 2
    coefficient_penalty_period_2: function(frm) {
        calculate_penalty(frm, 2);
    },
    late_entry_assume_as_absent_2: function(frm) {
        calculate_penalty(frm, 2);
    },
    early_exit_assume_as_absent_2: function(frm) {
        calculate_penalty(frm, 2);
    },
    
    // Période 3
    coefficient_penalty_period_3: function(frm) {
        calculate_penalty(frm, 3);
    },
    late_entry_assume_as_absent_3: function(frm) {
        calculate_penalty(frm, 3);
    },
    early_exit_assume_as_absent_3: function(frm) {
        calculate_penalty(frm, 3);
    },
    
    // Période 4
    coefficient_penalty_period_4: function(frm) {
        calculate_penalty(frm, 4);
    },
    late_entry_assume_as_absent_4: function(frm) {
        calculate_penalty(frm, 4);
    },
    early_exit_assume_as_absent_4: function(frm) {
        calculate_penalty(frm, 4);
    }
});

// Fonction de calcul unifié pour toutes les périodes
function calculate_penalty(frm, period) {
    let coefficient = frm.doc[`coefficient_penalty_period_${period}`];
    let late_threshold = frm.doc[`late_entry_assume_as_absent_${period}`];
    let early_threshold = frm.doc[`early_exit_assume_as_absent_${period}`];
    
    if (coefficient && (late_threshold || early_threshold)) {
        // Utilise le seuil le plus élevé entre late et early pour le calcul
        let base_threshold = Math.max(late_threshold || 0, early_threshold || 0);
        let penalty = Math.round(base_threshold * coefficient);
        
        // Met à jour le champ penalty automatiquement
        frm.set_value(`penalty_period_${period}`, penalty);
        
        // Affiche un message informatif
        frappe.show_alert({
            message: `Period ${period}: Penalty = ${base_threshold} min × ${coefficient} = ${penalty} min`,
            indicator: 'blue'
        });
    }
}

// Fonction de calcul pour période 1
function calculate_penalty_period_1(frm) {
    let late_entry = frm.doc.late_entry_assume_as_absent_1 || 0;
    let early_exit = frm.doc.early_exit_assume_as_absent_1 || 0;
    let coefficient = frm.doc.coefficient_penalty_period_1 || 0;
    
    if (coefficient > 0) {
        // Utiliser la moyenne entre late_entry et early_exit comme base de calcul
        let base_minutes = Math.max(late_entry, early_exit);
        if (base_minutes > 0) {
            let penalty = Math.round(base_minutes * coefficient);
            frm.set_value('penalty_period_1', penalty);
            frm.refresh_field('penalty_period_1');
        }
    }
}

// Fonction de calcul pour période 2
function calculate_penalty_period_2(frm) {
    let late_entry = frm.doc.late_entry_assume_as_absent_2 || 0;
    let early_exit = frm.doc.early_exit_assume_as_absent_2 || 0;
    let coefficient = frm.doc.coefficient_penalty_period_2 || 0;
    
    if (coefficient > 0) {
        let base_minutes = Math.max(late_entry, early_exit);
        if (base_minutes > 0) {
            let penalty = Math.round(base_minutes * coefficient);
            frm.set_value('penalty_period_2', penalty);
            frm.refresh_field('penalty_period_2');
        }
    }
}

// Fonction de calcul pour période 3
function calculate_penalty_period_3(frm) {
    let late_entry = frm.doc.late_entry_assume_as_absent_3 || 0;
    let early_exit = frm.doc.early_exit_assume_as_absent_3 || 0;
    let coefficient = frm.doc.coefficient_penalty_period_3 || 0;
    
    if (coefficient > 0) {
        let base_minutes = Math.max(late_entry, early_exit);
        if (base_minutes > 0) {
            let penalty = Math.round(base_minutes * coefficient);
            frm.set_value('penalty_period_3', penalty);
            frm.refresh_field('penalty_period_3');
        }
    }
}

// Fonction de calcul pour période 4
function calculate_penalty_period_4(frm) {
    let late_entry = frm.doc.late_entry_assume_as_absent_4 || 0;
    let early_exit = frm.doc.early_exit_assume_as_absent_4 || 0;
    let coefficient = frm.doc.coefficient_penalty_period_4 || 0;
    
    if (coefficient > 0) {
        let base_minutes = Math.max(late_entry, early_exit);
        if (base_minutes > 0) {
            let penalty = Math.round(base_minutes * coefficient);
            frm.set_value('penalty_period_4', penalty);
            frm.refresh_field('penalty_period_4');
        }
    }
}

// Message d'aide pour l'utilisateur
frappe.ui.form.on('Shift Type', {
    refresh: function(frm) {
        if (frm.doc.__islocal || frm.is_new()) {
            frm.dashboard.add_comment(
                __('💡 Astuce: Les pénalités se calculent automatiquement : Pénalité = Max(Late Entry, Early Exit) × Coefficient'),
                'blue', true
            );
        }
    },
    
    // Hook pour intercepter le processus d'attendance automatique
    process_auto_attendance: function(frm) {
        // Délai pour permettre au processus d'attendance de se terminer
        setTimeout(() => {
            check_and_create_penalty_management(frm);
        }, 3000); // 3 secondes de délai
    }
});

// Fonction pour vérifier et créer les entrées Penalty Management
function check_and_create_penalty_management(frm) {
    // Récupérer les nouvelles attendances avec pénalités
    frappe.call({
        method: 'aion_custom_hr.api.penalty_management.check_new_penalties_for_shift',
        args: {
            shift_type: frm.doc.name,
            from_date: frappe.datetime.add_days(frappe.datetime.get_today(), -7), // 7 jours en arrière
            to_date: frappe.datetime.get_today()
        },
        callback: function(r) {
            if (r.message && r.message.has_new_penalties) {
                show_penalty_management_creation_dialog(frm, r.message);
            }
        }
    });
}

// Dialogue pour créer les entrées Penalty Management
function show_penalty_management_creation_dialog(frm, penalty_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('New Penalties Detected'),
        size: 'large',
        fields: [
            {
                label: __('Penalty Summary'),
                fieldtype: 'HTML',
                fieldname: 'penalty_summary'
            },
            {
                fieldtype: 'Section Break'
            },
            {
                label: __('Create Penalty Management Records?'),
                fieldtype: 'Check',
                fieldname: 'create_records',
                default: 1
            },
            {
                label: __('Group by Employee'),
                fieldtype: 'Check',
                fieldname: 'group_by_employee',
                default: 1
            }
        ],
        primary_action_label: __('Create Records'),
        primary_action: function() {
            if (dialog.get_value('create_records')) {
                create_penalty_management_records(frm, penalty_data, dialog.get_value('group_by_employee'));
                dialog.hide();
            }
        }
    });

    // Construire le résumé HTML
    let summary_html = build_penalty_summary_html(penalty_data);
    dialog.fields_dict.penalty_summary.$wrapper.html(summary_html);

    dialog.show();
}

// Construire le HTML du résumé des pénalités
function build_penalty_summary_html(penalty_data) {
    let html = `
        <div class="penalty-summary">
            <h5>${__('Penalties Detected')}</h5>
            <table class="table table-bordered table-sm">
                <thead>
                    <tr>
                        <th>${__('Employee')}</th>
                        <th>${__('Date')}</th>
                        <th>${__('Late Penalty')}</th>
                        <th>${__('Early Penalty')}</th>
                        <th>${__('Total')}</th>
                    </tr>
                </thead>
                <tbody>
    `;

    penalty_data.penalties.forEach(penalty => {
        html += `
            <tr>
                <td>${penalty.employee_name}</td>
                <td>${penalty.attendance_date}</td>
                <td>${penalty.late_entry_penalty_minutes || 0} min</td>
                <td>${penalty.early_exit_penalty_minutes || 0} min</td>
                <td>${(penalty.late_entry_penalty_minutes || 0) + (penalty.early_exit_penalty_minutes || 0)} min</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
            <div class="mt-2">
                <strong>${__('Total Employees')}: ${penalty_data.total_employees}</strong><br>
                <strong>${__('Total Penalty Minutes')}: ${penalty_data.total_penalty_minutes}</strong>
            </div>
        </div>
    `;

    return html;
}

// Créer les enregistrements Penalty Management
function create_penalty_management_records(frm, penalty_data, group_by_employee) {
    frappe.call({
        method: 'aion_custom_hr.api.penalty_management.create_penalty_management_records',
        args: {
            shift_type: frm.doc.name,
            penalty_data: penalty_data,
            group_by_employee: group_by_employee
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Created {0} Penalty Management records', [r.message.records_created]),
                    indicator: 'green'
                });
                
                // Proposer d'ouvrir les enregistrements créés
                if (r.message.created_records && r.message.created_records.length > 0) {
                    setTimeout(() => {
                        show_created_records_dialog(r.message.created_records);
                    }, 1000);
                }
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message.error || __('Failed to create Penalty Management records'),
                    indicator: 'red'
                });
            }
        }
    });
}

// Dialogue pour afficher les enregistrements créés
function show_created_records_dialog(created_records) {
    let dialog = new frappe.ui.Dialog({
        title: __('Records Created'),
        size: 'small',
        fields: [
            {
                label: __('Open Records'),
                fieldtype: 'HTML',
                fieldname: 'records_list'
            }
        ]
    });

    let html = '<div class="records-list">';
    created_records.forEach((record, index) => {
        html += `
            <p>
                <a href="/app/penalty-managment/${record.name}" target="_blank">
                    ${record.employee_name || record.name} - ${record.from_date} to ${record.to_date}
                </a>
            </p>
        `;
    });
    html += '</div>';

    dialog.fields_dict.records_list.$wrapper.html(html);
    dialog.show();
}
