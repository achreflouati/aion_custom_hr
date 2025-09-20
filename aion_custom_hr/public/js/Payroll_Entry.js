frappe.ui.form.on('Payroll Entry', {
    refresh: function(frm) {
        // Ajouter les boutons seulement si le document n'est pas nouveau
        if (!frm.is_new()) {
            // Bouton pour créer Penalty Management
            frm.add_custom_button(__('Create Penalty Management'), function() {
                frappe.new_doc('penalty managment');
            }, __('Create'));
            
            // Bouton pour créer Extra Hours Management  
            frm.add_custom_button(__('Create Extra Hours Management'), function() {
                frappe.new_doc('Extra Hours');
            }, __('Create'));
        }
    }
});