# Copyright (c) 2025, ard and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import os

class RequestLawyerRenewal(Document):

    def on_update(self):
        # التحقق من أن الحالة Completed ولم يتم إرسال البريد
        if self.status == "Completed" and not self.get("completed_email_send"):
            self.send_completion_email()

    def send_completion_email(self):
        """Send completion email with attachments"""
        try:
            attachments = self.get_attachments()
            
            if not self.email:
                frappe.msgprint("No email address specified. Email not sent.")
                return

            frappe.msgprint(f"Preparing to send email to: {self.email}")

            # الحصول على محتوى البريد
            email_content = self.get_email_content()
            
            # إرسال البريد
            frappe.sendmail(
                recipients=[self.email],
                subject=email_content["subject"],
                message=email_content["message"],
                attachments=attachments,
                reference_doctype=self.doctype,
                reference_name=self.name,
                
            )

            # تعليم الوثيقة أن البريد تم إرساله
            self.db_set("completed_email_send", 1)
            frappe.msgprint("Completion email sent successfully.")

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error sending completion email")
            frappe.msgprint(f"Error sending email: {str(e)}")

    def get_email_content(self):
        """Get email content - try template first, then default"""
        template_name = "Lawyer Renewal Notification"
        
        # محاولة استخدام الـ template إذا كان موجوداً
        if frappe.db.exists("Email Template", template_name):
            try:
                template = frappe.get_doc("Email Template", template_name)
                context = self.as_dict()
                
                # معالجة الـ subject والـ message مع المتغيرات
                subject = frappe.render_template(template.subject, context)
                message = frappe.render_template(template.response, context)
                
                return {"subject": subject, "message": message}
                
            except Exception as e:
                frappe.msgprint(f"Error using email template: {str(e)}")
                # الاستمرار بالمحتوى الافتراضي إذا فشل Template
        
        # استخدام المحتوى الافتراضي
        return self.get_default_email_content()

    def get_default_email_content(self):
        """Get default email content"""
        subject = f"Renewal Completed - {self.name}"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2e5bff;">Renewal Request Completed</h2>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Request Number:</strong> {self.name}</p>
                <p><strong>Lawyer:</strong> {self.lawyer}</p>
                <p><strong>Status:</strong> {self.status}</p>
                <p><strong>Completion Date:</strong> {frappe.utils.nowdate()}</p>
            </div>
            
            <p>Dear Legal Team,</p>
            
            <p>The renewal request for <strong>{self.lawyer}</strong> has been successfully completed.</p>
            
            <p>All required documents have been processed and attached to this email.</p>
            
            <div style="margin-top: 30px; padding: 15px; background: #e8f5e8; border-radius: 5px;">
                <p style="margin: 0;">📎 <strong>Attachments included:</strong></p>
                <ul>
                    {"".join([f'<li>{row.attach}</li>' for row in self.fulfilment_checklist if row.attach])}
                    {f'<li>Final Document: {self.final_document}</li>' if self.final_document else ''}
                </ul>
            </div>
            <!-- Button to Web Form -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://23.88.43.154:8011/final_document/{self.name}" 
               style="background:#1a73e8;color:#fff;padding:12px 25px;
                      text-decoration:none;border-radius:6px;display:inline-block;font-weight:bold;"
               target="_blank">
                📄 Submit Final Attachment
            </a>
        </div>
            
            <br>
            <p>Best regards,<br>
            <strong>Legal Administration System</strong></p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #666; font-size: 12px; text-align: center;">
                This is an automated message. Please do not reply to this email.
            </p>
        </div>
        """
        
        return {"subject": subject, "message": message}

    def get_attachments(self):
        """Get all attachments from fulfilment_checklist and final_document"""
        attachments = []
        
        # جمع المرفقات من الجدول الفرعي
        for row in self.fulfilment_checklist:
            if row.get("attach"):
                file_path = self.get_file_path(row.attach)
                if file_path:
                    try:
                        with open(file_path, "rb") as f:
                            attachments.append({
                                "fname": os.path.basename(file_path),
                                "fcontent": f.read()
                            })
                        frappe.msgprint(f"Attachment added: {os.path.basename(file_path)}")
                    except Exception as e:
                        frappe.msgprint(f"Failed to read file {file_path}: {str(e)}")
    
        # إضافة الوثيقة النهائية
        if self.get("final_document"):
            file_path = self.get_file_path(self.final_document)
            if file_path:
                try:
                    with open(file_path, "rb") as f:
                        attachments.append({
                            "fname": os.path.basename(file_path),
                            "fcontent": f.read()
                        })
                    frappe.msgprint(f"Final document attached: {os.path.basename(file_path)}")
                except Exception as e:
                    frappe.msgprint(f"Failed to read final document {file_path}: {str(e)}")
        
        return attachments

    def get_file_path(self, file_url_or_name):
        """Get absolute file path from file URL or name"""
        try:
            clean_url = file_url_or_name.strip()
            clean_url = clean_url.replace("//", "/")
            
            if clean_url.startswith('/files/'):
                relative_path = clean_url[7:]
                full_path = frappe.get_site_path('public', 'files', relative_path)
            elif clean_url.startswith('/private/files/'):
                relative_path = clean_url[15:]
                full_path = frappe.get_site_path('private', 'files', relative_path)
            else:
                file_name = os.path.basename(clean_url)
                file_docs = frappe.get_all("File", 
                                         filters={"file_name": file_name},
                                         fields=["is_private"])
                if file_docs:
                    if file_docs[0].is_private:
                        full_path = frappe.get_site_path('private', 'files', file_name)
                    else:
                        full_path = frappe.get_site_path('public', 'files', file_name)
                else:
                    return None

            return full_path if os.path.exists(full_path) else None
                
        except Exception as e:
            frappe.msgprint(f"Error accessing file {file_url_or_name}: {str(e)}")
            return None

    def validate(self):
        """Validation logic"""
        # if self.status == "Completed":
        #     frappe.throw("Final Document is required when status is Completed")
        if self.email and "@" not in self.email:
            frappe.throw("Please enter a valid email address")