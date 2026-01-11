# Création automatique des demandes de retard à partir des présences

import frappe

import calendar
from frappe.utils import getdate, nowdate, now_datetime
from aion_custom_hr.api.penalty_management import load_penalties_for_period
from aion_custom_hr.api.penalty_management import create_single_penalty_management
from aion_custom_hr.extra_hours import load_extra_hours_for_period

from frappe import _

@frappe.whitelist()
def auto_mark_attendance_for_enabled_shifts():
    """
    Liste tous les Shift Type, vérifie si enable_auto_attendance est activé,
    met à jour last_sync_of_checkin, lance le marquage d'attendance, et gère les erreurs.
    """
    try:
        shift_types = frappe.get_all("Shift Type", fields=["name", "enable_auto_attendance", "last_sync_of_checkin"])
        for shift in shift_types:
            if shift.get("enable_auto_attendance"):
                # Mettre à jour la date de synchronisation
                frappe.db.set_value("Shift Type", shift["name"], "last_sync_of_checkin", now_datetime())
                # Appeler la méthode process_auto_attendance sur le document Shift Type
                try:
                    shift_doc = frappe.get_doc("Shift Type", shift["name"])
                    shift_doc.process_auto_attendance()
                except Exception as e:
                    frappe.log_error(f"Erreur lors du marquage d'attendance pour le shift {shift['name']}: {str(e)}")
                    frappe.throw(f"Erreur lors du marquage d'attendance pour le shift {shift['name']}: {str(e)}")
        return "Auto attendance sync completed."
    except Exception as e:
        frappe.log_error(f"Erreur globale auto attendance: {str(e)}")
        frappe.throw(f"Erreur globale auto attendance: {str(e)}")


@frappe.whitelist()
def create_extra_hours_requests_from_attendance():
    """
    Parcourt toutes les présences, vérifie les extra hours, et crée un Extra Hours Request pour chaque employé concerné.
    """
    try:
        attendances = frappe.get_all(
            "Attendance",
            fields=["name", "employee", "attendance_date", "shift", "in_time", "out_time"],
            filters={"docstatus": 1}
        )
        created_requests = []
        for att in attendances:
            print("Processing attendance:", att["name"])
            # Récupérer la fin de shift
            shift_doc = frappe.get_doc("Shift Type", att.get("shift")) if att.get("shift") else None
            shift_end = None
            if shift_doc and hasattr(shift_doc, "end_time"):
                shift_end = shift_doc.end_time
            # Récupérer l'heure de sortie réelle
            out_time = att.get("out_time")
            print("Shift end time:", shift_end, "Out time:", out_time)
            extra_minutes = 0
            if shift_end and out_time:
                from datetime import datetime
                fmt = "%H:%M:%S"
                try:
                    # Extraire l'heure de out_time si c'est un datetime complet
                    out_time_str = str(out_time)
                    if len(out_time_str) > 8 and " " in out_time_str:
                        out_time_str = out_time_str.strip().split(" ")[-1]
                    shift_end_dt = datetime.strptime(str(shift_end), fmt)
                    out_time_dt = datetime.strptime(out_time_str, fmt)
                    delta = (out_time_dt - shift_end_dt).total_seconds() / 60
                    print("Calculated extra minutes:", delta)
                    if delta > 0:
                        extra_minutes = delta
                except Exception as e:
                    frappe.log_error(f"Erreur de calcul extra hours pour attendance {att['name']}: {str(e)}")
                    print(f"Erreur de parsing out_time pour attendance {att['name']}: {str(e)}")
            if extra_minutes > 0:
                # Vérifier si une demande existe déjà pour cette présence
                date_str = str(att["attendance_date"])
                from_dt = date_str + " " + str(shift_end) if shift_end else date_str + " 00:00:00"
                exists = frappe.get_all(
                    "EXTRA HOURS REQUEST",
                    filters={
                        "employee": att["employee"],
                        "shift": att.get("shift"),
                        "from_datetime": from_dt
                    }
                )
                if not exists:
                    # Si out_time contient déjà la date complète, on l'utilise tel quel, sinon on concatène
                    out_time_str = str(out_time)
                    if out_time_str and len(out_time_str) > 10 and out_time_str[4] == '-' and out_time_str[7] == '-':
                        to_dt = out_time_str
                    elif out_time_str:
                        to_dt = date_str + " " + out_time_str
                    else:
                        to_dt = date_str + " 00:00:00"
                    doc = frappe.get_doc({
                        "doctype": "EXTRA HOURS REQUEST",
                        "naming_series": "EXTRA-HRS-REQ-.YYYY.-.MM.-.#####",
                        "employee": att["employee"],
                        "shift": att.get("shift"),
                        "from_datetime": from_dt,
                        "to_datetime": to_dt,
                        "nb_minutes_extra": extra_minutes,
                        "reason": "Extra Hours"
                    })
                    doc.insert(ignore_permissions=True)
                    created_requests.append(doc.name)
        return {
            "created": created_requests,
            "message": f"{len(created_requests)} Extra Hours Requests created."
        }
    except Exception as e:
        frappe.log_error(f"Erreur lors de la création des Extra Hours Requests: {str(e)}")
        frappe.throw(f"Erreur lors de la création des Extra Hours Requests: {str(e)}")
