// Penalty Management System
// Système de gestion des pénalités avec affichage de tous les jours d'attendance

frappe.ui.form.on('penalty managment', {
    refresh: function(frm) {
        // Ajouter bouton pour charger les attendances
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Load Attendances'), function() {
                load_attendances_for_period(frm);
            });
            
            frm.add_custom_button(__('Check New Penalties'), function() {
                check_new_penalties(frm);
            });
        }
    },
    
    employee: function(frm) {
        if (frm.doc.employee && frm.doc.shift_type && frm.doc.from_date && frm.doc.to_date) {
            load_attendances_for_period(frm);
        }
    },
    
    shift_type: function(frm) {
        if (frm.doc.employee && frm.doc.shift_type && frm.doc.from_date && frm.doc.to_date) {
            load_attendances_for_period(frm);
        }
    },
    
    from_date: function(frm) {
        if (frm.doc.employee && frm.doc.shift_type && frm.doc.from_date && frm.doc.to_date) {
            load_attendances_for_period(frm);
        }
    },
    
    to_date: function(frm) {
        if (frm.doc.employee && frm.doc.shift_type && frm.doc.from_date && frm.doc.to_date) {
            load_attendances_for_period(frm);
        }
    }
});

// Fonction pour charger tous les attendances d'une période
function load_attendances_for_period(frm) {
    if (!frm.doc.employee || !frm.doc.shift_type || !frm.doc.from_date || !frm.doc.to_date) {
        frappe.msgprint(__('Please fill Employee, Shift Type, From Date and To Date'));
        return;
    }
    
    frappe.show_alert({
        message: __('Loading attendances...'),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'aion_custom_hr.api.penalty_management.load_penalties_for_period',
        args: {
            employee: frm.doc.employee,
            shift_type: frm.doc.shift_type,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                populate_penalty_details(frm, r.message.penalties);
                update_summary_fields(frm, r.message.summary);
                
                frappe.show_alert({
                    message: __('Loaded {0} attendance records', [r.message.total_records]),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint(__('No attendance records found for the selected period'));
            }
        },
        error: function(r) {
            frappe.msgprint(__('Error loading attendances: {0}', [r.message || 'Unknown error']));
        }
    });
}

// Fonction pour vérifier les nouvelles pénalités
function check_new_penalties(frm) {
    if (!frm.doc.employee || !frm.doc.shift_type || !frm.doc.from_date || !frm.doc.to_date) {
        frappe.msgprint(__('Please fill Employee, Shift Type, From Date and To Date'));
        return;
    }
    
    frappe.call({
        method: 'aion_custom_hr.api.penalty_management.check_new_penalties_for_shift',
        args: {
            employee: frm.doc.employee,
            shift_type: frm.doc.shift_type,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                let data = r.message;
                
                // Afficher statistiques
                let msg = `
                    <h4>Résumé des attendances:</h4>
                    <ul>
                        <li><strong>Total attendances:</strong> ${data.total_attendances}</li>
                        <li><strong>Avec pénalités:</strong> ${data.total_penalty_attendances}</li>
                        <li><strong>Sans pénalités:</strong> ${data.total_normal_attendances}</li>
                        <li><strong>Employés concernés:</strong> ${data.total_employees}</li>
                    </ul>
                    <h4>Totaux des pénalités:</h4>
                    <ul>
                        <li><strong>Total pénalités:</strong> ${data.total_penalty_minutes} minutes</li>
                    </ul>
                `;
                
                frappe.msgprint({
                    title: __('Penalty Analysis'),
                    message: msg,
                    indicator: 'blue'
                });
                
                // Charger les données dans le child table
                populate_penalty_details(frm, data.penalties);
                update_summary_fields(frm, data.summary);
                
            } else {
                frappe.msgprint(__('No data found for the selected period'));
            }
        }
    });
}

