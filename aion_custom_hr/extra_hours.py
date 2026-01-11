import frappe
from frappe import _
from datetime import datetime, timedelta

# Envoi d'un mail au responsable lors de la justification
@frappe.whitelist()
def send_extra_hours_justification_mail(employee, docname, justification):
    """
    Envoie un mail au responsable (report_to) pour valider l'extra hours après justification de l'employé.
    """
    try:
        # Récupérer le responsable (report_to) de l'employé
        report_to = frappe.get_value("Employee", employee, "reports_to")
        if not report_to:
            return {"success": False, "message": "لا يوجد مسؤول مباشر معرف لهذا الموظف."}
        # Récupérer l'email du responsable
        report_to_user = frappe.get_value("Employee", report_to, "user_id")
        if not report_to_user:
            return {"success": False, "message": "المسؤول المباشر لا يملك حساب مستخدم مرتبط."}
        # Récupérer le nom de l'employé
        employee_name = frappe.get_value("Employee", employee, "employee_name")
        # Lien vers le document
        doc_url = frappe.utils.get_url_to_form("Extra Hours", docname)
        subject = f"يرجى التحقق من ساعات العمل الإضافية للموظف {employee_name}"
        message = (
            f"مرحباً،<br>قام الموظف <b>{employee_name}</b> بتعبئة تبرير لساعات العمل الإضافية.<br>"
            f"التبرير: <b>{justification}</b><br>"
            "يرجى الدخول على الرابط أدناه لمراجعة وتأكيد أو رفض هذه الساعات:<br>"
            f"<a href='{doc_url}' style='display:inline-block;padding:10px 20px;background:#28a745;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:10px;'>عرض الوثيقة</a>"
        )
        frappe.sendmail(
            recipients=[report_to_user],
            subject=subject,
            message=message,
            delayed=False
        )
        return {"success": True}
    except Exception as e:
        frappe.log_error(f"Erreur envoi mail justification extra hours: {str(e)}")
        return {"success": False, "message": str(e)}
import frappe
from frappe import _
from datetime import datetime, timedelta


@frappe.whitelist()
def load_extra_hours_for_period(employee, from_date, to_date):
    """Charger les attendances pour la période et calculer les heures supplémentaires"""
    
    # Récupérer toutes les attendances pour la période
    attendances = frappe.db.sql("""
        SELECT 
            a.name,
            a.attendance_date,
            a.employee,
            a.shift,
            a.status,
            a.in_time,
            a.out_time,
            st.name as shift_type,
            st.start_time,
            st.end_time,
            TIME_TO_SEC(st.end_time) - TIME_TO_SEC(st.start_time) as standard_seconds
        FROM `tabAttendance` a
        LEFT JOIN `tabShift Type` st ON a.shift = st.name
        WHERE a.employee = %s 
        AND a.attendance_date BETWEEN %s AND %s
        AND a.status = 'Present'
        AND a.in_time IS NOT NULL 
        AND a.out_time IS NOT NULL
        ORDER BY a.attendance_date DESC
    """, (employee, from_date, to_date), as_dict=True)
    
    extra_hours_data = []
    
    for attendance in attendances:
        if not attendance.shift_type:
            continue
            
        # Calculer les heures travaillées
        worked_seconds = calculate_worked_seconds(attendance.in_time, attendance.out_time)
        worked_hours = worked_seconds / 3600.0
        
        # Calculer les heures standard
        standard_hours = attendance.standard_seconds / 3600.0 if attendance.standard_seconds else 8.0
        
        # Calculer les heures supplémentaires
        extra_hours = max(0, worked_hours - standard_hours)
        
        extra_hours_data.append({
            'attendance_date': attendance.attendance_date,
            'attendance_name': attendance.name,
            'shift_type': attendance.shift_type,
            'check_in': attendance.in_time,
            'check_out': attendance.out_time,
            'worked_hours': round(worked_hours, 2),
            'standard_hours': round(standard_hours, 2),
            'extra_hours': round(extra_hours, 2),
            'approved_extra_hours': round(extra_hours, 2),  # Par défaut, approuvé = calculé
            'status': 'Pending',
            'comments': ''
        })
    
    return extra_hours_data


