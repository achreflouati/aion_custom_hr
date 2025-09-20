import frappe
from frappe import _


@frappe.whitelist()
def get_employee_tasks(employee):
    """
    Récupère toutes les tâches actives d'un employé avec les informations de projet
    et l'email du chef de projet (via custom_project_manager__)
    """
    if not employee:
        return []
    
    # Récupérer les tâches de l'employé avec les informations de projet
    tasks = frappe.db.sql("""
        SELECT 
            t.name,
            t.subject,
            t.status,
            t.priority,
            t.progress,
            t.exp_start_date,
            t.exp_end_date,
            t.department,
            t.employee,
            t.project,  -- Projet associé
            p.project_name,  -- Nom du projet
            p.custom_project_manager__,  -- Chef de projet (ID employé)
            emp.employee_name as project_manager_name,  -- Nom du chef de projet
            emp.user_id as project_manager_user_id,  -- User ID du chef de projet
            u.email as project_manager_email  -- Email du chef de projet
        FROM 
            `tabTask manger HR` t
        LEFT JOIN 
            `tabProject` p ON t.project = p.name
        LEFT JOIN
            `tabEmployee` emp ON p.custom_project_manager__ = emp.name
        LEFT JOIN
            `tabUser` u ON emp.user_id = u.name
        WHERE 
            t.employee = %(employee)s
            AND t.status NOT IN ('Completed', 'Cancelled')
            AND t.docstatus != 2
        ORDER BY 
            t.priority DESC, t.exp_end_date ASC
    """, {
        'employee': employee
    }, as_dict=1)
    
    # Pour chaque tâche, déterminer l'approbateur (toujours recalculé)
    for task in tasks:
        # Toujours recalculer l'approbateur pour avoir les données les plus récentes
        approver = get_department_approver(task.get('department'), employee)
        
        # Si pas d'approbateur trouvé, utiliser le Leave Approver par défaut
        if not approver:
            # Chercher le Leave Approver de l'employé
            leave_approver = frappe.db.get_value('Employee', employee, 'leave_approver')
            if leave_approver:
                # Récupérer le nom complet de l'approbateur
                approver_name = frappe.db.get_value('User', leave_approver, 'full_name') or leave_approver
                approver = {
                    'name': leave_approver,
                    'employee_name': approver_name,
                    'designation': 'Leave Approver'
                }
        
        # Fallback si l'email n'a pas été récupéré via la jointure SQL
        if task.get('custom_project_manager__') and not task.get('project_manager_email'):
            try:
                # Récupérer l'email via l'employé -> utilisateur
                user_id = frappe.db.get_value('Employee', task.get('custom_project_manager__'), 'user_id')
                if user_id:
                    email = frappe.db.get_value('User', user_id, 'email')
                    task['project_manager_email'] = email
            except Exception as e:
                frappe.log_error(f"Erreur récupération email pour employé {task.get('custom_project_manager__')}: {str(e)}")
                task['project_manager_email'] = ''
        
        # Fallback si le nom n'a pas été récupéré via la jointure SQL
        if task.get('custom_project_manager__') and not task.get('project_manager_name'):
            try:
                employee_name = frappe.db.get_value('Employee', task.get('custom_project_manager__'), 'employee_name')
                if employee_name:
                    task['project_manager_name'] = employee_name
            except Exception as e:
                frappe.log_error(f"Erreur récupération nom pour employé {task.get('custom_project_manager__')}: {str(e)}")
                task['project_manager_name'] = 'Non spécifié'
        
        task.update({
            'work_assignment_approver': approver.get('employee_name') if approver else 'Administrator',
            'approved_': 'pending',  # Status initial
            # Ajout des informations de projet
            'project': task.get('project', ''),
            'project_name': task.get('project_name', 'Aucun projet'),
            'project_manager': task.get('project_manager_name', ''),
            'project_manager_email': task.get('project_manager_email', '')
        })
    
    return tasks
    """
    Récupère toutes les tâches actives d'un employé avec les informations de projet
    et l'email du chef de projet
    """
    if not employee:
        return []
    
    # Récupérer les tâches de l'employé avec les informations de projet
    tasks = frappe.db.sql("""
        SELECT 
            t.name,
            t.subject,
            t.status,
            t.priority,
            t.progress,
            t.exp_start_date,
            t.exp_end_date,
            t.department,
            t.employee,
            t.project,  -- Projet associé
            p.project_name,  -- Nom du projet
            p.custom_project_manager__,  -- Chef de projet (employé)
            emp.employee_name as project_manager_name,  -- Nom du chef de projet
            emp.user_id as project_manager_user_id,  -- User ID du chef de projet
            u.email as project_manager_email  -- Email du chef de projet
        FROM 
            `tabTask manger HR` t
        LEFT JOIN 
            `tabProject` p ON t.project = p.name
        LEFT JOIN
            `tabEmployee` emp ON p.custom_project_manager__ = emp.name
        LEFT JOIN
            `tabUser` u ON emp.user_id = u.name
        WHERE 
            t.employee = %(employee)s
            AND t.status NOT IN ('Completed', 'Cancelled')
            AND t.docstatus != 2
        ORDER BY 
            t.priority DESC, t.exp_end_date ASC
    """, {
        'employee': employee
    }, as_dict=1)
    
    # Pour chaque tâche, déterminer l'approbateur (toujours recalculé)
    for task in tasks:
        # Toujours recalculer l'approbateur pour avoir les données les plus récentes
        approver = get_department_approver(task.get('department'), employee)
        
        # Si pas d'approbateur trouvé, utiliser le Leave Approver par défaut
        if not approver:
            # Chercher le Leave Approver de l'employé
            leave_approver = frappe.db.get_value('Employee', employee, 'leave_approver')
            if leave_approver:
                # Récupérer le nom complet de l'approbateur
                approver_name = frappe.db.get_value('User', leave_approver, 'full_name') or leave_approver
                approver = {
                    'name': leave_approver,
                    'employee_name': approver_name,
                    'designation': 'Leave Approver'
                }
        
        task.update({
            'work_assignment_approver': approver.get('employee_name') if approver else 'Administrator',
            'approved_': 'pending',  # Status initial
            # Ajout des informations de projet
            'project': task.get('project', ''),
            'project_name': task.get('project_name', 'Aucun projet'),
            'project_manager': task.get('project_manager_name', ''),
            'project_manager_email': task.get('project_manager_email', '')
        })
    
    return tasks
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
    
    # Pour chaque tâche, déterminer l'approbateur (toujours recalculé)
    for task in tasks:
        # Toujours recalculer l'approbateur pour avoir les données les plus récentes
        approver = get_department_approver(task.get('department'), employee)
        
        # Si pas d'approbateur trouvé, utiliser le Leave Approver par défaut
        if not approver:
            # Chercher le Leave Approver de l'employé
            leave_approver = frappe.db.get_value('Employee', employee, 'leave_approver')
            if leave_approver:
                # Récupérer le nom complet de l'approbateur
                approver_name = frappe.db.get_value('User', leave_approver, 'full_name') or leave_approver
                approver = {
                    'name': leave_approver,
                    'employee_name': approver_name,
                    'designation': 'Leave Approver'
                }
        
        task.update({
            'work_assignment_approver': approver.get('employee_name') if approver else 'Administrator',
            'approved_': 'pending'  # Status initial
        })
    
    return tasks


