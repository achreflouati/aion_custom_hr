def update_monthly_appraisal_score_handler(doc, method):
    """
    Handler pour doc_events : met à jour le score mensuel de l'employé après soumission d'un Appraisal.
    """
    update_monthly_appraisal_score(doc.employee, doc.name)
import frappe

def update_monthly_appraisal_score(employee, appraisal):
    """
    Met à jour le champ Monthly appraisal score de l'employé avec le total_score du dernier Appraisal.
    :param employee: Nom de l'employé (Employee.name)
    :param appraisal: Nom du document Appraisal
    """
    appraisal_doc = frappe.get_doc("Appraisal", appraisal)
    total_score = appraisal_doc.total_score
    emp_doc = frappe.get_doc("Employee", employee)
    emp_doc.monthly_appraisal_score = total_score
    emp_doc.save(ignore_permissions=True)
    frappe.msgprint(f"Le score mensuel de {employee} a été mis à jour à {total_score}.")