# make_attendance.py
"""
Module for custom attendance creation logic in aion_custom_hr.
Add your attendance creation functions and utilities here.
"""
@frappe.whitelist()
def create_extra_hours():
    """
    Crée en masse les demandes d'heures supplémentaires pour tous les employés ayant des extra hours dans leurs présences validées.
    """
    
    
    today = getdate(nowdate())
    year = today.year
    month = today.month
    from_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    to_date = f"{year}-{month:02d}-{last_day:02d}"

    # Récupérer toutes les présences validées du mois
    attendances = frappe.get_all(
        "Attendance",
        fields=["name", "employee", "attendance_date", "shift", "in_time", "out_time", "shift_type"],
        filters={
            "attendance_date": ["between", [from_date, to_date]],
            "docstatus": 1
        }
    )
    # Grouper par employé
    from collections import defaultdict
    emp_attendance = defaultdict(list)
    for att in attendances:
        emp_attendance[att["employee"]].append(att)

    created_docs = []
    for emp in emp_attendance:
        # Utiliser la même logique que load_extra_hours_for_period
        details = load_extra_hours_for_period(emp, from_date, to_date)
        # Filtrer uniquement les lignes avec extra_hours > 0
        real_details = [d for d in details if d.get('extra_hours', 0) > 0]
        if real_details:
            doc = frappe.get_doc({
                "doctype": "Extra Hours",
                "employee": emp,
                "from_date": from_date,
                "to_date": to_date,
                "extra_hours_details": real_details
            })
            doc.insert(ignore_permissions=True)
            created_docs.append(doc.name)

            # Envoi d'email à l'employé
            user = frappe.get_value("Employee", emp, "user_id")
            if user:
                doc_url = frappe.utils.get_url_to_form("Extra Hours", doc.name)
                subject = "لديكم ساعات عمل إضافية - الرجاء الدخول وتقديم التبرير اللازم"
                # Construire la liste des jours avec heures supplémentaires
                days_list = "<ul>" + "".join([
                    f"<li>{d['attendance_date']} : {d['extra_hours']} ساعة إضافية</li>"
                    for d in real_details
                ]) + "</ul>"
                message = (
                    f"مرحباً،<br>تم تسجيل ساعات عمل إضافية لكم خلال الفترة من {from_date} إلى {to_date}.<br>"
                    f"الأيام المعنية:<br>{days_list}"
                    "نرجو منكم الدخول على الرابط أدناه وتقديم التبرير اللازم في أقرب وقت ممكن:<br>"
                    f"<a href='{doc_url}' style='display:inline-block;padding:10px 20px;background:#007bff;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:10px;'>عرض الوثيقة</a>"
                )
                frappe.sendmail(
                    recipients=[user],
                    subject=subject,
                    message=message,
                    delayed=False
                )
    return {
        "created": created_docs,
        "message": f"{len(created_docs)} Extra Hours docs created."
    }

