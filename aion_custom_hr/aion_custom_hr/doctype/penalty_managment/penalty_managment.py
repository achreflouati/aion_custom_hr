# Copyright (c) 2025, ard and contributors
# For license information, please see license.txt





import frappe
from frappe.model.document import Document
from aion_custom_hr.api.penalty_management import load_penalties_for_period

class penaltymanagment(Document):
	pass

@frappe.whitelist()
def bulk_create_penalty_managment(employees, from_date, to_date):
	"""
	Crée en masse des documents Penalty Managment pour une liste d'employés, avec gestion du shift_type.
	Retourne la liste des créés et la liste des employés sans shift_type.
	"""
	employees = frappe.parse_json(employees)
	created = []
	without_shift = []
	without_penalty = []
	for emp in employees:
		emp_doc = frappe.get_doc("Employee", emp)
		shift_type = getattr(emp_doc, "default_shift", None)
		if shift_type:
			# Charger les pénalités pour la période
			penalties_result = load_penalties_for_period(emp, from_date, to_date, shift_type=None)
			
			# Si la fonction retourne un dict, extraire les pénalités
			penalties = penalties_result.get("attendances_with_penalties") if isinstance(penalties_result, dict) else []
			
			if penalties and len(penalties) > 0:
				doc = frappe.get_doc({
					"doctype": "penalty managment",
					"employee": emp,
					"from_date": from_date,
					"to_date": to_date,
					"default_shift": shift_type,
					"docstatus": 0
				})
				# Ajouter les pénalités dans la child table si elle existe
				for penalty in penalties:
					detail = doc.append("penalty_details", {})
					detail.attendance_date = penalty.get("attendance_date")
					detail.attendance_name = penalty.get("attendance_name")
					detail.shift_type = penalty.get("shift_type")
					detail.status = penalty.get("status")
					detail.actual_late_minutes = penalty.get("total_late_minutes", 0)
					detail.actual_early_minutes = penalty.get("total_early_exit_minutes", 0)
					detail.original_late_penalty = penalty.get("late_entry_penalty_minutes", 0)
					detail.original_early_penalty = penalty.get("early_exit_penalty_minutes", 0)
					detail.corrected_late_penalty = penalty.get("late_entry_penalty_minutes", 0)
					detail.corrected_early_penalty = penalty.get("early_exit_penalty_minutes", 0)
					detail.period_applied = max(
						penalty.get("late_entry_period_applied", 0) or 0,
						penalty.get("early_exit_period_applied", 0) or 0
					)
					detail.is_corrected = 0
				doc.insert()
				created.append(emp)
			else:
				without_penalty.append(emp_doc.employee_name + " (" + emp + ")")
		else:
			without_shift.append(emp_doc.employee_name + " (" + emp + ")")
	frappe.db.commit()
	return {
		"created": created,
		"without_shift": without_shift,
		"without_penalty": without_penalty,
		"success": True
	}
