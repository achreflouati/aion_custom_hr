import frappe

@frappe.whitelist()
def update_monthly_appraisal_score_handler(doc, method=None):
    import json
    # Si doc est une chaîne, le charger en dict
    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))
    frappe.logger().info(f"Appraisal submitted: {doc.name} for employee {doc.employee}")
    last_appraisal = frappe.get_all(
        "Appraisal",
        filters={"employee": doc.employee, "docstatus": 1},
        fields=["final_score", "total_score"],
        order_by="modified desc",
        limit=1
    )
    if last_appraisal:
        raw_score = last_appraisal[0].get("total_score", 0)
        monthly_score = (raw_score / 5) * 100 if raw_score else 0
    else:
        monthly_score = 0
    emp_doc = frappe.get_doc("Employee", doc.employee)
    if emp_doc.monthly_appraisal_score != monthly_score:
        frappe.db.set_value("Employee", doc.employee, "monthly_appraisal_score", monthly_score)