@frappe.whitelist()
def create_late_entry_requests_from_attendance():
    """
    Parcourt toutes les présences, vérifie les retards, et crée un Late Entry Request pour chaque employé concerné.
    """
    try:
        attendances = frappe.get_all(
            "Attendance",
            fields=["name", "employee", "attendance_date", "shift", "in_time", "out_time"],
            filters={"docstatus": 1}
        )
        created_requests = []
        for att in attendances:
            # Récupérer le début de shift
            shift_doc = frappe.get_doc("Shift Type", att.get("shift")) if att.get("shift") else None
            shift_start = None
            if shift_doc and hasattr(shift_doc, "start_time"):
                shift_start = shift_doc.start_time
            in_time = att.get("in_time")
            late_minutes = 0
            if shift_start and in_time:
                from datetime import datetime
                fmt = "%H:%M:%S"
                try:
                    # Extraire l'heure de in_time si c'est un datetime complet
                    in_time_str = str(in_time)
                    if len(in_time_str) > 8 and " " in in_time_str:
                        in_time_str = in_time_str.strip().split(" ")[-1]
                    shift_start_dt = datetime.strptime(str(shift_start), fmt)
                    in_time_dt = datetime.strptime(in_time_str, fmt)
                    delta = (in_time_dt - shift_start_dt).total_seconds() / 60
                    if delta > 0:
                        late_minutes = delta
                except Exception as e:
                    frappe.log_error(f"Erreur de calcul late entry pour attendance {att['name']}: {str(e)}")
            if late_minutes > 0:
                # Vérifier si une demande existe déjà pour cette présence
                date_str = str(att["attendance_date"])
                from_dt = date_str + " " + str(shift_start) if shift_start else date_str + " 00:00:00"
                exists = frappe.get_all(
                    "Late Entry Request",
                    filters={
                        "employee": att["employee"],
                        "shift": att.get("shift"),
                        "from_datetime": from_dt
                    }
                )
                if not exists:
                    # Si in_time contient déjà la date complète, on l'utilise tel quel, sinon on concatène
                    in_time_str = str(in_time)
                    if in_time_str and len(in_time_str) > 10 and in_time_str[4] == '-' and in_time_str[7] == '-':
                        to_dt = in_time_str
                    elif in_time_str:
                        to_dt = date_str + " " + in_time_str
                    else:
                        to_dt = date_str + " 00:00:00"
                    doc = frappe.get_doc({
                        "doctype": "Late Entry Request",
                        "naming_series": "LATE-REQ-.YYYY.-.MM.-.#####",
                        "employee": att["employee"],
                        "shift": att.get("shift"),
                        "from_datetime": from_dt,
                        "to_datetime": to_dt,
                        "nb_hours_late": round(late_minutes / 60, 2),
                        "reason": "Late"
                    })
                    doc.insert(ignore_permissions=True)
                    created_requests.append(doc.name)
        return {
            "created": created_requests,
            "message": f"{len(created_requests)} Late Entry Requests created."
        }
    except Exception as e:
        frappe.log_error(f"Erreur lors de la création des Late Entry Requests: {str(e)}")
        frappe.throw(f"Erreur lors de la création des Late Entry Requests: {str(e)}")


