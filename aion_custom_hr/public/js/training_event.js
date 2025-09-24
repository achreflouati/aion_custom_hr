frappe.ui.form.on("Training Event", {
    refresh: function(frm) {
        // Ajouter les boutons seulement si le document n'est pas nouveau et est soumis
        if (!frm.is_new() && frm.doc.docstatus === 1) {
           frm.add_custom_button(__("Add Event Calendar"), function() {
    frappe.new_doc("Event", {
        event_type: "Public",
        subject: frm.doc.event_name,
        starts_on: frm.doc.start_time,
        ends_on: frm.doc.end_time,
        description: frm.doc.description,
        all_day: 0,
        event_category: "Training",
        training_event: frm.doc.name,
        "event_participants": frm.doc.employees && frm.doc.employees.length > 0 ? 
                        frm.doc.employees.map(e => (
                            console.log("Creating participant for employee: ", e.employee_name,e.status),
                            frappe.msgprint("name: " + e.employee_name,"status: " + e.status),{
                            reference_doctype: "Contact",
                            reference_docname: e.employee_name,
                            status: "Accepted"
                        })) : []
        
    });
});
            if (frm.doc.travel_request_needs) {
                // Vérifier si des Travel Requests ont déjà été créés
                let all_requests_created = frm.doc.__travel_requests_created || false;
                
                if (!all_requests_created) {
                    // Bouton pour créer les Travel Requests
                    frm.add_custom_button(__('Create Travel Requests'), function() {
                        create_travel_requests(frm);
                    }, __('Create'));
                } else {
                    // Bouton désactivé si déjà créés
                    frm.add_custom_button(__('Travel Requests Created'), function() {
                        frappe.show_alert({
                            message: __('Travel Requests have already been created for all employees'),
                            indicator: 'blue'
                        });
                    }).addClass('btn-disabled');
                }
            }
        }
    }
});

// Fonction pour créer les Travel Requests - VERSION CORRIGÉE
function create_travel_requests(frm) {
    frappe.confirm(
        __('Create Travel Requests for all {0} employees?', [frm.doc.employees.length]),
        function() {
            // Oui, créer les demandes
            let created_count = 0;
            const total_employees = frm.doc.employees ? frm.doc.employees.length : 0;
            
            
            if (total_employees === 0) {
                frappe.msgprint(__('No employees found in this training event'));
                return;
            }
            
            frappe.show_alert({
                message: __('Creating Travel Requests...'),
                indicator: 'blue'
            });
            
            // Créer un Travel Request pour chaque employé - METHODE CORRIGEE
            frm.doc.employees.forEach(function(emp) {
                // Utiliser la méthode correcte pour créer un nouveau document
                frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
                            doctype: 'Travel Request',
                            travel_type: 'International',
                            purpose_of_travel: 'Training Travel',
                            custom_training_event_linked:frm.doc.name,
                            employee: emp.employee,
                            employee_name: emp.employee_name,
                            location: frm.doc.location,
                            from_date: frm.doc.start_time,
                            to_date: frm.doc.end_time,
                            description: frm.doc.description || 'Training Event: ' + frm.doc.event_name,
                            company: frm.doc.company,
                            training_event: frm.doc.name,
                            event_name: frm.doc.event_name
                        }
                    },
                    callback: function(r) {
                        if (r.message) {
                            created_count++;
                            frappe.show_alert({
                                message: __('Created for {0}', [emp.employee_name]),
                                indicator: 'green'
                            });
                            
                            if (created_count === total_employees) {
                                // Marquer que tous les Travel Requests ont été créés
                                frappe.call({
                                    method: 'frappe.client.set_value',
                                    args: {
                                        doctype: 'Training Event',
                                        name: frm.doc.name,
                                        fieldname: '__travel_requests_created',
                                        value: 1
                                    },
                                    callback: function() {
                                        frm.reload_doc();
                                        frappe.show_alert({
                                            message: __('{0} Travel Requests created successfully', [total_employees]),
                                            indicator: 'green'
                                        });
                                        
                                    }
                                });
                            }
                        }
                    },
                    error: function(error) {
                        console.error('Error creating Travel Request:', error);
                        frappe.show_alert({
                            message: __('Error creating for {0}', [emp.employee_name]),
                            indicator: 'red'
                        });
                    }
                });
            });
            frappe.set_route('Form', 'Travel Request');
            
        },
        function() {
            // Non, annuler
            frappe.show_alert({
                message: __('Cancelled'),
                indicator: 'red'
            });
        }
        
    );
    
    console.log("Navigated to Training Request form");
}