@frappe.whitelist()
def get_department_approver(department, employee):
    """
    Trouve un approbateur dans le département (via custom field table ou designation)
    """
    if not department:
        return None
    
    frappe.logger().info(f"Searching approver for department: {department}, employee: {employee}")
    
    # D'abord chercher si le département a des approbateurs définis via le child table
    try:
        department_approvers = frappe.get_all('Department Approver', 
            filters={'parent': department, 'parenttype': 'Department'},
            fields=['approver'])
        
        frappe.logger().info(f"Found department approvers: {department_approvers}")
        
        if department_approvers:
            # Récupérer tous les approbateurs de la liste
            approver_names = []
            
            for approver_row in department_approvers:
                approver_user = approver_row.get('approver')
                
                if approver_user:
                    # Chercher l'employé correspondant à cet utilisateur
                    employee_data = frappe.db.get_value('Employee', 
                        {'user_id': approver_user, 'status': 'Active'}, 
                        ['name', 'employee_name', 'designation'], as_dict=True)
                    
                    if employee_data and employee_data.name != employee:
                        approver_names.append(employee_data.employee_name)
                    else:
                        # Si pas d'employé trouvé, utiliser les données utilisateur
                        user_data = frappe.db.get_value('User', approver_user, 
                            ['name', 'full_name'], as_dict=True)
                        if user_data:
                            approver_names.append(user_data.full_name or user_data.name)
            
            # Si on a trouvé des approbateurs, les retourner
            if approver_names:
                # Joindre tous les noms avec une virgule
                combined_names = ", ".join(approver_names)
                frappe.logger().info(f"Found multiple department approvers: {combined_names}")
                
                return {
                    'name': 'Multiple Approvers',
                    'employee_name': combined_names,
                    'designation': 'Department Approvers'
                }
    except Exception as e:
        frappe.logger().warning(f"Error reading department approvers: {e}")
    
    # Fallback: chercher des managers/superviseurs par désignation
    frappe.logger().info("No department approver found, falling back to designation search")
    
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
    
    frappe.logger().info(f"Found managers/supervisors: {approver}")
    
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
        
        frappe.logger().info(f"Found other employees: {approver}")
    
    # Si toujours aucun, prendre l'administrateur par défaut
    if not approver:
        approver = [{
            'name': 'Administrator',
            'employee_name': 'System Administrator',
            'designation': 'Administrator'
        }]
        frappe.logger().info(f"Using fallback: {approver}")
    
    result = approver[0] if approver else None
    frappe.logger().info(f"Final approver result: {result}")
    return result


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


