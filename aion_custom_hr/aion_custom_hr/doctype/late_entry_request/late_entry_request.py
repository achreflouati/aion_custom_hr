# Copyright (c) 2026, ard and contributors
# For license information, please see license.txt

# import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate
import frappe


class LateEntryRequest(Document):
	def validate(self):
		# Vérifier que from_datetime et to_datetime ne sont pas antérieurs à aujourd'hui
		today = getdate(nowdate())
		from_date = getdate(self.from_datetime) if self.from_datetime else None
		to_date = getdate(self.to_datetime) if self.to_datetime else None
		if from_date and from_date < today:
			frappe.throw(_("The start date cannot be earlier than today."))
		if to_date and to_date < today:
			frappe.throw(_("The end date cannot be earlier than today."))
		# Vérifier que from_datetime <= to_datetime
		if self.from_datetime and self.to_datetime:
			if self.from_datetime > self.to_datetime:
				frappe.throw(_("The start date must be earlier than or equal to the end date."))

def notify_manager_on_late(doc, method=None):
	if doc.reason == 'Late':
		reports_to = frappe.db.get_value('Employee', doc.employee, 'reports_to')
		if reports_to:
			manager_user = frappe.db.get_value('Employee', reports_to, 'user_id')
			if manager_user:
				link = frappe.utils.get_url_to_form(doc.doctype, doc.name)
				button = f"<a href='{link}' style='background:#4CAF50;color:white;padding:8px 16px;text-decoration:none;border-radius:4px;'>فتح الطلب</a>"
				msg_ar = f"<p>الموظف <b>{doc.employee_name}</b> قدم طلب تأخير من <b>{doc.from_datetime}</b> إلى <b>{doc.to_datetime}</b>.</p>{button}"
				frappe.sendmail(
					recipients=[manager_user],
					subject="طلب تأخير جديد",
					message=msg_ar,
					delayed=False
				)
				# Notification système
				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": "طلب تأخير جديد",
					"email_content": msg_ar,
					"for_user": manager_user,
					"document_type": doc.doctype,
					"document_name": doc.name,
					"type": "Alert"
				}).insert(ignore_permissions=True)
			else:
				frappe.log_error(f"مدير الموظف {doc.employee} ليس لديه حساب مستخدم مرتبط.", "إشعار طلب تأخير")
				frappe.throw(_("مدير الموظف ليس لديه حساب مستخدم مرتبط."))
		else:
			frappe.log_error(f"الموظف {doc.employee} ليس لديه مدير معين.", "إشعار طلب تأخير")
			frappe.throw(_("الموظف ليس لديه مدير معين."))

def notify_employee_on_state_change(doc, method=None):
	if doc.reason == 'Late':
		employee_user = frappe.db.get_value('Employee', doc.employee, 'user_id')
		if not employee_user:
			return
		link = frappe.utils.get_url_to_form(doc.doctype, doc.name)
		button = f"<a href='{link}' style='background:#4CAF50;color:white;padding:8px 16px;text-decoration:none;border-radius:4px;'>عرض الطلب</a>"
		if doc.workflow_state == 'Approved':
			msg_ar = f"<p>تمت الموافقة على طلب التأخير من <b>{doc.from_datetime}</b> إلى <b>{doc.to_datetime}</b>.</p>{button}"
			frappe.sendmail(
				recipients=[employee_user],
				subject="تمت الموافقة على طلب التأخير",
				message=msg_ar,
				delayed=False
			)
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": "تمت الموافقة على طلب التأخير",
				"email_content": msg_ar,
				"for_user": employee_user,
				"document_type": doc.doctype,
				"document_name": doc.name,
				"type": "Alert"
			}).insert(ignore_permissions=True)
		elif doc.workflow_state == 'Rejected':
			msg_ar = f"<p>تم رفض طلب التأخير من <b>{doc.from_datetime}</b> إلى <b>{doc.to_datetime}</b>.</p>{button}"
			frappe.sendmail(
				recipients=[employee_user],
				subject="تم رفض طلب التأخير",
				message=msg_ar,
				delayed=False
			)
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": "تم رفض طلب التأخير",
				"email_content": msg_ar,
				"for_user": employee_user,
				"document_type": doc.doctype,
				"document_name": doc.name,
				"type": "Alert"
			}).insert(ignore_permissions=True)
