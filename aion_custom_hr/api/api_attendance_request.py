# API pour Attendance Request : notifications et workflow personnalisés
import frappe
from frappe import _

def notify_manager_on_late(doc, method=None):
    if doc.reason == 'Late':
        reports_to = frappe.db.get_value('Employee', doc.employee, 'reports_to')
        if reports_to:
            manager_user = frappe.db.get_value('Employee', reports_to, 'user_id')
            if manager_user:
                link = frappe.utils.get_url_to_form(doc.doctype, doc.name)
                button = f"<a href='{link}' style='background:#4CAF50;color:white;padding:8px 16px;text-decoration:none;border-radius:4px;'>فتح الطلب</a>"
                msg_ar = f"<p>الموظف <b>{doc.employee_name}</b> قدم طلب تأخير من <b>{doc.from_date}</b> إلى <b>{doc.to_date}</b>.</p>{button}"
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
            msg_ar = f"<p>تمت الموافقة على طلب التأخير من <b>{doc.from_date}</b> إلى <b>{doc.to_date}</b>.</p>{button}"
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
            msg_ar = f"<p>تم رفض طلب التأخير من <b>{doc.from_date}</b> إلى <b>{doc.to_date}</b>.</p>{button}"
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

