import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_extra_hours_custom_fields():
    """Install custom fields for Extra Hours DocType"""
    
    # Lire et installer les custom fields pour Extra Hours Detail
    try:
        extra_hours_detail_fields = frappe.get_file_json(frappe.get_app_path("aion_custom_hr", "fixtures", "custom_field_extra_hours_detail.json"))
        
        for field in extra_hours_detail_fields:
            if not frappe.db.exists("Custom Field", field.get("name")):
                frappe.get_doc(field).insert()
                print(f"Installed custom field: {field.get('name')}")
            else:
                print(f"Custom field already exists: {field.get('name')}")
                
    except Exception as e:
        print(f"Error installing Extra Hours Detail custom fields: {e}")
    
    # Lire et installer les custom fields pour Extra Hours
    try:
        extra_hours_fields = frappe.get_file_json(frappe.get_app_path("aion_custom_hr", "fixtures", "custom_field_extra_hours.json"))
        
        for field in extra_hours_fields:
            if not frappe.db.exists("Custom Field", field.get("name")):
                frappe.get_doc(field).insert()
                print(f"Installed custom field: {field.get('name')}")
            else:
                print(f"Custom field already exists: {field.get('name')}")
                
    except Exception as e:
        print(f"Error installing Extra Hours custom fields: {e}")
    
    # Commit les changements
    frappe.db.commit()
    print("Extra Hours custom fields installation completed!")