from aion_custom_hr.aion_custom_hr.doctype.penalty_managment.penalty_managment import bulk_create_penalty_managment
@frappe.whitelist()
def create_penalty_management_from_attendance():
    """
    Pour chaque employé ayant une présence ce mois-ci, crée un document Penalty Management,
    puis envoie un email à l'employé avec le lien vers son document.
    La période est toujours le mois courant (du 1 au 31).
    """
    
    

    today = getdate(nowdate())
    year = today.year
    month = today.month
    from_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    to_date = f"{year}-{month:02d}-{last_day:02d}"

    # Récupérer tous les employés ayant une présence ce mois-ci
    attendances = frappe.get_all(
        "Attendance",
        fields=["employee"],
        filters={
            "attendance_date": ["between", [from_date, to_date]],
            "docstatus": 1
        },
        distinct=True
    )
    employees = list({a["employee"] for a in attendances if a.get("employee")})
    print("Employees with attendance this month:", employees)

    # Filtrer les employés qui n'ont PAS déjà un penalty managment pour la période
    employees_to_create = []
    for emp in employees:
        penalty_doc_names = frappe.get_all(
            "penalty managment",
            filters={
                "employee": emp,
                "from_date": from_date,
                "to_date": to_date
            },
            pluck="name"
        )
        # Charger toutes les attendances de la période pour l'employé
        penalties_result = load_penalties_for_period(emp, from_date, to_date, shift_type=None)
        penalties = penalties_result.get("penalties") if isinstance(penalties_result, dict) else []
        all_attendance_names = set([p.get("attendance_name") for p in penalties if p.get("attendance_name")])
        if not penalty_doc_names:
            # Aucun doc penalty managment, donc à créer
            employees_to_create.append(emp)
        else:
            # Doc existe, vérifier s'il manque des attendances dans la child table
            doc = frappe.get_doc("penalty managment", penalty_doc_names[0])
            existing_attendance_names = set([d.attendance_name for d in doc.penalty_details])
            missing_attendances = all_attendance_names - existing_attendance_names
            if missing_attendances:
                employees_to_create.append(emp)
    print("Employees to create or update penalty managment for (missing attendances):", employees_to_create)

    # Utiliser la méthode bulk_create_penalty_managment uniquement pour les nouveaux
    try:
        # Appel direct de la fonction importée
        result = bulk_create_penalty_managment(
            frappe.as_json(employees_to_create),
            from_date,
            to_date
        )
        print("Bulk create penalty management result:", result)
        # Logguer les employés sans shift pour analyse
        if result.get("without_shift"):
            frappe.log_error(
                title="employees without shift (bulk_create_penalty_managment)",
                message="\n".join(result["without_shift"])
            )
        if result.get("without_penalty"):
            frappe.log_error(
                title="Employees without penalties for the period (bulk_create_penalty_managment)",
                message="\n".join(result["without_penalty"])
            )
        # Envoi d'email à chaque employé pour lequel un document a été créé
        for emp in result.get("created", []):
            # Vérifier si un document existe déjà pour cet employé et cette période
            existing = frappe.get_all(
                "penalty managment",
                filters={
                    "employee": emp,
                    "from_date": from_date,
                    "to_date": to_date
                },
                pluck="name"
            )
            if not existing:
                continue
            doc = frappe.get_doc("penalty managment", existing[0])
            user = frappe.get_value("Employee", emp, "user_id")
            if user:
                # Filtrer uniquement les pénalités avec original_late_penalty ou original_early_penalty > 0
                penalty_rows = [
                    d for d in doc.penalty_details
                    if (
                        (d.creation and str(d.creation).startswith(f"{year}-{month:02d}")) and
                        ((d.original_late_penalty and d.original_late_penalty > 0) or (d.original_early_penalty and d.original_early_penalty > 0))
                    )
                ]
                if penalty_rows:
                    doc_url = frappe.utils.get_url_to_form("penalty managment", existing[0])
                    subject = _("نود إفادتكم بأنه تم تسجيل تأخير في وقت الحضور أو خروج مبكر من الدوام الرسمي وفقًا لسجلات نظام الحضور والانصراف.")
                    dates_list = "<ul>" + "".join([
                        f"<li>{d.attendance_date} (تأخير: {d.original_late_penalty} دقيقة، خروج مبكر: {d.original_early_penalty} دقيقة)</li>"
                        for d in penalty_rows
                    ]) + "</ul>"
                    message = _(f"مرحباً،<br>تم إضافة عقوبات جديدة للأيام التالية:<br>{dates_list}<br>"
                        "نرجو منكم التكرم بالدخول على الرابط أدناه وتقديم التبرير اللازم في أقرب وقت ممكن، وذلك لاستكمال الإجراءات المعتمدة حسب سياسات العمل المعمول بها:<br>"
                        f"<a href='{doc_url}' style='display:inline-block;padding:10px 20px;background:#28a745;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:10px;'>عرض الوثيقة</a>")
                    frappe.sendmail(
                        recipients=[user],
                        subject=subject,
                        message=message,
                        delayed=False
                    )
        return result
    except Exception as e:
        frappe.log_error(f"Erreur bulk_create_penalty_managment: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()  
def scheduled_auto_attendance_and_extra_hours():
    auto_mark_attendance_for_enabled_shifts()
    # create_extra_hours_requests_from_attendance()
    # create_late_entry_requests_from_attendance()
    create_penalty_management_from_attendance()
    create_extra_hours()

