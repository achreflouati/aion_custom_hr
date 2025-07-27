import frappe

def validate_leave_balance(doc, method=None):
    # Récupérer le solde de congé de l'employé pour le type de congé
    leave_balance = frappe.db.get_value('Leave Balance', {
        'employee': doc.employee,
        'leave_type': doc.leave_type
    }, 'remaining_leaves')
    requested_days = doc.total_leave_days or 0
    if leave_balance is not None and requested_days > leave_balance:
        frappe.throw(f"Solde insuffisant : il vous reste {leave_balance} jours, vous avez demandé {requested_days}.")

# Pour le workflow, ajoutez ce hook dans hooks.py :
# doc_events = {
#     'Leave Application': {
#         'validate': 'aion_custom_hr.api.leave_application.validate_leave_balance'
#     }
# }
