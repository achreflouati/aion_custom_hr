import frappe
import json
from frappe.utils import getdate, nowdate

@frappe.whitelist()
def update_monthly_appraisal_score_handler(doc, method=None):
    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))

    frappe.logger().info(f"Appraisal submitted: {doc.get('name')} for employee {doc.get('employee')}")

    if not doc.get("employee"):
        return

    # dernier appraisal validé de l'employé
    last_appraisal = frappe.get_all(
        "Appraisal",
        filters={"employee": doc.get("employee"), "docstatus": 1},
        fields=["name", "final_score", "total_score", "modified"],
        order_by="modified desc",
        limit=1
    )

    if last_appraisal:
        la = last_appraisal[0]
        raw_score = la.get("total_score", 0) or 0
        monthly_score = (raw_score / 5) * 100 if raw_score else 0
        appraisal_ref = la.get("name")
        appraisal_modified = la.get("modified")
    else:
        monthly_score = 0
        appraisal_ref = doc.get("name")
        appraisal_modified = doc.get("modified") or nowdate()

    emp = frappe.get_doc("Employee", doc.get("employee"))

    try:
        if emp.get("monthly_appraisal_score") != monthly_score:
            frappe.db.set_value("Employee", emp.name, "monthly_appraisal_score", monthly_score)
    except Exception:
        pass

    # manager score
    manager_score = None
    manager_last = None
    manager_id = emp.get("reports_to")
    if manager_id:
        manager_last = frappe.get_all(
            "Appraisal",
            filters={"employee": manager_id, "docstatus": 1},
            fields=["total_score", "modified"],
            order_by="modified desc",
            limit=1
        )
        
        if manager_last:
            m_raw = manager_last[0].get("total_score", 0) or 0
            manager_score = (m_raw / 5) * 100 if m_raw else 0
        else:
            manager_score = 0

        try:
            
                frappe.db.set_value("Employee", emp.name, "manager_appraisal_score", manager_score)
                frappe.throw(f"Set manager appraisal score to {manager_score}")
        except Exception:
            pass

    # append to child table on Employee (fieldname configurable)
    table_fieldname = "appraisal_history"
    if emp.meta.get_field(table_fieldname):
        existing_refs = [r.get("appraisal_reference") for r in (emp.get(table_fieldname) or []) if r.get("appraisal_reference")]
        if appraisal_ref in existing_refs:
            return

        row = {
            "appraisal_date": getdate(appraisal_modified) if appraisal_modified else getdate(nowdate()),
            "employee": emp.name,
            "employee_name": emp.get("employee_name") or emp.get("name"),
            "appraisal_score": monthly_score,
            "final_score": (last_appraisal[0].get("final_score") if last_appraisal else doc.get("final_score", 0)),
            "appraisal_reference": appraisal_ref
        }

        if manager_id:
            try:
                mgr = frappe.get_doc("Employee", manager_id)
                row.update({
                    "manager": mgr.name,
                    "manager_name": mgr.get("employee_name") or mgr.name,
                    "manager_score": manager_score if manager_score is not None else None,
                    "manager_score_date": None
                })
                if manager_last and manager_last[0].get("modified"):
                    row["manager_score_date"] = getdate(manager_last[0].get("modified"))
            except Exception:
                pass

        try:
            emp.append(table_fieldname, row)
            emp.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to append appraisal history row: {e}", "update_monthly_appraisal_score_handler")
    else:
        frappe.log_error(f"Employee missing child table field '{table_fieldname}'", "update_monthly_appraisal_score_handler")
