# Copyright (c) 2025, ard and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document



class ExtraHours(Document):
    pass


# @frappe.whitelist()
# def approve_extra_hours_justification(extra_hours_name, attendance_name):
#     """
#     Approuve une justification d'heures supplémentaires pour une ligne spécifique
#     """
#     try:
#         extra_hours_doc = frappe.get_doc("Extra Hours", extra_hours_name)
#         found = False
#         for detail in extra_hours_doc.extra_hours_details:
#             if detail.attendance_name == attendance_name:
#                 detail.status = "Approved"
#                 found = True
#         if not found:
#             return {"success": False, "message": f"Attendance {attendance_name} not found in Extra Hours {extra_hours_name}"}
#         # Recalculer le total des heures approuvées
#         total_approved = 0
#         for detail in extra_hours_doc.extra_hours_details:
#             if detail.status == "Approved":
#                 total_approved += detail.approved_extra_hours or 0
#         extra_hours_doc.total_approved_extra_hours = round(total_approved, 2)
#         extra_hours_doc.save()
#         frappe.db.commit()
#         return {"success": True, "message": f"Justification for {attendance_name} approved in Extra Hours {extra_hours_name}"}
#     except Exception as e:
#         frappe.log_error(f"Error approving justification: {str(e)}")
#         return {"success": False, "message": f"Error: {str(e)}"}


@frappe.whitelist()
def get_approved_extra_hours_justifications(employee, from_date, to_date):
    """
    Retourne toutes les demandes d'heures supplémentaires approuvées pour un employé et une période donnée.
    """
    try:
        justifications = frappe.db.get_all(
            "EXTRA HOURS REQUEST",
            filters={
                "employee": employee,
                "from_datetime": [">=", from_date],
                "to_datetime": ["<=", to_date],
                "workflow_state": "Approved"
            },
            fields=["name", "from_datetime", "nb_minutes_extra"]
        )
        result = []
        for j in justifications:
            result.append({
                "date": str(j.from_datetime.date()),
                "extra_minutes": j.nb_minutes_extra or 0,
                "name": j.name
            })
        return {"success": True, "justifications": result}
    except Exception as e:
        frappe.log_error(f"Error fetching extra hours justifications: {str(e)}")
        return {"success": False, "error": str(e)}