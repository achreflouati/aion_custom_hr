# Copyright (c) 2025, ard and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class appraisalemployeeitems(Document):
    def validate(self):
        self.set_employee_scores()
        self.check_and_set_manager_score()
        self.calculate_final_score()
    
    def set_employee_scores(self):
        if self.employee:
            # Get all monthly scores for the employee
            monthly_scores = frappe.get_all(
                "Employee Monthly Score",
                filters={
                    "employee": self.employee,
                    "appraisal_date": ("<=", self.appraisal_date)
                },
                fields=["monthly_score"],
                order_by="appraisal_date desc"
            )
            
            if monthly_scores:
                # Calculate average score from monthly scores
                total_score = sum(score.monthly_score for score in monthly_scores)
                self.appraisal_score = total_score / len(monthly_scores)
    
    def check_and_set_manager_score(self):
        if self.employee:
            # Get employee's manager
            employee = frappe.get_doc("Employee", self.employee)
            if employee.reports_to:
                manager = frappe.get_doc("Employee", employee.reports_to)
                self.manager = manager.name
                self.manager_name = manager.employee_name
                
                # Get manager's monthly scores
                manager_scores = frappe.get_all(
                    "Employee Monthly Score",
                    filters={
                        "employee": manager.name,
                        "appraisal_date": ("<=", self.appraisal_date)
                    },
                    fields=["monthly_score", "appraisal_date"],
                    order_by="appraisal_date desc",
                    limit=1
                )
                
                if manager_scores:
                    self.manager_score = manager_scores[0].monthly_score
                    self.manager_score_date = getdate(manager_scores[0].appraisal_date)
    
    def calculate_final_score(self):
        if self.appraisal_score and self.manager_score:
            self.final_score = (self.appraisal_score + self.manager_score) / 2