def create_extra_hours_doctypes():
    """Create the Extra Hours and Extra Hours Detail DocTypes if they don't exist"""
    
    # Créer le DocType Extra Hours Detail
    if not frappe.db.exists("DocType", "Extra Hours Detail"):
        extra_hours_detail_doctype = {
            "doctype": "DocType",
            "name": "Extra Hours Detail",
            "module": "HR",
            "custom": 1,
            "istable": 1,
            "autoname": "hash",
            "fields": [
                {
                    "fieldname": "attendance_date",
                    "fieldtype": "Date",
                    "label": "Attendance Date",
                    "in_list_view": 1
                },
                {
                    "fieldname": "attendance_name",
                    "fieldtype": "Link",
                    "label": "Attendance",
                    "options": "Attendance"
                },
                {
                    "fieldname": "shift_type",
                    "fieldtype": "Link",
                    "label": "Shift Type",
                    "options": "Shift Type",
                    "in_list_view": 1
                },
                {
                    "fieldname": "check_in",
                    "fieldtype": "Datetime",
                    "label": "Check In"
                },
                {
                    "fieldname": "check_out",
                    "fieldtype": "Datetime",
                    "label": "Check Out"
                },
                {
                    "fieldname": "worked_hours",
                    "fieldtype": "Float",
                    "label": "Worked Hours",
                    "precision": 2,
                    "in_list_view": 1
                },
                {
                    "fieldname": "standard_hours",
                    "fieldtype": "Float",
                    "label": "Standard Hours",
                    "precision": 2
                },
                {
                    "fieldname": "extra_hours",
                    "fieldtype": "Float",
                    "label": "Extra Hours",
                    "precision": 2,
                    "in_list_view": 1
                },
                {
                    "fieldname": "approved_extra_hours",
                    "fieldtype": "Float",
                    "label": "Approved Extra Hours",
                    "precision": 2,
                    "in_list_view": 1
                },
                {
                    "fieldname": "status",
                    "fieldtype": "Select",
                    "label": "Status",
                    "options": "Pending\nApproved\nRejected",
                    "default": "Pending",
                    "in_list_view": 1
                },
                {
                    "fieldname": "comments",
                    "fieldtype": "Text",
                    "label": "Comments"
                }
            ],
            "permissions": [
                {
                    "role": "HR Manager",
                    "permlevel": 0,
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                },
                {
                    "role": "HR User",
                    "permlevel": 0,
                    "read": 1,
                    "write": 1,
                    "create": 1
                }
            ]
        }
        
        frappe.get_doc(extra_hours_detail_doctype).insert()
        print("Created DocType: Extra Hours Detail")
    
    # Créer le DocType Extra Hours
    if not frappe.db.exists("DocType", "Extra Hours"):
        extra_hours_doctype = {
            "doctype": "DocType",
            "name": "Extra Hours",
            "module": "HR",
            "custom": 1,
            "naming_rule": "By Script",
            "autoname": "EH-.YYYY.-.MM.-.#####",
            "title_field": "employee_name",
            "fields": [
                {
                    "fieldname": "employee",
                    "fieldtype": "Link",
                    "label": "Employee",
                    "options": "Employee",
                    "reqd": 1,
                    "in_list_view": 1,
                    "in_standard_filter": 1
                },
                {
                    "fieldname": "employee_name",
                    "fieldtype": "Data",
                    "label": "Employee Name",
                    "fetch_from": "employee.employee_name",
                    "read_only": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "column_break_1",
                    "fieldtype": "Column Break"
                },
                {
                    "fieldname": "from_date",
                    "fieldtype": "Date",
                    "label": "From Date",
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "to_date",
                    "fieldtype": "Date",
                    "label": "To Date",
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "section_break_1",
                    "fieldtype": "Section Break",
                    "label": "Extra Hours Details"
                },
                {
                    "fieldname": "extra_hours_details",
                    "fieldtype": "Table",
                    "label": "Extra Hours Details",
                    "options": "Extra Hours Detail"
                },
                {
                    "fieldname": "section_break_2",
                    "fieldtype": "Section Break",
                    "label": "Summary"
                },
                {
                    "fieldname": "total_worked_hours",
                    "fieldtype": "Float",
                    "label": "Total Worked Hours",
                    "precision": 2,
                    "read_only": 1
                },
                {
                    "fieldname": "total_standard_hours",
                    "fieldtype": "Float",
                    "label": "Total Standard Hours",
                    "precision": 2,
                    "read_only": 1
                },
                {
                    "fieldname": "column_break_2",
                    "fieldtype": "Column Break"
                },
                {
                    "fieldname": "total_extra_hours",
                    "fieldtype": "Float",
                    "label": "Total Extra Hours",
                    "precision": 2,
                    "read_only": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "total_approved_extra_hours",
                    "fieldtype": "Float",
                    "label": "Total Approved Extra Hours",
                    "precision": 2,
                    "read_only": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "section_break_3",
                    "fieldtype": "Section Break",
                    "label": "Approval"
                },
                {
                    "fieldname": "approval_status",
                    "fieldtype": "Select",
                    "label": "Approval Status",
                    "options": "Draft\nPending Approval\nApproved\nRejected",
                    "default": "Draft",
                    "in_list_view": 1,
                    "in_standard_filter": 1
                },
                {
                    "fieldname": "approved_by",
                    "fieldtype": "Link",
                    "label": "Approved By",
                    "options": "User",
                    "read_only": 1
                },
                {
                    "fieldname": "column_break_3",
                    "fieldtype": "Column Break"
                },
                {
                    "fieldname": "approval_date",
                    "fieldtype": "Datetime",
                    "label": "Approval Date",
                    "read_only": 1
                },
                {
                    "fieldname": "approval_comments",
                    "fieldtype": "Text",
                    "label": "Approval Comments"
                }
            ],
            "permissions": [
                {
                    "role": "HR Manager",
                    "permlevel": 0,
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "submit": 1,
                    "cancel": 1
                },
                {
                    "role": "HR User",
                    "permlevel": 0,
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "submit": 1
                },
                {
                    "role": "Employee",
                    "permlevel": 0,
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "if_owner": 1
                }
            ]
        }
        
        frappe.get_doc(extra_hours_doctype).insert()
        print("Created DocType: Extra Hours")
    
    frappe.db.commit()
    print("Extra Hours DocTypes creation completed!")


def execute():
    """Main installation function"""
    print("Starting Extra Hours module installation...")
    
    # Créer les DocTypes
    create_extra_hours_doctypes()
    
    # Installer les custom fields
    install_extra_hours_custom_fields()
    
    print("Extra Hours module installation completed successfully!")


if __name__ == "__main__":
    execute()
