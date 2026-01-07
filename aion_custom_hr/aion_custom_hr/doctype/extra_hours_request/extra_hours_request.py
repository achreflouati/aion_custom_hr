# Copyright (c) 2026, ard and contributors
# For license information, please see license.txt

# import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate
import frappe

class EXTRAHOURSREQUEST(Document):
	# def validate(self):
	# 	# التحقق من أن تاريخ البداية والنهاية ليسا في الماضي
	# 	today = getdate(nowdate())
	# 	from_date = getdate(self.from_datetime) if self.from_datetime else None
	# 	to_date = getdate(self.to_datetime) if self.to_datetime else None
	# 	if from_date and from_date < today:
	# 		frappe.throw(_("لا يمكن أن يكون تاريخ البداية أقدم من اليوم."))
	# 	if to_date and to_date < today:
	# 		frappe.throw(_("لا يمكن أن يكون تاريخ النهاية أقدم من اليوم."))
	# 	# التحقق أن البداية <= النهاية
	# 	if self.from_datetime and self.to_datetime:
	# 		if self.from_datetime > self.to_datetime:
	# 			frappe.throw(_("يجب أن يكون تاريخ البداية قبل أو يساوي تاريخ النهاية."))
	pass

def notify_manager_on_extra_hours(doc, method=None):
	if doc.reason in ('Extra Hours', 'Surplus'):
		reports_to = frappe.db.get_value('Employee', doc.employee, 'reports_to')
		if reports_to:
			manager_user = frappe.db.get_value('Employee', reports_to, 'user_id')
			if manager_user:
				link = frappe.utils.get_url_to_form(doc.doctype, doc.name)
				button = f"<a href='{link}' style='background:#4CAF50;color:white;padding:8px 16px;text-decoration:none;border-radius:4px;'>عرض الطلب</a>"
				msg = f"<p>الموظف <b>{doc.employee_name}</b> قدم طلب ساعات إضافية من <b>{doc.from_datetime}</b> إلى <b>{doc.to_datetime}</b> لمدة <b>{doc.nb_minutes_extra} دقيقة</b>.</p>{button}"
				frappe.sendmail(
					recipients=[manager_user],
					subject="طلب ساعات إضافية جديد",
					message=msg,
					delayed=False
				)
				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": "طلب ساعات إضافية جديد",
					"email_content": msg,
					"for_user": manager_user,
					"document_type": doc.doctype,
					"document_name": doc.name,
					"type": "Alert"
				}).insert(ignore_permissions=True)
			else:
				frappe.log_error(f"مدير الموظف {doc.employee} ليس لديه حساب مستخدم.", "إشعار ساعات إضافية")
				frappe.throw(_("مدير الموظف ليس لديه حساب مستخدم."))
		else:
			frappe.log_error(f"الموظف {doc.employee} ليس لديه مدير معين.", "إشعار ساعات إضافية")
			frappe.throw(_("الموظف ليس لديه مدير معين."))

def notify_employee_on_state_change(doc, method=None):
	if doc.reason in ('Extra Hours', 'Surplus'):
		employee_user = frappe.db.get_value('Employee', doc.employee, 'user_id')
		if not employee_user:
			return
		link = frappe.utils.get_url_to_form(doc.doctype, doc.name)
		button = f"<a href='{link}' style='background:#4CAF50;color:white;padding:8px 16px;text-decoration:none;border-radius:4px;'>عرض الطلب</a>"
		if getattr(doc, 'workflow_state', None) == 'Approved':
			msg = f"<p>تمت الموافقة على طلب الساعات الإضافية من <b>{doc.from_datetime}</b> إلى <b>{doc.to_datetime}</b>.</p>{button}"
			frappe.sendmail(
				recipients=[employee_user],
				subject="تمت الموافقة على طلب الساعات الإضافية",
				message=msg,
				delayed=False
			)
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": "تمت الموافقة على طلب الساعات الإضافية",
				"email_content": msg,
				"for_user": employee_user,
				"document_type": doc.doctype,
				"document_name": doc.name,
				"type": "Alert"
			}).insert(ignore_permissions=True)
		elif getattr(doc, 'workflow_state', None) == 'Rejected':
			msg = f"<p>تم رفض طلب الساعات الإضافية من <b>{doc.from_datetime}</b> إلى <b>{doc.to_datetime}</b>.</p>{button}"
			frappe.sendmail(
				recipients=[employee_user],
				subject="تم رفض طلب الساعات الإضافية",
				message=msg,
				delayed=False
			)
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": "تم رفض طلب الساعات الإضافية",
				"email_content": msg,
				"for_user": employee_user,
				"document_type": doc.doctype,
				"document_name": doc.name,
				"type": "Alert"
			}).insert(ignore_permissions=True)
