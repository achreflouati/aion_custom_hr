import frappe
from frappe import _


@frappe.whitelist()
def get_employee_tasks(employee):
    """
    Récupère toutes les tâches actives d'un employé
    """
    if not employee:
        return []
    
    # Récupérer les tâches de l'employé
    tasks = frappe.db.sql("""
        SELECT 
            name,
            subject,
            status,
            priority,
            progress,
            exp_start_date,
            exp_end_date,
            department,
            employee
        FROM 
            `tabTask manger HR`
        WHERE 
            employee = %(employee)s
            AND status NOT IN ('Completed', 'Cancelled')
            AND docstatus != 2
        ORDER BY 
            priority DESC, exp_end_date ASC
    """, {
        'employee': employee
    }, as_dict=1)
    
    # Pour chaque tâche, déterminer l'approbateur
    for task in tasks:
        # Trouver l'approbateur dans le département
        approver = get_department_approver(task.get('department'), employee)
        
        # Si pas d'approbateur trouvé, utiliser le Leave Approver par défaut
        if not approver:
            # Chercher le Leave Approver de l'employé
            leave_approver = frappe.db.get_value('Employee', employee, 'leave_approver')
            if leave_approver:
                approver = {
                    'name': leave_approver,
                    'employee_name': leave_approver,
                    'designation': 'Leave Approver'
                }
        
        task.update({
            'work_assignment_approver': approver.get('employee_name') if approver else 'No Approver Found',
            'approved_': 'pending'  # Status initial
        })
    
    return tasks


def get_department_approver(department, employee):
    """
    Trouve un approbateur dans le département (manager, director, etc.)
    """
    if not department:
        return None
    
    # D'abord chercher des managers/superviseurs
    approver = frappe.db.sql("""
        SELECT 
            name,
            employee_name,
            designation
        FROM 
            `tabEmployee`
        WHERE 
            department = %(department)s
            AND name != %(employee)s
            AND status = 'Active'
            AND (
                designation LIKE %(manager_pattern)s OR 
                designation LIKE %(head_pattern)s OR 
                designation LIKE %(director_pattern)s OR
                designation LIKE %(supervisor_pattern)s
            )
        ORDER BY 
            CASE 
                WHEN designation LIKE %(director_pattern)s THEN 1
                WHEN designation LIKE %(manager_pattern)s THEN 2
                WHEN designation LIKE %(head_pattern)s THEN 3
                WHEN designation LIKE %(supervisor_pattern)s THEN 4
                ELSE 5
            END
        LIMIT 1
    """, {
        'department': department,
        'employee': employee,
        'manager_pattern': '%Manager%',
        'head_pattern': '%Head%',
        'director_pattern': '%Director%',
        'supervisor_pattern': '%Supervisor%'
    }, as_dict=1)
    
    # Si aucun manager trouvé, prendre n'importe quel autre employé actif du département
    if not approver:
        approver = frappe.db.sql("""
            SELECT 
                name,
                employee_name,
                designation
            FROM 
                `tabEmployee`
            WHERE 
                department = %(department)s
                AND name != %(employee)s
                AND status = 'Active'
            ORDER BY 
                creation ASC
            LIMIT 1
        """, {
            'department': department,
            'employee': employee
        }, as_dict=1)
    
    # Si toujours aucun, prendre l'administrateur par défaut
    if not approver:
        approver = [{
            'name': 'Administrator',
            'employee_name': 'System Administrator',
            'designation': 'Administrator'
        }]
    
    return approver[0] if approver else None


@frappe.whitelist()
def update_task_approval_decisions(leave_application, tasks_data):
    """
    Met à jour les décisions d'approbation des tâches et le statut de la demande de congé
    """
    if not leave_application or not tasks_data:
        return {"status": "error", "message": "Paramètres manquants"}
    
    try:
        # Parser les données si c'est une chaîne JSON
        if isinstance(tasks_data, str):
            import json
            tasks_data = json.loads(tasks_data)
        
        leave_doc = frappe.get_doc("Leave Application", leave_application)
        
        # Analyser les décisions
        approved_count = 0
        rejected_count = 0
        pending_count = 0
        total_tasks = len(tasks_data)
        
        for task_data in tasks_data:
            decision = task_data.get('approved_', 'pending')
            if decision == 'approved':
                approved_count += 1
            elif decision == 'rejected':
                rejected_count += 1
            else:
                pending_count += 1
        
        # Déterminer le statut de la demande de congé
        status_message = ""
        
        if rejected_count > 0:
            # Si des tâches sont rejetées, la demande doit être rejetée
            if hasattr(leave_doc, 'workflow_state'):
                leave_doc.workflow_state = "Rejected"
            leave_doc.status = "Rejected"
            status_message = f"❌ Demande rejetée: {rejected_count} tâche(s) rejetée(s)"
            
        elif approved_count == total_tasks and total_tasks > 0:
            # Si toutes les tâches sont approuvées
            if hasattr(leave_doc, 'workflow_state'):
                leave_doc.workflow_state = "Approved"
            leave_doc.status = "Approved"
            status_message = f"✅ Demande approuvée: Toutes les {approved_count} tâches approuvées"
            
        elif pending_count == 0 and approved_count > 0:
            # Approbation partielle
            status_message = f"⏳ En cours: {approved_count} approuvées, {rejected_count} rejetées"
        else:
            status_message = f"⏳ En attente: {pending_count} tâches en attente de décision"
        
        # Sauvegarder si le statut a changé
        if rejected_count > 0 or approved_count == total_tasks:
            leave_doc.save(ignore_permissions=True)
            
            # Ajouter un commentaire
            comment_content = f"Révision des tâches: {status_message}"
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": "Leave Application", 
                "reference_name": leave_application,
                "content": comment_content
            }).insert(ignore_permissions=True)
        
        return {
            "status": "success",
            "message": status_message,
            "leave_status": leave_doc.status,
            "approved_tasks": approved_count,
            "rejected_tasks": rejected_count,
            "pending_tasks": pending_count,
            "total_tasks": total_tasks
        }
        
    except Exception as e:
        frappe.log_error(f"Erreur update_task_approval_decisions: {str(e)}")
        return {"status": "error", "message": f"Erreur: {str(e)}"}


def auto_load_employee_tasks(doc, method=None):
    """
    Charge automatiquement les tâches lors de la sélection d'un employé
    Hook à utiliser dans Leave Application
    """
    if doc.employee and not doc.get('employee_tasks'):
        try:
            tasks = get_employee_tasks(doc.employee)
            
            # Vider la table existante
            doc.employee_tasks = []
            
            # Ajouter les tâches
            for task in tasks:
                doc.append("employee_tasks", {
                    "task_manger_hr": task.get("name"),
                    "subject_of_task": task.get("subject"),
                    "status": task.get("status"),
                    "progress": str(task.get("progress", 0)),
                    "employee": task.get("employee"),
                    "department": task.get("department"),
                    "work_assignment_approver": task.get("work_assignment_approver"),
                    "approved_": "pending"
                })
                
        except Exception as e:
            frappe.log_error(f"Erreur auto_load_employee_tasks: {str(e)}")


@frappe.whitelist()
def reload_employee_tasks(leave_application):
    """
    Recharge les tâches d'un employé pour une demande de congé
    """
    try:
        doc = frappe.get_doc("Leave Application", leave_application)
        if doc.employee:
            auto_load_employee_tasks(doc)
            doc.save()
            return {"status": "success", "message": "Tâches rechargées avec succès"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
