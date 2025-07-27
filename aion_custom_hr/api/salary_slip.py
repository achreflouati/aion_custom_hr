import frappe
from datetime import datetime

def calculate_assume_absent_count(doc, method=None):
    """
    Calcule le nombre total d'attendances marquées comme 'assume as absent'
    pour l'employé dans la période du salary slip
    """
    if not doc.employee or not doc.start_date or not doc.end_date:
        return
    
    try:
        # Compter les attendances avec late_entry_assume_as_absent = 1
        late_assume_count = frappe.db.count('Attendance', {
            'employee': doc.employee,
            'attendance_date': ['between', [doc.start_date, doc.end_date]],
            'late_entry_assume_as_absent': 1
        })
        
        # Compter les attendances avec early_exit_assume_as_absent = 1
        early_assume_count = frappe.db.count('Attendance', {
            'employee': doc.employee,
            'attendance_date': ['between', [doc.start_date, doc.end_date]],
            'early_exit_assume_as_absent': 1
        })
        
        # Compter les attendances avec les deux cases cochées (éviter le double comptage)
        both_assume_count = frappe.db.count('Attendance', {
            'employee': doc.employee,
            'attendance_date': ['between', [doc.start_date, doc.end_date]],
            'late_entry_assume_as_absent': 1,
            'early_exit_assume_as_absent': 1
        })
        
        # Total unique (éviter le double comptage si les deux cases sont cochées le même jour)
        total_assume_absent = late_assume_count + early_assume_count - both_assume_count
        
        # Mettre à jour le champ
        doc.assume_as_absent_count = total_assume_absent
        
        frappe.logger().info(f"Salary Slip {doc.name}: Employee {doc.employee} - Assume absent count: {total_assume_absent}")
        
    except Exception as e:
        frappe.logger().error(f"Error calculating assume absent count for {doc.employee}: {e}")
        doc.assume_as_absent_count = 0
