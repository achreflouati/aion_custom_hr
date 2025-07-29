import frappe

def calculate_payroll_totals(doc, method=None):
    """
    Calcule les totaux des minutes de retard, départ anticipé et assume absent count
    pour tous les employés dans ce Payroll Entry
    """
    if not doc.employees:
        return
    
    total_late_minutes = 0
    total_early_exit_minutes = 0
    total_assume_absent = 0
    
    # Parcourir tous les employés du payroll
    for emp_row in doc.employees:
        if not emp_row.employee:
            continue
            
        employee = emp_row.employee
        
        # Requête pour obtenir les données d'attendance de cet employé
        # pendant la période du payroll
        attendance_data = frappe.db.sql("""
            SELECT 
                COALESCE(SUM(total_late_minutes), 0) as late_sum,
                COALESCE(SUM(total_early_exit_minutes), 0) as early_sum,
                COALESCE(SUM(CASE WHEN late_entry_assume_as_absent = 1 OR early_exit_assume_as_absent = 1 THEN 1 ELSE 0 END), 0) as absent_count
            FROM `tabAttendance`
            WHERE employee = %s
            AND attendance_date BETWEEN %s AND %s
            AND docstatus != 2
        """, (employee, doc.start_date, doc.end_date), as_dict=True)
        
        if attendance_data:
            data = attendance_data[0]
            total_late_minutes += int(data.get('late_sum', 0))
            total_early_exit_minutes += int(data.get('early_sum', 0))
            total_assume_absent += int(data.get('absent_count', 0))
    
    # Mettre à jour les champs du Payroll Entry
    if hasattr(doc, 'total_late_minutes_sum'):
        doc.total_late_minutes_sum = total_late_minutes
    if hasattr(doc, 'total_early_exit_minutes_sum'):
        doc.total_early_exit_minutes_sum = total_early_exit_minutes
    if hasattr(doc, 'total_assume_absent_count'):
        doc.total_assume_absent_count = total_assume_absent
    
    frappe.logger().info(f"Payroll Entry {doc.name}: Late minutes sum = {total_late_minutes}, Early exit sum = {total_early_exit_minutes}, Assume absent count = {total_assume_absent}")