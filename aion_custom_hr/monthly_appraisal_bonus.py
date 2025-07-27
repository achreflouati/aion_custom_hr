import frappe

def calculate_monthly_appraisal_bonus(employee, base):
    print("Calculating Monthly Appraisal Bonus for employee:", employee)
    """
    Calcule le montant du composant salarial 'Monthly Appraisal Bonus' selon le score mensuel de l'employé.
    :param employee: Nom de l'employé (Employee.name)
    :param base: Montant de base du salaire
    :return: Montant du bonus
    """
    emp_doc = frappe.get_doc("Employee", employee)
    latest_score = emp_doc.monthly_appraisal_score or 0
    if latest_score >= 95:
        component_amount = base * 0.25
    elif latest_score >= 90:
        component_amount = base * 0.225
    elif latest_score >= 75:
        component_amount = base * 0.20
    elif latest_score >= 65:
        component_amount = base * 0.15
    elif latest_score >= 50:
        component_amount = base * 0.10
    else:
        component_amount = 0.0
    return component_amount
