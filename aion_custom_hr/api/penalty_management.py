import frappe
from frappe import _
from frappe.utils import getdate, add_days, date_diff, flt
from frappe.model.document import Document

@frappe.whitelist()
def check_new_penalties_for_shift(shift_type, from_date, to_date):
    """
    Vérifier s'il y a de nouvelles pénalités pour un shift type donné
    """
    # shift_type = "shift tripoly"
    try:
        # Récupérer TOUTES les attendances (avec et sans pénalités)
        penalties = frappe.db.sql("""
            SELECT 
                a.name as attendance_name,
                a.employee,
                a.employee_name,
                a.attendance_date,
                a.shift_type,
                a.status,
                a.in_time,
                a.out_time,
                COALESCE(a.late_entry_penalty_minutes, 0) as late_entry_penalty_minutes,
                COALESCE(a.early_exit_penalty_minutes, 0) as early_exit_penalty_minutes,
                COALESCE(a.total_late_minutes, 0) as total_late_minutes,
                COALESCE(a.total_early_exit_minutes, 0) as total_early_exit_minutes,
                COALESCE(a.late_entry_period_applied, 0) as late_entry_period_applied,
                COALESCE(a.early_exit_period_applied, 0) as early_exit_period_applied
            FROM `tabAttendance` a
            WHERE a.shift_type = %s
            AND a.attendance_date BETWEEN %s AND %s
            AND a.docstatus = 1
            AND NOT EXISTS (
                SELECT 1 FROM `tabpenalty managment` pm
                WHERE pm.employee = a.employee
                AND pm.from_date <= a.attendance_date
                AND pm.to_date >= a.attendance_date
                AND pm.docstatus != 2
            )
            ORDER BY a.employee, a.attendance_date
        """, (shift_type, from_date, to_date), as_dict=True)
        
        if not penalties:
            return {"has_new_penalties": False, "has_attendances": False}
        
        # Séparer les attendances avec et sans pénalités
        attendances_with_penalties = [p for p in penalties if (p.late_entry_penalty_minutes > 0 or p.early_exit_penalty_minutes > 0)]
        attendances_without_penalties = [p for p in penalties if (p.late_entry_penalty_minutes == 0 and p.early_exit_penalty_minutes == 0)]
        
        # Calculer les statistiques
        total_employees = len(set(p.employee for p in penalties))
        total_penalty_minutes = sum((p.late_entry_penalty_minutes or 0) + (p.early_exit_penalty_minutes or 0) for p in attendances_with_penalties)
        
        # Grouper par employé
        employees_data = {}
        for penalty in penalties:
            if penalty.employee not in employees_data:
                employees_data[penalty.employee] = {
                    "employee": penalty.employee,
                    "employee_name": penalty.employee_name,
                    "penalties": [],
                    "attendances_with_penalties": [],
                    "attendances_without_penalties": [],
                    "total_late_penalty": 0,
                    "total_early_penalty": 0,
                    "total_attendances": 0
                }
            
            employees_data[penalty.employee]["penalties"].append(penalty)
            employees_data[penalty.employee]["total_attendances"] += 1
            
            if penalty.late_entry_penalty_minutes > 0 or penalty.early_exit_penalty_minutes > 0:
                employees_data[penalty.employee]["attendances_with_penalties"].append(penalty)
                employees_data[penalty.employee]["total_late_penalty"] += penalty.late_entry_penalty_minutes or 0
                employees_data[penalty.employee]["total_early_penalty"] += penalty.early_exit_penalty_minutes or 0
            else:
                employees_data[penalty.employee]["attendances_without_penalties"].append(penalty)
        
        return {
            "has_new_penalties": len(attendances_with_penalties) > 0,
            "has_attendances": True,
            "penalties": penalties,
            "attendances_with_penalties": attendances_with_penalties,
            "attendances_without_penalties": attendances_without_penalties,
            "employees_data": employees_data,
            "total_employees": total_employees,
            "total_attendances": len(penalties),
            "total_penalty_attendances": len(attendances_with_penalties),
            "total_normal_attendances": len(attendances_without_penalties),
            "total_penalty_minutes": total_penalty_minutes,
            "shift_type": shift_type,
            "from_date": from_date,
            "to_date": to_date
        }
        
    except Exception as e:
        frappe.log_error(f"Error checking new penalties: {str(e)}")
        return {"has_new_penalties": False, "error": str(e)}

