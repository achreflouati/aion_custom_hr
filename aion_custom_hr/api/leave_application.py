import frappe
import re

def validate_leave_balance(doc, method=None):
    """
    Valide le solde de congés pour la demande de congé
    """
    if not doc.leave_type or not doc.employee:
        return
        
    # Récupérer le solde de congé de l'employé pour le type de congé
    leave_balance = frappe.db.get_value('Leave Balance', {
        'employee': doc.employee,
        'leave_type': doc.leave_type
    }, 'remaining_leaves')
    
    requested_days = doc.total_leave_days or 0
    
    if leave_balance is not None and requested_days > leave_balance:
        frappe.throw(f"Solde insuffisant : il vous reste {leave_balance} jours, vous avez demandé {requested_days}.")




def before_save_leave_application(doc, method):
    """
    Récupère tous les emails des chefs de projet et les stocke dans un champ personnalisé
    """
    # Initialiser la liste des emails
    emails = []
    
    # Vérifier si la table enfant existe et a des données
    if hasattr(doc, 'employee_tasks') and doc.employee_tasks:
        for task in doc.employee_tasks:
            if task.project_manager_email:
                # Valider l'email avant de l'ajouter
                if is_valid_email(task.project_manager_email):
                    emails.append(task.project_manager_email)
                else:
                    # Logger les emails invalides
                    frappe.log_error(
                        f"Email invalide pour le projet {task.project}: {task.project_manager_email}",
                        "Leave Application Notification"
                    )
    
    # Stocker dans le champ personnalisé (séparé par des virgules)
    doc.all_project_managers_emails = ", ".join(emails) if emails else "Aucun email valide"

def is_valid_email(email):
    """
    Valide le format d'un email
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) if email else False

# ... autres fonctions leave_application ...