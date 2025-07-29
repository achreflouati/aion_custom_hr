
import frappe
from datetime import datetime

def set_attendance_status(doc, method=None):
    if doc.shift and doc.in_time and doc.out_time:
        shift = frappe.get_doc('Shift Type', doc.shift)
        grace_late = int(getattr(shift, "late_entry_grace_period", 0) or 0)
        grace_early = int(getattr(shift, "early_exit_grace_period", 0) or 0)
        late_assume_absent = int(getattr(shift, "late_entry_assume_as_absent", 0) or 0)
        early_assume_absent = int(getattr(shift, "early_exit_assume_as_absent", 0) or 0)
        fmt_time = "%H:%M:%S"
        fmt_dt = "%Y-%m-%d %H:%M:%S"
        frappe.logger().info(f"Attendance debug: in_time={doc.in_time}, out_time={doc.out_time}, shift_in={shift.start_time}, shift_out={shift.end_time}, grace_late={grace_late}, grace_early={grace_early}")
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
        if late_minutes > grace_late:
            doc.total_late_minutes = late_minutes - late_minutes + 60
        
        # Logique arrondi pour early exit : si total_early_exit_minutes > grace_early, alors arrondir à 60 minutes  
        if early_exit_minutes > grace_early:
            doc.total_early_exit_minutes = early_exit_minutes - early_exit_minutes + 60
            
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
        