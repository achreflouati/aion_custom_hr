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
    }
});