@frappe.whitelist()
def create_penalty_management_records(shift_type, penalty_data, group_by_employee=True):
    """
    Créer les enregistrements Penalty Management
    """
    try:
        penalty_data = frappe.parse_json(penalty_data)
        group_by_employee = frappe.parse_json(group_by_employee)
        
        created_records = []
        
        if group_by_employee:
            # Créer un enregistrement par employé
            for employee_id, employee_data in penalty_data.get("employees_data", {}).items():
                penalty_mgmt = create_single_penalty_management(
                    employee_data["employee"],
                    employee_data["employee_name"],
                    penalty_data["from_date"],
                    penalty_data["to_date"],
                    employee_data["penalties"]
                )
                if penalty_mgmt:
                    created_records.append({
                        "name": penalty_mgmt.name,
                        "employee_name": employee_data["employee_name"],
                        "from_date": penalty_data["from_date"],
                        "to_date": penalty_data["to_date"]
                    })
        else:
            # Créer un enregistrement par jour/employé
            for penalty in penalty_data.get("penalties", []):
                penalty_mgmt = create_single_penalty_management(
                    penalty["employee"],
                    penalty["employee_name"],
                    penalty["attendance_date"],
                    penalty["attendance_date"],
                    [penalty]
                )
                if penalty_mgmt:
                    created_records.append({
                        "name": penalty_mgmt.name,
                        "employee_name": penalty["employee_name"],
                        "from_date": penalty["attendance_date"],
                        "to_date": penalty["attendance_date"]
                    })
        
        return {
            "success": True,
            "records_created": len(created_records),
            "created_records": created_records
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating penalty management records: {str(e)}")
        return {"success": False, "error": str(e)}

def create_single_penalty_management(employee, employee_name, from_date, to_date, penalties):
    """
    Créer un seul enregistrement Penalty Management
    """
    try:
        # Calculer les totaux
        total_late_penalty = sum(p.get("late_entry_penalty_minutes", 0) or 0 for p in penalties)
        total_early_penalty = sum(p.get("early_exit_penalty_minutes", 0) or 0 for p in penalties)
        total_penalty_minutes = total_late_penalty + total_early_penalty
        
        # Créer l'enregistrement principal
        penalty_mgmt = frappe.get_doc({
            "doctype": "penalty managment",
            "employee": employee,
            "from_date": from_date,
            "to_date": to_date,
            "total_late_penalty": total_late_penalty,
            "total_early_penalty": total_early_penalty,
            "total_penalty_minutes": total_penalty_minutes,
            "corrected_late_penalty": total_late_penalty,
            "corrected_early_penalty": total_early_penalty,
            "total_corrected_penalty": total_penalty_minutes,
            "correction_status": "Draft"
        })
        
        # Ajouter les détails des pénalités
        for penalty in penalties:
            penalty_detail = penalty_mgmt.append("penalty_details", {})
            penalty_detail.attendance_date = penalty.get("attendance_date")
            penalty_detail.attendance_name = penalty.get("attendance_name")
            penalty_detail.shift_type = penalty.get("shift_type")
            penalty_detail.status = penalty.get("status")
            penalty_detail.actual_late_minutes = penalty.get("total_late_minutes", 0)
            penalty_detail.actual_early_minutes = penalty.get("total_early_exit_minutes", 0)
            penalty_detail.original_late_penalty = penalty.get("late_entry_penalty_minutes", 0)
            penalty_detail.original_early_penalty = penalty.get("early_exit_penalty_minutes", 0)
            penalty_detail.corrected_late_penalty = penalty.get("late_entry_penalty_minutes", 0)
            penalty_detail.corrected_early_penalty = penalty.get("early_exit_penalty_minutes", 0)
            penalty_detail.period_applied = max(
                penalty.get("late_entry_period_applied", 0) or 0,
                penalty.get("early_exit_period_applied", 0) or 0
            )
            
            # Récupérer le coefficient utilisé
            if penalty_detail.period_applied > 0:
                shift_type_doc = frappe.get_doc("Shift Type", penalty.get("shift_type"))
                coefficient_field = f"coefficient_penalty_period_{penalty_detail.period_applied}"
                penalty_detail.coefficient_used = getattr(shift_type_doc, coefficient_field, 0)
            
            penalty_detail.is_corrected = 0
        
        penalty_mgmt.insert()
        
        return penalty_mgmt
        
    except Exception as e:
        frappe.log_error(f"Error creating single penalty management: {str(e)}")
        return None

@frappe.whitelist()
def load_penalties_for_period(employee, from_date, to_date, shift_type=None):
    """
    Charger les pénalités pour une période donnée
    """
    try:
        # Construire la requête SQL en fonction des paramètres
        conditions = [
            "employee = %s",
            "attendance_date BETWEEN %s AND %s",
            "docstatus = 1"
        ]
        params = [employee, from_date, to_date]
        
        if shift_type:
            conditions.append("shift_type = %s")
            params.append(shift_type)
        
        query = f"""
            SELECT 
                name as attendance_name,
                attendance_date,
                shift_type,
                status,
                in_time,
                out_time,
                COALESCE(total_late_minutes, 0) as total_late_minutes,
                COALESCE(total_early_exit_minutes, 0) as total_early_exit_minutes,
                COALESCE(late_entry_penalty_minutes, 0) as late_entry_penalty_minutes,
                COALESCE(early_exit_penalty_minutes, 0) as early_exit_penalty_minutes,
                COALESCE(late_entry_period_applied, 0) as late_entry_period_applied,
                COALESCE(early_exit_period_applied, 0) as early_exit_period_applied,
                COALESCE(applied_penalty_minutes, 0) as applied_penalty_minutes
            FROM `tabAttendance`
            WHERE {' AND '.join(conditions)}
            ORDER BY attendance_date
        """
        
        penalties = frappe.db.sql(query, tuple(params), as_dict=True)
        
        # Enrichir avec les coefficients utilisés
        for penalty in penalties:
            if penalty.shift_type:
                shift_type_doc = frappe.get_doc("Shift Type", penalty.shift_type)
                period_applied = max(
                    penalty.late_entry_period_applied or 0,
                    penalty.early_exit_period_applied or 0
                )
                if period_applied > 0:
                    coefficient_field = f"coefficient_penalty_period_{period_applied}"
                    penalty.coefficient_used = getattr(shift_type_doc, coefficient_field, 0)
                else:
                    penalty.coefficient_used = 0
        
        # Séparer les attendances avec et sans pénalités
        attendances_with_penalties = [p for p in penalties if (p.late_entry_penalty_minutes > 0 or p.early_exit_penalty_minutes > 0)]
        attendances_without_penalties = [p for p in penalties if (p.late_entry_penalty_minutes == 0 and p.early_exit_penalty_minutes == 0)]
        
        return {
            "success": True,
            "penalties": penalties,
            "attendances_with_penalties": attendances_with_penalties,
            "attendances_without_penalties": attendances_without_penalties,
            "total_records": len(penalties),
            "total_penalty_records": len(attendances_with_penalties),
            "total_normal_records": len(attendances_without_penalties),
            "summary": {
                "total_late_penalty": sum(p.late_entry_penalty_minutes or 0 for p in penalties),
                "total_early_penalty": sum(p.early_exit_penalty_minutes or 0 for p in penalties),
                "total_penalty_minutes": sum(p.applied_penalty_minutes or 0 for p in penalties),
                "total_attendances": len(penalties),
                "penalty_attendances": len(attendances_with_penalties),
                "normal_attendances": len(attendances_without_penalties)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error loading penalties: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def recalculate_penalty_management(doc_name):
    """
    Recalculer les totaux d'un Penalty Management
    """
    try:
        penalty_mgmt = frappe.get_doc("penalty managment", doc_name)
        
        # Recalculer les totaux à partir des détails
        total_late = sum(d.corrected_late_penalty or 0 for d in penalty_mgmt.penalty_details)
        total_early = sum(d.corrected_early_penalty or 0 for d in penalty_mgmt.penalty_details)
        
        penalty_mgmt.corrected_late_penalty = total_late
        penalty_mgmt.corrected_early_penalty = total_early
        penalty_mgmt.total_corrected_penalty = total_late + total_early
        
        penalty_mgmt.save()
        
        return {
            "success": True,
            "message": "Penalty Management recalculated successfully",
            "totals": {
                "corrected_late_penalty": total_late,
                "corrected_early_penalty": total_early,
                "total_corrected_penalty": total_late + total_early
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error recalculating penalty management: {str(e)}")
        return {"success": False, "error": str(e)}
