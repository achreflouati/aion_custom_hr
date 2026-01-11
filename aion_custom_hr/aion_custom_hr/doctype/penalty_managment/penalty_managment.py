
# Copyright (c) 2025, ard and contributors
# For license information, please see license.txt





import frappe
from frappe.model.document import Document
from aion_custom_hr.api.penalty_management import load_penalties_for_period

class penaltymanagment(Document):
	pass



@frappe.whitelist()
def notify_report_to_on_justification(penalty_docname, row_idx, correction_note):
	"""
	إرسال بريد إلكتروني إلى المسؤول المباشر عند تبرير عقوبة في سطر التفاصيل.
	"""
	doc = frappe.get_doc("penalty managment", penalty_docname)
	employee = doc.employee
	emp_doc = frappe.get_doc("Employee", employee)
	report_to = getattr(emp_doc, "reports_to", None)
	if not report_to:
		frappe.msgprint("هذا الموظف ليس لديه مسؤول مباشر محدد. يرجى التواصل مع قسم الموارد البشرية.")
		return
	report_to_user = frappe.get_value("Employee", report_to, "user_id")
	if not report_to_user:
		frappe.msgprint("المسؤول المباشر لا يملك حساب مستخدم مرتبط. يرجى التواصل مع قسم الموارد البشرية.")
		return
	# استرجاع السطر المعني
	try:
		idx = int(row_idx) - 1
		row = doc.penalty_details[idx]
	except (IndexError, ValueError, TypeError):
		frappe.msgprint("لم يتم العثور على سطر العقوبة المحدد.")
		return
	doc_url = frappe.utils.get_url_to_form("penalty managment", penalty_docname)
	subject = f"تبرير عقوبة للموظف {emp_doc.employee_name} ({employee})"
	message = f"مرحباً،<br>تم إدخال تبرير للعقوبة التالية:<br>"
	message += f"<b>التاريخ:</b> {row.attendance_date}<br>"
	message += f"<b>نوع الوردية:</b> {row.shift_type}<br>"
	message += f"<b>الحالة:</b> {row.status}<br>"
	message += f"<b>دقائق التأخير الأصلية:</b> {row.original_late_penalty} دقيقة<br>"
	message += f"<b>دقائق الخروج المبكر الأصلية:</b> {row.original_early_penalty} دقيقة<br>"
	message += f"<b>التبرير:</b> {correction_note}<br>"
	message += f"<a href='{doc_url}' style='display:inline-block;padding:10px 20px;background:#28a745;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:10px;'>عرض الوثيقة</a>"
	frappe.sendmail(
		recipients=[report_to_user],
		subject=subject,
		message=message,
		delayed=False
	)
	frappe.msgprint(f"تم إرسال بريد إلكتروني إلى المسؤول المباشر ({report_to_user}) بالتبرير.")


	
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
			print(f"\n==== Employé: {emp_doc.employee_name} ({emp}) ====")
			print("penalties_result (résultat brut):")
			import pprint
			pprint.pprint(penalties_result)
			# On veut maintenant insérer toutes les attendances, pas seulement celles avec pénalité
			penalties = penalties_result.get("penalties") if isinstance(penalties_result, dict) else []
			print("penalties (à insérer dans penalty_details):")
			pprint.pprint(penalties)
			if penalties and len(penalties) > 0:
				# Vérifier si un doc penalty managment existe déjà pour cet employé et cette période
				existing_docs = frappe.get_all(
					"penalty managment",
					filters={
						"employee": emp,
						"from_date": from_date,
						"to_date": to_date
					},
					pluck="name"
				)
				if existing_docs:
					doc = frappe.get_doc("penalty managment", existing_docs[0])
					# Récupérer les attendances déjà présentes dans la child table
					existing_attendance_names = set([d.attendance_name for d in doc.penalty_details])
					new_count = 0
					for penalty in penalties:
						if penalty.get("attendance_name") not in existing_attendance_names:
							detail = doc.append("penalty_details", {})
							detail.attendance_date = penalty.get("attendance_date")
							detail.attendance_name = penalty.get("attendance_name")
							detail.shift_type = penalty.get("shift_type")
							detail.status = penalty.get("status")
							detail.status_justification = "Pending"
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
							new_count += 1
					if new_count > 0:
						# Recalculer les totaux après ajout de nouvelles lignes
						total_late = sum(d.corrected_late_penalty or 0 for d in doc.penalty_details)
						total_early = sum(d.corrected_early_penalty or 0 for d in doc.penalty_details)
						doc.corrected_late_penalty = total_late
						doc.corrected_early_penalty = total_early
						doc.total_corrected_penalty = total_late + total_early
						doc.save()
					created.append(emp)
				else:
					doc = frappe.get_doc({
						"doctype": "penalty managment",
						"employee": emp,
						"from_date": from_date,
						"to_date": to_date,
						"default_shift": shift_type,
						"docstatus": 0
					})
					for penalty in penalties:
						detail = doc.append("penalty_details", {})
						detail.attendance_date = penalty.get("attendance_date")
						detail.attendance_name = penalty.get("attendance_name")
						detail.shift_type = penalty.get("shift_type")
						detail.status = penalty.get("status")
						detail.status_justification = "Pending"
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
