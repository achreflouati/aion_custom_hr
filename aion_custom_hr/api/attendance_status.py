
import frappe
from datetime import datetime

def set_attendance_status(doc, method=None):
    if doc.shift and doc.in_time and doc.out_time:
        shift = frappe.get_doc('Shift Type', doc.shift)
        grace_late = int(getattr(shift, "late_entry_grace_period", 0) or 0)
        grace_early = int(getattr(shift, "early_exit_grace_period", 0) or 0)
        late_assume_absent = int(getattr(shift, "late_entry_assume_as_absent", 0) or 0)
        early_assume_absent = int(getattr(shift, "early_exit_assume_as_absent", 0) or 0)
        
        # Récupération des nouveaux champs pour les 4 périodes
        # Période 1
        late_entry_p1 = int(getattr(shift, "late_entry_assume_as_absent_1", 0) or 0)
        early_exit_p1 = int(getattr(shift, "early_exit_assume_as_absent_1", 0) or 0)
        coefficient_p1 = float(getattr(shift, "coefficient_penalty_period_1", 0) or 0)
        penalty_p1 = int(getattr(shift, "penalty_period_1", 0) or 0)
        
        # Période 2
        late_entry_p2 = int(getattr(shift, "late_entry_assume_as_absent_2", 0) or 0)
        early_exit_p2 = int(getattr(shift, "early_exit_assume_as_absent_2", 0) or 0)
        coefficient_p2 = float(getattr(shift, "coefficient_penalty_period_2", 0) or 0)
        penalty_p2 = int(getattr(shift, "penalty_period_2", 0) or 0)
        
        # Période 3
        late_entry_p3 = int(getattr(shift, "late_entry_assume_as_absent_3", 0) or 0)
        early_exit_p3 = int(getattr(shift, "early_exit_assume_as_absent_3", 0) or 0)
        coefficient_p3 = float(getattr(shift, "coefficient_penalty_period_3", 0) or 0)
        penalty_p3 = int(getattr(shift, "penalty_period_3", 0) or 0)
        
        # Période 4
        late_entry_p4 = int(getattr(shift, "late_entry_assume_as_absent_4", 0) or 0)
        early_exit_p4 = int(getattr(shift, "early_exit_assume_as_absent_4", 0) or 0)
        coefficient_p4 = float(getattr(shift, "coefficient_penalty_period_4", 0) or 0)
        penalty_p4 = int(getattr(shift, "penalty_period_4", 0) or 0)
        fmt_time = "%H:%M:%S"
        fmt_dt = "%Y-%m-%d %H:%M:%S"
        frappe.logger().info(f"Attendance debug: in_time={doc.in_time}, out_time={doc.out_time}, shift_in={shift.start_time}, shift_out={shift.end_time}, grace_late={grace_late}, grace_early={grace_early}")
        frappe.logger().info(f"Period config: P1({late_entry_p1},{early_exit_p1},{coefficient_p1},{penalty_p1}) P2({late_entry_p2},{early_exit_p2},{coefficient_p2},{penalty_p2}) P3({late_entry_p3},{early_exit_p3},{coefficient_p3},{penalty_p3}) P4({late_entry_p4},{early_exit_p4},{coefficient_p4},{penalty_p4})")
        try:
            scheduled_in = datetime.strptime(str(shift.start_time), fmt_time)
            actual_in = datetime.strptime(str(doc.in_time), fmt_dt)
            scheduled_out = datetime.strptime(str(shift.end_time), fmt_time)
            actual_out = datetime.strptime(str(doc.out_time), fmt_dt)
            # Aligner la date sur celle du pointage
            scheduled_in = scheduled_in.replace(year=actual_in.year, month=actual_in.month, day=actual_in.day)
            scheduled_out = scheduled_out.replace(year=actual_out.year, month=actual_out.month, day=actual_out.day)
        except Exception as e:
            frappe.throw(f"Erreur de parsing des horaires : {e}")
        try:
            raw_late = int((actual_in - scheduled_in).total_seconds() // 60)
            late_minutes = raw_late if raw_late > 0 else 0
        except Exception as e:
            frappe.logger().error(f"Attendance late_minutes error: {e}")
            late_minutes = 0
        try:
            raw_early = int((scheduled_out - actual_out).total_seconds() // 60)
            early_exit_minutes = raw_early if raw_early > 0 else 0
        except Exception as e:
            frappe.logger().error(f"Attendance early_exit_minutes error: {e}")
            early_exit_minutes = 0
        frappe.logger().info(f"Attendance debug: late_minutes={late_minutes}, early_exit_minutes={early_exit_minutes}")
        # Total late/early minutes = tous les minutes réels (pas de soustraction de la tolérance)
        doc.total_late_minutes = late_minutes
        doc.total_early_exit_minutes = early_exit_minutes
        # Ajout des cases à cocher
        doc.late_entry = late_minutes > 0
        doc.early_exit = early_exit_minutes > 0
        # Ajout des nouveaux checkboxes
        doc.late_entry_assume_as_absent = False
        doc.early_exit_assume_as_absent = False
        if late_assume_absent and late_minutes >= late_assume_absent:
            doc.late_entry_assume_as_absent = True
        if early_assume_absent and early_exit_minutes >= early_assume_absent:
            doc.early_exit_assume_as_absent = True
        
        # Logique arrondi : si total_late_minutes > grace_late, alors arrondir à 60 minutes
        # if late_minutes > grace_late:
        #     doc.total_late_minutes = late_minutes - late_minutes + 60
        
        # Logique arrondi pour early exit : si total_early_exit_minutes > grace_early, alors arrondir à 60 minutes  
        # if early_exit_minutes > grace_early:
        #     doc.total_early_exit_minutes = early_exit_minutes - early_exit_minutes + 60
            
        # Calcul séparé des pénalités pour late entry et early exit
        late_penalty = 0
        early_penalty = 0
        late_period_applied = 0
        early_period_applied = 0
        
        # === CALCUL PÉNALITÉ LATE ENTRY ===
        if late_minutes > 0:
            # Période 4 (la plus sévère) pour late entry
            if late_entry_p4 > 0 and late_minutes >= late_entry_p4:
                if penalty_p4 > 0:
                    late_penalty = penalty_p4
                    late_period_applied = 4
            # Période 3 pour late entry
            elif late_entry_p3 > 0 and late_minutes >= late_entry_p3:
                if penalty_p3 > 0:
                    late_penalty = penalty_p3
                    late_period_applied = 3
            # Période 2 pour late entry
            elif late_entry_p2 > 0 and late_minutes >= late_entry_p2:
                if penalty_p2 > 0:
                    late_penalty = penalty_p2
                    late_period_applied = 2
            # Période 1 pour late entry
            elif late_entry_p1 > 0 and late_minutes >= late_entry_p1:
                if penalty_p1 > 0:
                    late_penalty = penalty_p1
                    late_period_applied = 1
        
        # === CALCUL PÉNALITÉ EARLY EXIT ===
        if early_exit_minutes > 0:
            # Période 4 (la plus sévère) pour early exit
            if early_exit_p4 > 0 and early_exit_minutes >= early_exit_p4:
                if penalty_p4 > 0:
                    early_penalty = penalty_p4
                    early_period_applied = 4
            # Période 3 pour early exit
            elif early_exit_p3 > 0 and early_exit_minutes >= early_exit_p3:
                if penalty_p3 > 0:
                    early_penalty = penalty_p3
                    early_period_applied = 3
            # Période 2 pour early exit
            elif early_exit_p2 > 0 and early_exit_minutes >= early_exit_p2:
                if penalty_p2 > 0:
                    early_penalty = penalty_p2
                    early_period_applied = 2
            # Période 1 pour early exit
            elif early_exit_p1 > 0 and early_exit_minutes >= early_exit_p1:
                if penalty_p1 > 0:
                    early_penalty = penalty_p1
                    early_period_applied = 1
        
        # Sauvegarder les pénalités séparées dans l'attendance
        doc.late_entry_penalty_minutes = late_penalty
        doc.early_exit_penalty_minutes = early_penalty
        doc.late_entry_period_applied = late_period_applied
        doc.early_exit_period_applied = early_period_applied
        
        # Total des pénalités (pour compatibilité)
        doc.applied_penalty_minutes = late_penalty + early_penalty
        doc.penalty_period_applied = max(late_period_applied, early_period_applied)
        
        frappe.logger().info(f"Separate penalty calculation: late_minutes={late_minutes} -> late_penalty={late_penalty} (period {late_period_applied}), early_exit_minutes={early_exit_minutes} -> early_penalty={early_penalty} (period {early_period_applied}), total={late_penalty + early_penalty}")
            
        # Cas pile à l'heure
        # if late_minutes == 0 and early_exit_minutes == 0:
        #     doc.status = 'Present'
        # # Cas retard et/ou départ anticipé dans la tolérance
        # elif (late_minutes > 0 and late_minutes <= grace_late) and (early_exit_minutes > 0 and early_exit_minutes <= grace_early):
        #     doc.status = 'Present'
        # elif (late_minutes > 0 and late_minutes <= grace_late):
        #     doc.status = 'Present'
        # elif (early_exit_minutes > 0 and early_exit_minutes <= grace_early):
        #     doc.status = 'Present'
        # # Cas dépassement de tolérance (un ou les deux)
        # elif late_minutes > grace_late or early_exit_minutes > grace_early:
        #     doc.status = 'Present'
        