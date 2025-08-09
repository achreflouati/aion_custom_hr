frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        // Ajouter le bouton "Create Contract" seulement si l'employé est sauvegardé
        if (!frm.is_new()) {
            frm.add_custom_button(__('Create Contract'), function() {
                create_employee_contract(frm);
            }, __('Actions'));
            
            // Optionnel: Ajouter un bouton pour voir les contrats existants
            frm.add_custom_button(__('View Contracts'), function() {
                view_employee_contracts(frm);
            }, __('Actions'));
        }
    }
});

function create_employee_contract(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first'));
        return;
    }
    
    // Préparer les données du contrat avec les informations de l'employé
    let contract_data = {
        doctype: 'Contract',
        party_type: 'Employee',
        party_name: frm.doc.name,
        party_user: frm.doc.user_id,
        start_date: frm.doc.date_of_joining || frappe.datetime.get_today(),
        
        // Pré-remplir les termes du contrat avec des informations de base
        contract_terms: generate_employee_contract_terms(frm.doc),
        
        // Définir une date de fin par défaut (1 an après la date de début)
        end_date: frm.doc.contract_end_date || frappe.datetime.add_months(frm.doc.date_of_joining || frappe.datetime.get_today(), 12),
        
        // Références au document employé - laisser vide pour éviter les erreurs de validation
        document_type: '',
        document_name: '',
        
        // Statut initial
        status: 'Unsigned',
        requires_fulfilment: 1
    };
    
    // Créer un nouveau contrat avec les données pré-remplies
    frappe.new_doc('Contract', contract_data);
    
    frappe.show_alert({
        message: __('Contract draft created with employee information'),
        indicator: 'green'
    });
}

function generate_employee_contract_terms(employee_doc) {
    let terms = `
<h3>Employment Contract Terms</h3>

<p><strong>Employee Information:</strong></p>
<ul>
    <li>Employee Name: ${employee_doc.employee_name || 'N/A'}</li>
    <li>Employee ID: ${employee_doc.name || 'N/A'}</li>
    <li>Department: ${employee_doc.department || 'N/A'}</li>
    <li>Designation: ${employee_doc.designation || 'N/A'}</li>
    <li>Date of Joining: ${employee_doc.date_of_joining || 'N/A'}</li>
    <li>Employment Type: ${employee_doc.employment_type || 'N/A'}</li>
</ul>

<p><strong>Basic Terms:</strong></p>
<ul>
    <li>This employment contract establishes the terms and conditions of employment.</li>
    <li>The employee agrees to perform duties as assigned by the company.</li>
    <li>Salary and benefits as per company policy and applicable laws.</li>
    <li>Working hours and leave policy as per company handbook.</li>
</ul>

<p><strong>Additional Information:</strong></p>
<ul>
    <li>Branch: ${employee_doc.branch || 'N/A'}</li>
    <li>Company: ${employee_doc.company || 'N/A'}</li>
    <li>Reports To: ${employee_doc.reports_to || 'N/A'}</li>
</ul>

<p><em>Note: This is a template. Please customize the terms according to your organization's policies and legal requirements.</em></p>
    `;
    
    return terms;
}

function view_employee_contracts(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first'));
        return;
    }
    
    // Ouvrir la liste des contrats filtrée pour cet employé
    frappe.route_options = {
        "party_type": "Employee",
        "party_name": frm.doc.name
    };
    frappe.set_route("List", "Contract");
}

// Fonction pour ajouter des indicateurs visuels
frappe.ui.form.on('Employee', {
    onload: function(frm) {
        // Vérifier s'il y a des contrats existants pour cet employé
        if (!frm.is_new()) {
            check_existing_contracts(frm);
        }
    }
});

function check_existing_contracts(frm) {
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Contract',
            filters: {
                party_type: 'Employee',
                party_name: frm.doc.name
            }
        },
        callback: function(r) {
            if (r.message > 0) {
                // Afficher un indicateur si des contrats existent
                frm.dashboard.add_indicator(__('Contracts: {0}', [r.message]), 
                    r.message > 0 ? 'blue' : 'grey');
                
                // Ajouter des informations supplémentaires
                get_contract_summary(frm);
            }
        }
    });
}

function get_contract_summary(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Contract',
            filters: {
                party_type: 'Employee',
                party_name: frm.doc.name
            },
            fields: ['name', 'status', 'start_date', 'end_date', 'is_signed'],
            limit: 5,
            order_by: 'creation desc'
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let contract_info = '<div class="alert alert-info">';
                contract_info += '<strong>Recent Contracts:</strong><br>';
                
                r.message.forEach(function(contract) {
                    let status_indicator = contract.is_signed ? '✅' : '⏳';
                    contract_info += `${status_indicator} <a href="/app/contract/${contract.name}">${contract.name}</a> - ${contract.status}<br>`;
                });
                
                contract_info += '</div>';
                
                // Ajouter les informations au formulaire
                frm.set_df_property('employee_name', 'description', contract_info);
            }
        }
    });
}
