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
        fields=["name", "final_score", "total_score", "modified", "appraisal_cycle"],
        order_by="modified desc",
        limit=1
    )

    la = last_appraisal[0] if last_appraisal else None
    if la:
        raw_score = la.get("total_score", 0) or 0
        monthly_score = (raw_score / 5) * 100 if raw_score else 0
        appraisal_ref = la.get("name")
        appraisal_modified = la.get("modified")
        appraisal_cycle = la.get("appraisal_cycle")
        la_total = la.get("total_score")
        la_final = la.get("final_score")
    else:
        monthly_score = 0
        appraisal_ref = doc.get("name")
        appraisal_modified = doc.get("modified") or nowdate()
        appraisal_cycle = doc.get("appraisal_cycle")
        la_total = doc.get("total_score", 0)
        la_final = doc.get("final_score", 0)

    # récupérer statut et dates depuis le DocType "Appraisal Cycle" (si link existe)
    cycle_status = None
    cycle_start = None
    cycle_end = None
    if appraisal_cycle:
        try:
            cycle_doc = frappe.get_doc("Appraisal Cycle", appraisal_cycle)
            if cycle_doc:
                cycle_status = cycle_doc.get("status") or cycle_doc.get("state")
                cycle_start = cycle_doc.get("start_date") or cycle_doc.get("cycle_start_date")
                cycle_end = cycle_doc.get("end_date") or cycle_doc.get("cycle_end_date")
        except frappe.DoesNotExistError:
            # cycle introuvable — laisser None
            pass
        except Exception as e:
            frappe.log_error(f"Error fetching Appraisal Cycle '{appraisal_cycle}': {e}", "update_monthly_appraisal_score_handler")

    # obtenir document Employee
    try:
        emp = frappe.get_doc("Employee", doc.get("employee"))
    except Exception:
        frappe.log_error(f"Employee {doc.get('employee')} not found", "update_monthly_appraisal_score_handler")
        return

    # mettre à jour monthly_appraisal_score si nécessaire
    try:
        if emp.get("monthly_appraisal_score") != monthly_score:
            frappe.db.set_value("Employee", emp.name, "monthly_appraisal_score", monthly_score)
    except Exception as e:
        frappe.log_error(f"Failed to set monthly_appraisal_score: {e}", "update_monthly_appraisal_score_handler")

    # manager score et dernier appraisal du manager
    manager_score = None
    manager_last = None
    manager_id = emp.get("reports_to")
    if manager_id:
        manager_last = frappe.get_all(
            "Appraisal",
            filters={"employee": manager_id, "docstatus": 1},
            fields=["name", "total_score", "final_score", "modified", "appraisal_cycle"],
            order_by="modified desc",
            limit=1
        )
        if manager_last:
            m = manager_last[0]
            m_raw = m.get("total_score", 0) or 0
            manager_score = (m_raw / 5) * 100 if m_raw else 0
        else:
            manager_score = 0

        try:
            if emp.get("manager_appraisal_score") != manager_score:
                frappe.db.set_value("Employee", emp.name, "manager_appraisal_score", manager_score)
        except Exception as e:
            frappe.log_error(f"Failed to set manager_appraisal_score: {e}", "update_monthly_appraisal_score_handler")

    # Append to employee child table
    emp_table = "appraisal_history"
    try:
        # robust append: reload Employee before append and retry on "Document has been modified"
        def robust_append_employee_row(employee_name, table_field, row, max_retries=2):
            for attempt in range(max_retries):
                try:
                    fresh_emp = frappe.get_doc("Employee", employee_name)  # always get latest
                    fresh_emp.append(table_field, row)
                    fresh_emp.save(ignore_permissions=True)
                    return True
                except Exception as e:
                    msg = str(e)
                    # conflit de modification -> recharger et retenter
                    if "Document has been modified" in msg or "Please refresh to get the latest document" in msg:
                        frappe.logger().warning(f"Document modified conflict for Employee {employee_name}, retry {attempt+1}/{max_retries}")
                        continue
                    # autre erreur -> log et remonter
                    frappe.log_error(f"Failed to append row to {table_field} for {employee_name}: {e}", "update_monthly_appraisal_score_handler")
                    return False
            # si on arrive ici, on a épuisé les retries
            frappe.log_error(f"Exhausted retries appending to {table_field} for {employee_name}", "update_monthly_appraisal_score_handler")
            return False

        # usage pour employee
        if emp.meta.get_field(emp_table):
            existing_refs = [r.get("appraisal_reference") for r in (emp.get(emp_table) or []) if r.get("appraisal_reference")]
            if appraisal_ref not in existing_refs:
                emp_row = {
                    "appraisal_date": getdate(appraisal_modified) if appraisal_modified else getdate(nowdate()),
                    "reference_date": getdate(appraisal_modified) if appraisal_modified else None,
                    "employee": emp.name,
                    "employee_name": emp.get("employee_name") or emp.name,
                    "appraisal_cycle": appraisal_cycle,
                    "cycle_start_date": cycle_start,
                    "cycle_end_date": cycle_end,
                    "status": cycle_status,
                    "appraisal_score": monthly_score,
                    "total_score": la_total,
                    "final_score": la_final,
                    "appraisal_reference": appraisal_ref
                }
                if manager_id:
                    try:
                        mgr = frappe.get_doc("Employee", manager_id)
                        emp_row.update({
                            "manager": mgr.name,
                            "manager_name": mgr.get("employee_name") or mgr.name,
                            "manager_score": manager_score if manager_score is not None else None,
                            "manager_score_date": getdate(manager_last[0].get("modified")) if manager_last and manager_last[0].get("modified") else None
                        })
                    except Exception:
                        pass

                robust_append_employee_row(emp.name, emp_table, emp_row)
    except Exception as e:
        frappe.log_error(f"Failed to append to {emp_table}: {e}", "update_monthly_appraisal_score_handler")

    # Append to manager child table (on manager's Employee doc)
    if manager_id:
        try:
            mgr_table = "appraisal_manager_history"
            # robust usage: reuse the helper to avoid "Document has been modified" and stale doc
            def robust_append_employee_row(employee_name, table_field, row, max_retries=2):
                for attempt in range(max_retries):
                    try:
                        fresh_emp = frappe.get_doc("Employee", employee_name)  # always get latest
                        fresh_emp.append(table_field, row)
                        fresh_emp.save(ignore_permissions=True)
                        return True
                    except Exception as e:
                        msg = str(e)
                        if "Document has been modified" in msg or "Please refresh to get the latest document" in msg:
                            frappe.logger().warning(f"Document modified conflict for Employee {employee_name}, retry {attempt+1}/{max_retries}")
                            continue
                        frappe.log_error(f"Failed to append row to {table_field} for {employee_name}: {e}", "update_monthly_appraisal_score_handler")
                        return False
                frappe.log_error(f"Exhausted retries appending to {table_field} for {employee_name}", "update_monthly_appraisal_score_handler")
                return False

            # get fresh manager doc before checking existing refs
            mgr_emp = frappe.get_doc("Employee", manager_id)
            if mgr_emp.meta.get_field(mgr_table):
                existing_mgr_refs = [r.get("appraisal_reference") for r in (mgr_emp.get(mgr_table) or []) if r.get("appraisal_reference")]
                if appraisal_ref not in existing_mgr_refs:
                    mgr_row = {
                        "appraisal_date": getdate(appraisal_modified) if appraisal_modified else getdate(nowdate()),
                        "reference_date": getdate(appraisal_modified) if appraisal_modified else None,
                        "manager": mgr_emp.name,
                        "manager_name": mgr_emp.get("employee_name") or mgr_emp.name,
                        "appraisal_cycle": appraisal_cycle,
                        "cycle_start_date": cycle_start,
                        "cycle_end_date": cycle_end,
                        "status": cycle_status,
                        "appraisal_score": manager_score if manager_score is not None else None,
                        "total_score": (manager_last[0].get("total_score") if manager_last else None),
                        "final_score": (manager_last[0].get("final_score") if manager_last else None),
                        "employee": emp.name,
                        "employee_name": emp.get("employee_name") or emp.name,
                        "employee_score": monthly_score,
                        "appraisal_reference": appraisal_ref
                    }
                    robust_append_employee_row(mgr_emp.name, mgr_table, mgr_row)
            else:
                frappe.log_error(f"Manager Employee missing child table field '{mgr_table}'", "update_monthly_appraisal_score_handler")
        except Exception as e:
            frappe.log_error(f"Failed to append to manager table: {e}", "update_monthly_appraisal_score_handler")
