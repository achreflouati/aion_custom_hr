import frappe
from frappe import _
from frappe.utils import getdate, add_months, today


@frappe.whitelist()
def create_employee_contract(employee_id, contract_type="Standard", duration_months=12):
    """
    Crée un contrat pour un employé avec des données pré-remplies
    """
    if not employee_id:
        frappe.throw(_("Employee ID is required"))
    
    # Récupérer les informations de l'employé
    employee = frappe.get_doc("Employee", employee_id)
    
    # Créer le contrat avec les données de l'employé
    contract = frappe.new_doc("Contract")
    
    # Informations de base
    contract.party_type = "Employee"
    contract.party_name = employee.name
    contract.party_user = employee.user_id
    
    # Dates
    contract.start_date = employee.date_of_joining or today()
    contract.end_date = add_months(contract.start_date, duration_months)
    
    # Termes du contrat
    contract.contract_terms = generate_contract_terms(employee, contract_type)
    
    # Références
    contract.document_type = ""
    contract.document_name = ""
    
    # Statut initial
    contract.status = "Unsigned"
    contract.requires_fulfilment = 1
    
    # Ajouter des termes d'accomplissement de base
    contract.append("fulfilment_terms", {
        "requirement": "Complete employee onboarding process",
        "notes": "Employee must complete all required onboarding documentation"
    })
    
    contract.append("fulfilment_terms", {
        "requirement": "Provide required identification documents",
        "notes": "Valid ID, passport, and other legal documents"
    })
    
    contract.append("fulfilment_terms", {
        "requirement": "Complete probation period evaluation",
        "notes": f"Evaluation to be completed after probation period"
    })
    
    # Sauvegarder le contrat
    contract.insert()
    
    return {
        "contract_name": contract.name,
        "message": _("Contract created successfully for employee {0}").format(employee.employee_name)
    }


def generate_contract_terms(employee, contract_type="Standard"):
    """
    Génère les termes du contrat basés sur les informations de l'employé
    """
    
    terms_template = f"""
    <h2>Employment Contract - {contract_type}</h2>
    
    <h3>Employee Information</h3>
    <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
        <tr style="background-color: #f5f5f5;">
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Employee Name:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{employee.employee_name or 'N/A'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Employee ID:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{employee.name or 'N/A'}</td>
        </tr>
        <tr style="background-color: #f5f5f5;">
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Department:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{employee.department or 'N/A'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Designation:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{employee.designation or 'N/A'}</td>
        </tr>
        <tr style="background-color: #f5f5f5;">
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Date of Joining:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{employee.date_of_joining or 'N/A'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Employment Type:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{employee.employment_type or 'N/A'}</td>
        </tr>
        <tr style="background-color: #f5f5f5;">
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Branch:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{employee.branch or 'N/A'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Company:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{employee.company or 'N/A'}</td>
        </tr>
    </table>
    
    <h3>Terms and Conditions</h3>
    
    <h4>1. Employment Relationship</h4>
    <p>This contract establishes an employment relationship between <strong>{employee.company or 'The Company'}</strong> 
    and <strong>{employee.employee_name or 'The Employee'}</strong> for the position of 
    <strong>{employee.designation or 'Employee'}</strong> in the <strong>{employee.department or 'General'}</strong> department.</p>
    
    <h4>2. Duties and Responsibilities</h4>
    <ul>
        <li>Perform assigned duties diligently and professionally</li>
        <li>Adhere to company policies and procedures</li>
        <li>Maintain confidentiality of company information</li>
        <li>Report to: <strong>{employee.reports_to or 'Direct Supervisor'}</strong></li>
    </ul>
    
    <h4>3. Compensation and Benefits</h4>
    <ul>
        <li>Salary and benefits as per company policy</li>
        <li>Leave entitlements as per company handbook</li>
        <li>Performance-based incentives (if applicable)</li>
        <li>Medical and other benefits as per company policy</li>
    </ul>
    
    <h4>4. Working Hours</h4>
    <ul>
        <li>Standard working hours as per company policy</li>
        <li>Overtime compensation as per applicable labor laws</li>
        <li>Flexible working arrangements (if applicable)</li>
    </ul>
    
    <h4>5. Probation Period</h4>
    <p>The employee will be on probation for the initial period as per company policy. 
    Performance will be evaluated, and confirmation will be subject to satisfactory completion.</p>
    
    <h4>6. Termination</h4>
    <ul>
        <li>Either party may terminate this contract with appropriate notice</li>
        <li>Notice period as per company policy and applicable laws</li>
        <li>Termination procedures as outlined in employee handbook</li>
    </ul>
    
    <h4>7. Confidentiality and Non-Disclosure</h4>
    <p>The employee agrees to maintain strict confidentiality regarding company information, 
    trade secrets, and proprietary data both during and after employment.</p>
    
    <h4>8. Compliance</h4>
    <p>This contract is subject to applicable labor laws and regulations. 
    Any disputes will be resolved as per company policy and legal procedures.</p>
    
    <p><em><strong>Note:</strong> This is a template contract. Please review and customize 
    according to your organization's specific policies, legal requirements, and local labor laws.</em></p>
    """
    
    return terms_template


@frappe.whitelist()
def get_employee_contract_summary(employee_id):
    """
    Récupère un résumé des contrats pour un employé
    """
    if not employee_id:
        return []
    
    contracts = frappe.get_all("Contract", 
        filters={
            "party_type": "Employee",
            "party_name": employee_id
        },
        fields=[
            "name", "status", "start_date", "end_date", 
            "is_signed", "signed_on", "fulfilment_status"
        ],
        order_by="creation desc"
    )
    
    return contracts


@frappe.whitelist()
def check_contract_requirements(employee_id):
    """
    Vérifie si un employé a besoin d'un nouveau contrat
    """
    if not employee_id:
        return {"needs_contract": False, "message": "No employee specified"}
    
    # Vérifier les contrats existants
    active_contracts = frappe.get_all("Contract",
        filters={
            "party_type": "Employee",
            "party_name": employee_id,
            "status": "Active"
        }
    )
    
    if not active_contracts:
        return {
            "needs_contract": True,
            "message": "No active contract found for this employee"
        }
    
    # Vérifier les contrats qui expirent bientôt
    expiring_soon = frappe.get_all("Contract",
        filters={
            "party_type": "Employee", 
            "party_name": employee_id,
            "status": "Active",
            "end_date": ["<=", add_months(today(), 2)]  # Expire dans 2 mois
        }
    )
    
    if expiring_soon:
        return {
            "needs_contract": True,
            "message": "Contract expiring soon - renewal may be required"
        }
    
    return {
        "needs_contract": False,
        "message": "Employee has active contract"
    }