// Fonction pour remplir le child table avec les pénalités
function populate_penalty_details(frm, penalties) {
    // Vider le child table existant
    frm.clear_table('penalty_details');
    
    // Ajouter chaque pénalité au child table
    penalties.forEach(function(penalty) {
        let child = frm.add_child('penalty_details');
        
        // Informations de base
        child.attendance_date = penalty.attendance_date;
        child.attendance_name = penalty.attendance_name;
        
        // CHAMPS MANQUANTS AJOUTÉS :
        child.shift_type = penalty.shift_type;  // Shift Type
        child.status = penalty.status || 'Present';  // Status de l'attendance
        child.actual_late_minutes = penalty.total_late_minutes || 0;  // Actual Late (min)
        child.actual_early_minutes = penalty.total_early_exit_minutes || 0;  // Actual Early (min)
        child.original_late_penalty = penalty.late_entry_penalty_minutes || 0;  // Original Late Penalty
        child.original_early_penalty = penalty.early_exit_penalty_minutes || 0;  // Original Early Penalty
        
        // Heures d'entrée et sortie
        child.in_time = penalty.in_time ? format_time(penalty.in_time) : '';
        child.out_time = penalty.out_time ? format_time(penalty.out_time) : '';
        
        // Pénalités calculées
        child.late_entry_penalty_minutes = penalty.late_entry_penalty_minutes || 0;
        child.early_exit_penalty_minutes = penalty.early_exit_penalty_minutes || 0;
        child.applied_penalty_minutes = penalty.applied_penalty_minutes || 0;
        
        // Informations détaillées sur les retards/sorties
        child.late_entry_minutes = penalty.total_late_minutes || 0;
        child.early_exit_minutes = penalty.total_early_exit_minutes || 0;
        
        // Périodes appliquées
        child.late_entry_period_applied = penalty.late_entry_period_applied || 0;
        child.early_exit_period_applied = penalty.early_exit_period_applied || 0;
        child.period_applied = Math.max(penalty.late_entry_period_applied || 0, penalty.early_exit_period_applied || 0);
        
        // Coefficient utilisé
        child.coefficient_used = penalty.coefficient_used || 0;
        
        // Statut de la pénalité basé sur la présence de pénalités
        if (penalty.applied_penalty_minutes > 0 || penalty.late_entry_penalty_minutes > 0 || penalty.early_exit_penalty_minutes > 0) {
            child.penalty_status = 'Applied';
            child.has_penalty = 1;
        } else {
            child.penalty_status = 'No Penalty';
            child.has_penalty = 0;
        }
        
        // Commentaires/corrections
        child.correction_reason = penalty.correction_reason || '';
        child.is_corrected = penalty.is_corrected || 0;
        
        // Calculs des pénalités corrigées (initialement égales aux originales)
        child.corrected_late_penalty = penalty.late_entry_penalty_minutes || 0;
        child.corrected_early_penalty = penalty.early_exit_penalty_minutes || 0;
    });
    
    // Rafraîchir l'affichage du child table
    frm.refresh_field('penalty_details');
    
    frappe.show_alert({
        message: __('Loaded {0} attendance records into details table ({1} with penalties, {2} normal)', 
                  [penalties.length, 
                   penalties.filter(p => (p.applied_penalty_minutes > 0 || p.late_entry_penalty_minutes > 0 || p.early_exit_penalty_minutes > 0)).length,
                   penalties.filter(p => (p.applied_penalty_minutes == 0 && p.late_entry_penalty_minutes == 0 && p.early_exit_penalty_minutes == 0)).length]),
        indicator: 'green'
    });
}

// Fonction pour mettre à jour les champs de résumé
function update_summary_fields(frm, summary) {
    if (summary) {
        frm.set_value('total_late_penalty', summary.total_late_penalty || 0);
        frm.set_value('total_early_penalty', summary.total_early_penalty || 0);
        frm.set_value('total_penalty_minutes', summary.total_penalty_minutes || 0);
        
        frm.refresh_fields();
    }
}

// Event handlers pour le child table
frappe.ui.form.on('Penalty Detail', {
    correction_reason: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.correction_reason) {
            frappe.model.set_value(cdt, cdn, 'is_corrected', 1);
        }
    },
    
    is_corrected: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.is_corrected) {
            // Si corrigé, réinitialiser les pénalités appliquées
            frappe.model.set_value(cdt, cdn, 'applied_penalty_minutes', 0);
            frappe.model.set_value(cdt, cdn, 'penalty_status', 'Corrected');
        } else {
            // Restaurer la pénalité originale
            let original_penalty = (row.late_entry_penalty_minutes || 0) + (row.early_exit_penalty_minutes || 0);
            frappe.model.set_value(cdt, cdn, 'applied_penalty_minutes', original_penalty);
            frappe.model.set_value(cdt, cdn, 'penalty_status', original_penalty > 0 ? 'Applied' : 'No Penalty');
        }
        
        // Recalculer les totaux
        recalculate_totals(frm);
    }
});

// Fonction pour recalculer les totaux après correction
function recalculate_totals(frm) {
    let total_late = 0;
    let total_early = 0;
    let total_applied = 0;
    
    frm.doc.penalty_details.forEach(function(row) {
        total_late += row.late_entry_penalty_minutes || 0;
        total_early += row.early_exit_penalty_minutes || 0;
        total_applied += row.applied_penalty_minutes || 0;
    });
    
    frm.set_value('total_late_penalty', total_late);
    frm.set_value('total_early_penalty', total_early);
    frm.set_value('total_penalty_minutes', total_applied);
    
    frm.refresh_fields();
}

// Fonction utilitaire pour formater les heures
function format_time(time_str) {
    if (!time_str) return '';
    return time_str.split(' ')[1] || time_str; // Récupérer seulement l'heure
}

// Auto-refresh des attendances quand les critères changent
frappe.ui.form.on('penalty managment', {
    validate: function(frm) {
        // Validation des données avant sauvegarde
        if (frm.doc.penalty_details && frm.doc.penalty_details.length > 0) {
            // Recalculer les totaux une dernière fois
            recalculate_totals(frm);
        }
    }
});
