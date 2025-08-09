import frappe
from datetime import datetime

def calculate_assume_absent_count(doc, method=None):
    """
    Calcule le nombre total d'attendances marquées comme 'assume as absent'
    et les minutes de retard/sortie anticipée pour l'employé dans la période du salary slip
    """
    if not doc.employee or not doc.start_date or not doc.end_date:
        return
    
    # Calculer assume_as_absent_count
    calculate_assume_absent_count_only(doc)
    
    # Calculer les minutes de retard et sortie anticipée
    calculate_late_minutes_sum(doc)


def calculate_assume_absent_count_only(doc):
    """
    Calcule uniquement le nombre total d'attendances marquées comme 'assume as absent'
    """
    # Vérifier si le champ existe
    if not hasattr(doc, 'assume_as_absent_count'):
        frappe.logger().warning(f"Field 'assume_as_absent_count' not found in Salary Slip. Please install custom field fixture.")
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
        
        frappe.logger().info(f"Salary Slip {doc.name}: Employee {doc.employee} - Assume absent count: {total_assume_absent} (late: {late_assume_count}, early: {early_assume_count}, both: {both_assume_count})")
        
    except Exception as e:
        frappe.logger().error(f"Error calculating assume absent count for {doc.employee}: {e}")
        doc.assume_as_absent_count = 0


def calculate_late_minutes_sum(doc):
    """
    Calcule la somme des pénalités séparées pour late entry et early exit
    """
    try:
        # Calculer total_late_minutes_sum = somme des pénalités late entry
        if hasattr(doc, 'total_late_minutes_sum'):
            late_penalty_sum = frappe.db.sql("""
                SELECT COALESCE(SUM(late_entry_penalty_minutes), 0) as total
                FROM `tabAttendance`
                WHERE employee = %(employee)s
                AND attendance_date BETWEEN %(start_date)s AND %(end_date)s
                AND late_entry_penalty_minutes > 0
            """, {
                'employee': doc.employee,
                'start_date': doc.start_date,
                'end_date': doc.end_date
            }, as_dict=1)
            
            doc.total_late_minutes_sum = int(late_penalty_sum[0].total) if late_penalty_sum else 0
            frappe.logger().info(f"Salary Slip {doc.name}: Total late entry penalty: {doc.total_late_minutes_sum}")
        
        # Calculer total_early_exit_minutes_sum = somme des pénalités early exit
        if hasattr(doc, 'total_early_exit_minutes_sum'):
            early_penalty_sum = frappe.db.sql("""
                SELECT COALESCE(SUM(early_exit_penalty_minutes), 0) as total
                FROM `tabAttendance`
                WHERE employee = %(employee)s
                AND attendance_date BETWEEN %(start_date)s AND %(end_date)s
                AND early_exit_penalty_minutes > 0
            """, {
                'employee': doc.employee,
                'start_date': doc.start_date,
                'end_date': doc.end_date
            }, as_dict=1)
            
            doc.total_early_exit_minutes_sum = int(early_penalty_sum[0].total) if early_penalty_sum else 0
            frappe.logger().info(f"Salary Slip {doc.name}: Total early exit penalty: {doc.total_early_exit_minutes_sum}")
            
    except Exception as e:
        frappe.logger().error(f"Error calculating separate penalty sums for {doc.employee}: {e}")
        # Mettre des valeurs par défaut en cas d'erreur
        if hasattr(doc, 'total_late_minutes_sum'):
            doc.total_late_minutes_sum = 0
        if hasattr(doc, 'total_early_exit_minutes_sum'):
            doc.total_early_exit_minutes_sum = 0


@frappe.whitelist()
def recalculate_all_salary_slips():
    """
    Fonction utilitaire pour recalculer tous les champs personnalisés 
    sur tous les salary slips existants
    """
    salary_slips = frappe.get_all('Salary Slip', fields=['name'])
    updated_count = 0
    
    for slip in salary_slips:
        try:
            doc = frappe.get_doc('Salary Slip', slip.name)
            
            # Sauvegarder les anciennes valeurs pour comparaison
            old_absent_count = getattr(doc, 'assume_as_absent_count', 0)
            old_late_minutes = getattr(doc, 'total_late_minutes_sum', 0)
            old_early_minutes = getattr(doc, 'total_early_exit_minutes_sum', 0)
            
            # Recalculer tous les champs
            calculate_assume_absent_count(doc)
            
            # Nouvelles valeurs
            new_absent_count = getattr(doc, 'assume_as_absent_count', 0)
            new_late_minutes = getattr(doc, 'total_late_minutes_sum', 0)
            new_early_minutes = getattr(doc, 'total_early_exit_minutes_sum', 0)
            
            # Sauvegarder si au moins une valeur a changé
            if (old_absent_count != new_absent_count or 
                old_late_minutes != new_late_minutes or 
                old_early_minutes != new_early_minutes):
                
                doc.save()
                updated_count += 1
                frappe.logger().info(f"Updated {slip.name}: absent_count {old_absent_count}->{new_absent_count}, late_minutes {old_late_minutes}->{new_late_minutes}, early_minutes {old_early_minutes}->{new_early_minutes}")
                
        except Exception as e:
            frappe.logger().error(f"Error updating {slip.name}: {e}")
    
    frappe.msgprint(f"Successfully updated {updated_count} Salary Slips")
    return f"Updated {updated_count} salary slips"


@frappe.whitelist()
def test_calculation(employee, start_date, end_date):
    """
    Fonction de test pour vérifier les calculs manuellement
    """
    try:
        # Test separate penalty calculation
        penalty_result = frappe.db.sql("""
            SELECT 
                attendance_date,
                total_late_minutes,
                total_early_exit_minutes,
                late_entry_penalty_minutes,
                early_exit_penalty_minutes,
                late_entry_period_applied,
                early_exit_period_applied,
                applied_penalty_minutes
            FROM `tabAttendance`
            WHERE employee = %(employee)s
            AND attendance_date BETWEEN %(start_date)s AND %(end_date)s
            AND (total_late_minutes > 0 OR total_early_exit_minutes > 0)
            ORDER BY attendance_date
        """, {
            'employee': employee,
            'start_date': start_date,
            'end_date': end_date
        }, as_dict=1)
        
        # Calculer les totaux séparés
        total_late_penalty = sum(row.late_entry_penalty_minutes or 0 for row in penalty_result)
        total_early_penalty = sum(row.early_exit_penalty_minutes or 0 for row in penalty_result)
        total_penalty = sum(row.applied_penalty_minutes or 0 for row in penalty_result)
        
        return {
            "status": "success",
            "employee": employee,
            "period": f"{start_date} to {end_date}",
            "total_late_penalty": total_late_penalty,
            "total_early_penalty": total_early_penalty,
            "total_penalty_minutes": total_penalty,
            "attendance_details": penalty_result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