@frappe.whitelist()
def create_extra_hours_record(employee, from_date, to_date, extra_hours_details):
    """Créer un nouvel enregistrement Extra Hours"""
    
    try:
        # Convertir extra_hours_details en liste si c'est une chaîne JSON
        if isinstance(extra_hours_details, str):
            import json
            extra_hours_details = json.loads(extra_hours_details)
        
        # Créer le document Extra Hours
        extra_hours_doc = frappe.new_doc("Extra Hours")
        extra_hours_doc.employee = employee
        extra_hours_doc.from_date = from_date
        extra_hours_doc.to_date = to_date
        extra_hours_doc.approval_status = "Draft"
        
        # Calculer les totaux
        total_worked_hours = 0
        total_standard_hours = 0
        total_extra_hours = 0
        total_approved_extra_hours = 0
        
        # Ajouter les détails
        for detail in extra_hours_details:
            extra_hours_doc.append("extra_hours_details", {
                "attendance_date": detail.get("attendance_date"),
                "attendance_name": detail.get("attendance_name"),
                "shift_type": detail.get("shift_type"),
                "check_in": detail.get("check_in"),
                "check_out": detail.get("check_out"),
                "worked_hours": detail.get("worked_hours", 0),
                "standard_hours": detail.get("standard_hours", 0),
                "extra_hours": detail.get("extra_hours", 0),
                "approved_extra_hours": detail.get("approved_extra_hours", 0),
                "status": detail.get("status", "Pending"),
                "comments": detail.get("comments", "")
            })
            
            # Calculer les totaux
            total_worked_hours += detail.get("worked_hours", 0)
            total_standard_hours += detail.get("standard_hours", 0)
            total_extra_hours += detail.get("extra_hours", 0)
            total_approved_extra_hours += detail.get("approved_extra_hours", 0)
        
        # Mettre à jour les totaux
        extra_hours_doc.total_worked_hours = round(total_worked_hours, 2)
        extra_hours_doc.total_standard_hours = round(total_standard_hours, 2)
        extra_hours_doc.total_extra_hours = round(total_extra_hours, 2)
        extra_hours_doc.total_approved_extra_hours = round(total_approved_extra_hours, 2)
        
        # Sauvegarder le document
        extra_hours_doc.insert()
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Extra Hours record created successfully: {extra_hours_doc.name}",
            "name": extra_hours_doc.name
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating Extra Hours record: {str(e)}")
        return {
            "success": False,
            "message": f"Error creating Extra Hours record: {str(e)}"
        }


@frappe.whitelist()
def approve_extra_hours(extra_hours_name, approval_status, approval_comments=""):
    """Approuver ou rejeter un enregistrement Extra Hours"""
    
    try:
        extra_hours_doc = frappe.get_doc("Extra Hours", extra_hours_name)
        
        # Mettre à jour le statut d'approbation
        extra_hours_doc.approval_status = approval_status
        extra_hours_doc.approved_by = frappe.session.user
        extra_hours_doc.approval_date = frappe.utils.now()
        extra_hours_doc.approval_comments = approval_comments
        
        # Si approuvé, mettre à jour le total des heures approuvées
        if approval_status == "Approved":
            total_approved = 0
            for detail in extra_hours_doc.extra_hours_details:
                if detail.status == "Approved":
                    total_approved += detail.approved_extra_hours or 0
            extra_hours_doc.total_approved_extra_hours = round(total_approved, 2)
        elif approval_status == "Rejected":
            extra_hours_doc.total_approved_extra_hours = 0
        
        extra_hours_doc.save()
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Extra Hours {approval_status.lower()} successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error approving Extra Hours: {str(e)}")
        return {
            "success": False,
            "message": f"Error approving Extra Hours: {str(e)}"
        }


@frappe.whitelist()
def get_approved_extra_hours_for_salary_slip(employee, start_date, end_date):
    """Récupérer les heures الإضافية approuvées pour le salary slip"""
    
    approved_extra_hours = frappe.db.sql("""
        SELECT SUM(eh.total_approved_extra_hours) as total_approved_hours
        FROM `tabExtra Hours` eh
        WHERE eh.employee = %s
        AND eh.approval_status = 'Approved'
        AND eh.from_date >= %s
        AND eh.to_date <= %s
    """, (employee, start_date, end_date), as_dict=True)
    
    return approved_extra_hours[0].total_approved_hours or 0 if approved_extra_hours else 0


def calculate_worked_seconds(in_time, out_time):
    """Calculer les secondes travaillées entre deux horaires"""
    if not in_time or not out_time:
        return 0
    
    # Convertir en datetime si ce sont des strings
    if isinstance(in_time, str):
        in_time = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
    if isinstance(out_time, str):
        out_time = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
    
    # Calculer la différence
    time_diff = out_time - in_time
    return time_diff.total_seconds()


# Hook pour recalculer les totaux quand les détails changent
def update_extra_hours_totals(doc, method):
    """Hook pour recalculer les totaux automatiquement"""
    if doc.doctype == "Extra Hours":
        total_worked_hours = 0
        total_standard_hours = 0
        total_extra_hours = 0
        total_approved_extra_hours = 0
        
        for detail in doc.extra_hours_details:
            total_worked_hours += detail.worked_hours or 0
            total_standard_hours += detail.standard_hours or 0
            total_extra_hours += detail.extra_hours or 0
            if detail.status == "Approved":
                total_approved_extra_hours += detail.approved_extra_hours or 0
        
        doc.total_worked_hours = round(total_worked_hours, 2)
        doc.total_standard_hours = round(total_standard_hours, 2)
        doc.total_extra_hours = round(total_extra_hours, 2)
        doc.total_approved_extra_hours = round(total_approved_extra_hours, 2)
