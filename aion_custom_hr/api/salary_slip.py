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
    
    # Calculer les heures supplémentaires
    calculate_extra_hours(doc)


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


def calculate_late_minutes_sum(doc, method=None):
    """
    Calcule la somme des pénalités séparées pour late entry et early exit
    en tenant compte des corrections de penalty management
    """
    try:
        frappe.logger().info(f"=== Début du calcul des pénalités pour Salary Slip {doc.name} ===")
        frappe.msgprint(f"=== Début du calcul des pénalités pour Salary Slip {doc.name} ===")
        frappe.logger().info(f"Employé: {doc.employee}")
        frappe.msgprint(f"Employé: {doc.employee}")
        frappe.logger().info(f"Période: du {doc.start_date} au {doc.end_date}")
        frappe.msgprint(f"Période: du {doc.start_date} au {doc.end_date}")

        # D'abord vérifier s'il existe un penalty management validé pour cette période
        frappe.logger().info("Recherche d'un penalty management validé...")
        frappe.logger().info(f"Paramètres de recherche: employee={doc.employee}, start_date={doc.start_date}, end_date={doc.end_date}")
        frappe.msgprint(f"Paramètres de recherche: employee={doc.employee}, start_date={doc.start_date}, end_date={doc.end_date}")  
        # Vérifier d'abord si des penalty managements existent pour cet employé
        all_penalties = frappe.db.sql("""
            SELECT name, employee, from_date, to_date, docstatus, modified
            FROM `tabpenalty managment`
            WHERE employee = %(employee)s
        """, {
            'employee': doc.employee
        }, as_dict=1)
        
        if all_penalties:
            frappe.logger().info(f"Trouvé {len(all_penalties)} penalty managements pour l'employé:")
            frappe.msgprint(f"Trouvé {len(all_penalties)} penalty managements pour l'employé:")
            for p in all_penalties:
                frappe.logger().info(f"- {p.name}: du {p.from_date} au {p.to_date}, status={p.docstatus}")
        else:
            frappe.logger().info("Aucun penalty management trouvé pour cet employé")
            frappe.msgprint("Aucun penalty management trouvé pour cet employé")
        
        # Recherche du penalty management spécifique pour la période
        # D'abord, vérifions tous les penalty managements pour cet employé sans filtres de date
        all_penalties_detail = frappe.db.sql("""
            SELECT 
                name,
                employee,
                from_date,
                to_date,
                docstatus,
                creation,
                modified
            FROM `tabpenalty managment`
            WHERE employee = %(employee)s
        """, {
            'employee': doc.employee
        }, as_dict=1)
        
        frappe.msgprint(f"Tous les penalty managements trouvés : {all_penalties_detail}")
        
        # Maintenant la requête principale avec des dates converties explicitement
        penalty_mgmt = frappe.db.sql("""
            SELECT 
                name,
                employee,
                from_date,
                to_date,
                corrected_late_penalty as total_late,
                corrected_early_penalty as total_early,
                docstatus,
                creation,
                modified
            FROM `tabpenalty managment`
            WHERE employee = %(employee)s
            AND DATE(from_date) <= DATE(%(end_date)s)
            AND DATE(to_date) >= DATE(%(start_date)s)
            
            ORDER BY modified DESC
            LIMIT 1
        """, {
            'employee': doc.employee,
            'start_date': doc.start_date,
            'end_date': doc.end_date
        }, as_dict=1)
        
        frappe.msgprint(f"Paramètres de la requête: employee={doc.employee}, start_date={doc.start_date}, end_date={doc.end_date}")
        frappe.msgprint(f"Résultat de la requête avec filtres de date: {penalty_mgmt}")
        frappe.msgprint(f"penalty_mgmttessssssssssst: {penalty_mgmt}")

        if penalty_mgmt:
            frappe.logger().info(f"Penalty Management trouvé: {penalty_mgmt[0].name}")
            frappe.msgprint(f"Penalty Management trouvé: {penalty_mgmt[0].name}")
            frappe.logger().info(f"Détails: du {penalty_mgmt[0].from_date} au {penalty_mgmt[0].to_date}")
            frappe.msgprint(f"Détails: du {penalty_mgmt[0].from_date} au {penalty_mgmt[0].to_date}")
            frappe.logger().info(f"Status: {penalty_mgmt[0].docstatus}")
            frappe.msgprint(f"Penalty Management trouvé: {penalty_mgmt[0].name}")
            frappe.msgprint(f"Status: {penalty_mgmt[0].docstatus}")
            
            # Utiliser les valeurs corrigées du penalty management
            if hasattr(doc, 'total_late_minutes_sum'):
                doc.total_late_minutes_sum = int(penalty_mgmt[0].total_late or 0)
                frappe.logger().info(f"Pénalités de retard depuis PM: {doc.total_late_minutes_sum} minutes")
                frappe.msgprint(f"Penalite de retard { doc.total_late_minutes_sum} minut")
                
            if hasattr(doc, 'total_early_exit_minutes_sum'):
                doc.total_early_exit_minutes_sum = int(penalty_mgmt[0].total_early or 0)
                frappe.logger().info(f"Pénalités de sortie anticipée depuis PM: {doc.total_early_exit_minutes_sum} minutes")
                
            doc.penalty_note = f"Pénalités importées depuis {penalty_mgmt[0].name}"
            frappe.logger().info("=== Fin du calcul des pénalités depuis Penalty Management ===")
            return
        else:
            frappe.logger().info("Aucun Penalty Management trouvé pour la période spécifiée")

        # Si pas de penalty management, calculer depuis les attendances
        frappe.logger().info("Aucun Penalty Management trouvé, calcul depuis les attendances...")
        
        if hasattr(doc, 'total_late_minutes_sum'):
            frappe.logger().info("Calcul des pénalités de retard depuis les attendances...")
            late_penalty_sum = frappe.db.sql("""
                SELECT COALESCE(SUM(late_entry_penalty_minutes), 0) as total,
                       COUNT(*) as total_records
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
            frappe.logger().info(f"Pénalités de retard trouvées: {doc.total_late_minutes_sum} minutes sur {late_penalty_sum[0].total_records} enregistrements")

        # Calculer total_early_exit_minutes_sum = somme des pénalités early exit
        if hasattr(doc, 'total_early_exit_minutes_sum'):
            frappe.logger().info("Calcul des pénalités de sortie anticipée depuis les attendances...")
            early_penalty_sum = frappe.db.sql("""
                SELECT COALESCE(SUM(early_exit_penalty_minutes), 0) as total,
                       COUNT(*) as total_records
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
            frappe.logger().info(f"Pénalités de sortie anticipée trouvées: {doc.total_early_exit_minutes_sum} minutes sur {early_penalty_sum[0].total_records} enregistrements")
            
        frappe.logger().info(f"=== Fin du calcul des pénalités depuis les attendances ===")
        frappe.logger().info(f"Total des pénalités: {doc.total_late_minutes_sum + doc.total_early_exit_minutes_sum} minutes")
            
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
def test_extra_hours_calculation(employee, start_date, end_date):
    """
    Fonction de test pour déboguer le calcul des heures supplémentaires
    """
    try:
        # Test des données d'attendance
        attendances = frappe.db.sql("""
            SELECT 
                a.attendance_date,
                a.shift as shift_type,
                a.in_time,
                a.out_time,
                s.start_time,
                s.end_time,
                a.status
            FROM `tabAttendance` a
            LEFT JOIN `tabShift Type` s ON a.shift = s.name
            WHERE a.employee = %s
            AND a.attendance_date BETWEEN %s AND %s
            ORDER BY a.attendance_date
        """, (employee, start_date, end_date), as_dict=True)
        
        result = {
            "status": "success",
            "employee": employee,
            "period": f"{start_date} to {end_date}",
            "total_attendances": len(attendances),
            "attendances_with_times": 0,
            "attendances_present": 0,
            "attendances_with_shift": 0,
            "total_extra_hours": 0.0,
            "details": []
        }
        
        for attendance in attendances:
            detail = {
                "date": str(attendance.attendance_date),
                "status": attendance.status,
                "shift_type": attendance.shift_type,
                "in_time": str(attendance.in_time) if attendance.in_time else None,
                "out_time": str(attendance.out_time) if attendance.out_time else None,
                "shift_start": str(attendance.start_time) if attendance.start_time else None,
                "shift_end": str(attendance.end_time) if attendance.end_time else None,
                "error": None,
                "extra_hours": 0.0
            }
            
            # Compter les attendances par critère
            if attendance.status == 'Present':
                result["attendances_present"] += 1
            if attendance.in_time and attendance.out_time:
                result["attendances_with_times"] += 1
            if attendance.shift_type and attendance.start_time and attendance.end_time:
                result["attendances_with_shift"] += 1
            
            # Calculer les heures supplémentaires si toutes les conditions sont remplies
            if (attendance.status == 'Present' and 
                attendance.in_time and attendance.out_time and 
                attendance.shift_type and attendance.start_time and attendance.end_time):
                
                try:
                    # Parser les heures
                    shift_start_str = str(attendance.start_time)
                    shift_end_str = str(attendance.end_time)
                    actual_in_str = str(attendance.in_time)
                    actual_out_str = str(attendance.out_time)
                    
                    # Parser le shift start/end (format Time: HH:MM:SS)
                    if len(shift_start_str.split(':')) == 3:
                        shift_start_parts = shift_start_str.split(':')
                        shift_start_minutes = int(shift_start_parts[0]) * 60 + int(shift_start_parts[1])
                    else:
                        detail["error"] = f"Invalid shift start time format: {shift_start_str}"
                        result["details"].append(detail)
                        continue
                        
                    if len(shift_end_str.split(':')) == 3:
                        shift_end_parts = shift_end_str.split(':')
                        shift_end_minutes = int(shift_end_parts[0]) * 60 + int(shift_end_parts[1])
                    else:
                        detail["error"] = f"Invalid shift end time format: {shift_end_str}"
                        result["details"].append(detail)
                        continue
                    
                    # Parser actual in/out time (format DateTime: YYYY-MM-DD HH:MM:SS)
                    if ' ' in actual_in_str:
                        actual_in_time_part = actual_in_str.split(' ')[1]
                        actual_in_parts = actual_in_time_part.split(':')
                        actual_in_minutes = int(actual_in_parts[0]) * 60 + int(actual_in_parts[1])
                    else:
                        detail["error"] = f"Invalid actual in time format: {actual_in_str}"
                        result["details"].append(detail)
                        continue
                        
                    if ' ' in actual_out_str:
                        actual_out_time_part = actual_out_str.split(' ')[1]
                        actual_out_parts = actual_out_time_part.split(':')
                        actual_out_minutes = int(actual_out_parts[0]) * 60 + int(actual_out_parts[1])
                    else:
                        detail["error"] = f"Invalid actual out time format: {actual_out_str}"
                        result["details"].append(detail)
                        continue
                    
                    # Calculer les heures de travail prévues
                    planned_work_minutes = shift_end_minutes - shift_start_minutes
                    if planned_work_minutes < 0:  # Gestion du passage de minuit
                        planned_work_minutes = (24 * 60) - shift_start_minutes + shift_end_minutes
                    
                    # Calculer les heures réellement travaillées
                    actual_work_minutes = actual_out_minutes - actual_in_minutes
                    if actual_work_minutes < 0:  # Gestion du passage de minuit
                        actual_work_minutes = (24 * 60) - actual_in_minutes + actual_out_minutes
                    
                    # Calculer les heures supplémentaires
                    if actual_work_minutes > planned_work_minutes:
                        extra_minutes = actual_work_minutes - planned_work_minutes
                        extra_hours_today = extra_minutes / 60.0
                        detail["extra_hours"] = round(extra_hours_today, 2)
                        result["total_extra_hours"] += extra_hours_today
                    
                    # Ajouter les détails de calcul
                    detail["planned_minutes"] = planned_work_minutes
                    detail["actual_minutes"] = actual_work_minutes
                    detail["planned_hours"] = round(planned_work_minutes / 60.0, 2)
                    detail["actual_hours"] = round(actual_work_minutes / 60.0, 2)
                    
                except Exception as calc_error:
                    detail["error"] = f"Calculation error: {str(calc_error)}"
            
            result["details"].append(detail)
        
        result["total_extra_hours"] = round(result["total_extra_hours"], 2)
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


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

def calculate_extra_hours(doc, method=None):
    """
    Calcule les heures supplémentaires à partir des enregistrements Extra Hours approuvés
    """
    if not doc.employee or not doc.start_date or not doc.end_date:
        return
    
    # Vérifier si le champ existe
    if not hasattr(doc, 'extra_hours'):
        frappe.logger().warning(f"Field 'extra_hours' not found in Salary Slip. Please install custom field fixture.")
        return
    
    try:
        # Importer la fonction depuis le module extra_hours
        from aion_custom_hr.extra_hours import get_approved_extra_hours_for_salary_slip
        
        # Récupérer les heures supplémentaires approuvées pour cette période
        approved_extra_hours = get_approved_extra_hours_for_salary_slip(
            doc.employee, 
            doc.start_date, 
            doc.end_date
        )
        
        # Mettre à jour le champ extra_hours
        doc.extra_hours = round(approved_extra_hours, 2)
        
        frappe.logger().info(f"Extra hours from approved records for {doc.employee} ({doc.start_date} to {doc.end_date}): {doc.extra_hours} hours")
        
    except ImportError:
        # Fallback vers l'ancien calcul automatique si le module extra_hours n'est pas disponible
        frappe.logger().warning("Extra Hours module not found, falling back to automatic calculation")
        calculate_extra_hours_automatic(doc)
        
    except Exception as e:
        frappe.logger().error(f"Error calculating extra hours for {doc.employee}: {str(e)}")
        doc.extra_hours = 0.0


def calculate_extra_hours_automatic(doc):
    """
    Méthode de fallback pour calculer automatiquement les heures supplémentaires
    (conserve l'ancien comportement)
    """
    try:
        # Récupérer toutes les attendances de l'employé pour la période
        attendances = frappe.db.sql("""
            SELECT 
                a.attendance_date,
                a.shift as shift_type,
                a.in_time,
                a.out_time,
                s.start_time,
                s.end_time
            FROM `tabAttendance` a
            LEFT JOIN `tabShift Type` s ON a.shift = s.name
            WHERE a.employee = %s
            AND a.attendance_date BETWEEN %s AND %s
            AND a.docstatus = 1
            AND a.status = 'Present'
            AND a.in_time IS NOT NULL
            AND a.out_time IS NOT NULL
            AND a.shift IS NOT NULL
            AND s.start_time IS NOT NULL
            AND s.end_time IS NOT NULL
        """, (doc.employee, doc.start_date, doc.end_date), as_dict=True)
        
        total_extra_hours = 0.0
        
        frappe.logger().info(f"Processing {len(attendances)} attendances for automatic extra hours calculation")
        
        for attendance in attendances:
            try:
                # Parser les heures - formats différents
                # shift_time est au format HH:MM:SS
                # in_time/out_time sont au format YYYY-MM-DD HH:MM:SS
                
                shift_start_str = str(attendance.start_time)
                shift_end_str = str(attendance.end_time)
                
                # Parser le shift start/end (format Time: HH:MM:SS)
                if len(shift_start_str.split(':')) == 3:
                    shift_start_parts = shift_start_str.split(':')
                    shift_start_minutes = int(shift_start_parts[0]) * 60 + int(shift_start_parts[1])
                else:
                    frappe.logger().error(f"Invalid shift start time format: {shift_start_str}")
                    continue
                    
                if len(shift_end_str.split(':')) == 3:
                    shift_end_parts = shift_end_str.split(':')
                    shift_end_minutes = int(shift_end_parts[0]) * 60 + int(shift_end_parts[1])
                else:
                    frappe.logger().error(f"Invalid shift end time format: {shift_end_str}")
                    continue
                
                # Parser actual in/out time (format DateTime: YYYY-MM-DD HH:MM:SS)
                actual_in_str = str(attendance.in_time)
                actual_out_str = str(attendance.out_time)
                
                if ' ' in actual_in_str:
                    actual_in_time_part = actual_in_str.split(' ')[1]  # Récupérer juste la partie time
                    actual_in_parts = actual_in_time_part.split(':')
                    actual_in_minutes = int(actual_in_parts[0]) * 60 + int(actual_in_parts[1])
                else:
                    frappe.logger().error(f"Invalid actual in time format: {actual_in_str}")
                    continue
                    
                if ' ' in actual_out_str:
                    actual_out_time_part = actual_out_str.split(' ')[1]  # Récupérer juste la partie time
                    actual_out_parts = actual_out_time_part.split(':')
                    actual_out_minutes = int(actual_out_parts[0]) * 60 + int(actual_out_parts[1])
                else:
                    frappe.logger().error(f"Invalid actual out time format: {actual_out_str}")
                    continue
                
                # Calculer les heures de travail prévues
                planned_work_minutes = shift_end_minutes - shift_start_minutes
                if planned_work_minutes < 0:  # Gestion du passage de minuit
                    planned_work_minutes = (24 * 60) - shift_start_minutes + shift_end_minutes
                
                # Calculer les heures réellement travaillées
                actual_work_minutes = actual_out_minutes - actual_in_minutes
                if actual_work_minutes < 0:  # Gestion du passage de minuit
                    actual_work_minutes = (24 * 60) - actual_in_minutes + actual_out_minutes
                
                # Calculer les heures supplémentaires
                if actual_work_minutes > planned_work_minutes:
                    extra_minutes = actual_work_minutes - planned_work_minutes
                    extra_hours_today = extra_minutes / 60.0
                    total_extra_hours += extra_hours_today
                    
                    frappe.logger().info(f"Extra hours for {attendance.attendance_date}: "
                                       f"Shift: {shift_start_str}-{shift_end_str} ({planned_work_minutes/60:.2f}h), "
                                       f"Actual: {actual_in_time_part}-{actual_out_time_part} ({actual_work_minutes/60:.2f}h), "
                                       f"Extra: {extra_hours_today:.2f}h")
                else:
                    frappe.logger().info(f"No extra hours for {attendance.attendance_date}: "
                                       f"Planned: {planned_work_minutes/60:.2f}h, "
                                       f"Actual: {actual_work_minutes/60:.2f}h")
                
            except Exception as date_error:
                frappe.logger().error(f"Error processing attendance {attendance.attendance_date}: {str(date_error)}")
                continue
        
        # Mettre à jour le champ extra_hours
        doc.extra_hours = round(total_extra_hours, 2)
        frappe.logger().info(f"Total extra hours calculated automatically for {doc.employee} ({doc.start_date} to {doc.end_date}): {doc.extra_hours} hours")
        
    except Exception as e:
        frappe.logger().error(f"Error in automatic extra hours calculation for {doc.employee}: {str(e)}")
        doc.extra_hours = 0.0