def auto_load_employee_tasks(doc, method=None, force_reload=False):
    """
    Charge automatiquement les tâches lors de la sélection d'un employé
    Hook à utiliser dans Leave Application
    """
    if doc.employee and (not doc.get('employee_tasks') or force_reload):
        try:
            tasks = get_employee_tasks(doc.employee)
            
            # Vider la table existante
            doc.employee_tasks = []
            
            # Ajouter les tâches avec les approbateurs recalculés
            for task in tasks:
                doc.append("employee_tasks", {
                    "task_manger_hr": task.get("name"),
                    "subject_of_task": task.get("subject"),
                    "status": task.get("status"),
                    "progress": str(task.get("progress", 0)),
                    "employee": task.get("employee"),
                    "department": task.get("department"),
                    "work_assignment_approver": task.get("work_assignment_approver"),
                    "approved_": "pending",
                    # Ajout des nouveaux champs de projet
                    "project": task.get("project", ""),
                    "project_manager": task.get("project_manager", ""),
                    "project_manager_email": task.get("project_manager_email", "")
                })
                
        except Exception as e:
            frappe.log_error(f"Erreur auto_load_employee_tasks: {str(e)}")
    """
    Charge automatiquement les tâches lors de la sélection d'un employé
    Hook à utiliser dans Leave Application
    """
    if doc.employee and (not doc.get('employee_tasks') or force_reload):
        try:
            tasks = get_employee_tasks(doc.employee)
            
            # Vider la table existante
            doc.employee_tasks = []
            
            # Ajouter les tâches avec les approbateurs recalculés
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
    Recharge les tâches d'un employé pour une demande de congé avec recalcul des approbateurs
    """
    try:
        doc = frappe.get_doc("Leave Application", leave_application)
        if doc.employee:
            # Forcer le rechargement même si la table n'est pas vide
            auto_load_employee_tasks(doc, force_reload=True)
            doc.save()
            return {"status": "success", "message": "Tâches rechargées avec succès et approbateurs mis à jour"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
