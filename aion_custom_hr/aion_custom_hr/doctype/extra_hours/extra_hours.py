# Copyright (c) 2025, ard and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class ExtraHours(Document):
	pass


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