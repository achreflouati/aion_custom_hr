import frappe
from frappe.utils import now_datetime

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


def scheduled_auto_attendance_and_extra_hours():
    auto_mark_attendance_for_enabled_shifts()
    create_extra_hours_requests_from_attendance()

