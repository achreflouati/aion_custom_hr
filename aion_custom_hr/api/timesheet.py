import frappe

def check_project_approver(project, user):
    # Récupérer le département du projet
    department = frappe.db.get_value('Project', project, 'department')
    # Vérifier si l'utilisateur est approver dans ce département
    is_approver = frappe.db.exists('Work Assignment Approver', {
        'parenttype': 'Department',
        'parent': department,
        'approver': user
    })
    # Lister tous les projets liés à cet employé
    employee = frappe.db.get_value('Employee', {'user_id': user}, 'name')
    projects = frappe.get_all('Project', filters={'employee': employee}, pluck='name')
    return {
        'is_approver': bool(is_approver),
        'projects': projects
    }
