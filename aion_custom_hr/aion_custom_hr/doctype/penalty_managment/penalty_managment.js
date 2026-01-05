// Copyright (c) 2025, ard and contributors
// For license information, please see license.txt

frappe.ui.form.on("penalty managment", {
    onload: function(frm) {
        frm.is_saving = false;
    },

    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            // frm.add_custom_button(__("Load Penalties"), function() {
            //     load_penalties_for_employee(frm);
            // });

            // frm.add_custom_button(__("Recalculate"), function() {
            //     recalculate_penalty_totals(frm);
            // });

            frm.add_custom_button(__("Apply the justifications for the delays"), function() {
                apply_late_justifications(frm);
            });
        }
        // Appliquer les justifications de retard approuvées
        function apply_late_justifications(frm) {
            if (!frm.doc.employee || !frm.doc.from_date || !frm.doc.to_date) {
                frappe.msgprint(__("يرجى اختيار الموظف والفترة الزمنية."));
                return;
            }
            frappe.call({
                method: 'aion_custom_hr.api.penalty_management.get_approved_late_justifications',
                args: {
                    employee: frm.doc.employee,
                    from_date: frm.doc.from_date,
                    to_date: frm.doc.to_date
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        let justifications = r.message.justifications || [];
                        console.log("justfication",justifications)
                        if (justifications.length === 0) {
                            frappe.msgprint(__("لم يتم العثور على أي مبرر معتمد لهذه الفترة."));
                            return;
                        }
                        // Préparer un résumé dynamique des lignes affectées
                        let summary = '<ul>';
                        justifications.forEach(j => {
                            summary += `<li>التاريخ: <b>${j.date}</b> - دقائق مبررة: <b>${j.late_minutes}</b></li>`;
                        });
                        summary += '</ul>';
                        frappe.confirm(
                            __("سيتم تطبيق المبررات التالية وتصحيح العقوبات:") + '<br>' + summary + '<br>' + __("هل تريد المتابعة؟"),
                            function() {
                                // Appliquer la correction après confirmation
                                let applied_count = 0;
                                justifications.forEach(j => {
                                    (frm.doc.penalty_details || []).forEach(row => {
                                        if (row.attendance_date === j.date) {
                                            let before = row.corrected_late_penalty || 0;
                                            row.corrected_late_penalty = Math.max(0, before - (j.late_minutes || 0));
                                            row.is_corrected = 1;
                                            applied_count++;
                                        }
                                    });
                                });
                                if (applied_count > 0) {
                                    calculate_totals_from_details(frm);
                                    frm.refresh_field("penalty_details");
                                    frappe.msgprint(__("تم تطبيق المبررات على {0} سطر(أسطر) من العقوبات.", [applied_count]));
                                    schedule_save(frm);
                                } else {
                                    frappe.msgprint(__("لم يتم العثور على أي سطر عقوبة مطابق للمبررات."));
                                }
                            },
                            function() {
                                frappe.msgprint(__("لم يتم تطبيق أي تصحيح."));
                            }
                        );
                    } else {
                        frappe.msgprint(__("حدث خطأ أثناء جلب المبررات: ") + (r.message && r.message.error || "خطأ غير معروف"));
                    }
                }
            });
        }
        
        if (frm.doc.penalty_details && frm.doc.penalty_details.length > 0) {
            calculate_totals_from_details(frm);
        }
    },
    
    before_save: function(frm) {
        calculate_totals_from_details(frm);
    },
    
    employee: function(frm) {
        if (frm.doc.employee && frm.doc.from_date && frm.doc.to_date) {
            load_penalties_for_employee(frm);
        }
    },
    
    from_date: function(frm) {
        if (frm.doc.employee && frm.doc.from_date && frm.doc.to_date) {
            load_penalties_for_employee(frm);
        }
    },
    
    to_date: function(frm) {
        if (frm.doc.employee && frm.doc.from_date && frm.doc.to_date) {
            load_penalties_for_employee(frm);
        }
    }
});

frappe.ui.form.on("Penalty Detail", {
    corrected_late_penalty: function(frm, cdt, cdn) {
        mark_as_modified(frm, cdt, cdn);
        calculate_totals_from_details(frm);
        schedule_save(frm);
    },
    
    corrected_early_penalty: function(frm, cdt, cdn) {
        mark_as_modified(frm, cdt, cdn);
        calculate_totals_from_details(frm);
        schedule_save(frm);
    },
    
    penalty_details_remove: function(frm) {
        calculate_totals_from_details(frm);
        schedule_save(frm);
    },
    
    penalty_details_add: function(frm, cdt, cdn) {
        schedule_save(frm);
    }
});

function mark_as_modified(frm, cdt, cdn) {
    var row = frappe.get_doc(cdt, cdn);
    frappe.model.set_value(cdt, cdn, "is_corrected", 1);
}

function schedule_save(frm) {
    if (frm.is_saving) return;
    clearTimeout(frm.save_timeout);
    frm.save_timeout = setTimeout(function() {
        save_document(frm);
    }, 2000);
}

function save_document(frm) {
    if (frm.is_saving) {
        frappe.show_alert({message: __('جاري الحفظ...'), indicator: 'blue'});
        return;
    }
    if (!frm.doc.employee) {
        frappe.msgprint(__("يرجى اختيار الموظف أولاً"));
        return;
    }
    frm.is_saving = true;
    frappe.show_alert({message: __('جاري حفظ التغييرات...'), indicator: 'blue'});
    frm.save().then(() => {
        frappe.show_alert({message: __('تم حفظ التغييرات بنجاح'), indicator: 'green'});
        frm.is_saving = false;
        after_save_update_salary_slips(frm);
    }).catch((error) => {
        console.error('Save error:', error);
        frappe.show_alert({message: __('حدث خطأ أثناء الحفظ'), indicator: 'red'});
        frm.is_saving = false;
    });
}

function after_save_update_salary_slips(frm) {
    if (frm.doc.docstatus === 1) {
        frappe.call({
            method: 'aion_custom_hr.api.penalty_management.update_salary_slip_penalties',
            args: {
                employee: frm.doc.employee,
                from_date: frm.doc.from_date,
                to_date: frm.doc.to_date,
                total_late_minutes: frm.doc.corrected_late_penalty || 0,
                total_early_minutes: frm.doc.corrected_early_penalty || 0
            },
            callback: function(r) {
                console.log("Salary slip update response:", r.message);
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('تم تحديث {0} قسيمة راتب', [r.message.total_updated]),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('حدث خطأ أثناء تحديث قسائم الراتب: {0}', [r.message.error || 'خطأ غير معروف']),
                        indicator: 'red'
                    });
                }
            }
        });
    }
}
function load_penalties_for_employee(frm) {
    if (!frm.doc.employee) {
        frappe.msgprint(__("يرجى اختيار الموظف أولاً"));
        return;
    }
    if (!frm.doc.from_date || !frm.doc.to_date) {
        frappe.msgprint(__("يرجى اختيار تاريخ البداية والنهاية"));
        return;
    }
    frappe.call({
        method: 'aion_custom_hr.api.penalty_management.load_penalties_for_period',
        args: {
            employee: frm.doc.employee,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                populate_penalty_details(frm, r.message.penalties);
                update_summary_totals(frm, r.message.summary);
                frappe.msgprint(__("تم تحميل {0} سجل عقوبة", [r.message.total_records]));
                after_save_update_salary_slips(frm);
                save_document(frm);
            } else {
                frappe.msgprint(__("حدث خطأ أثناء تحميل العقوبات: ") + (r.message.error || "خطأ غير معروف"));
            }
        }
    });
}

function populate_penalty_details(frm, penalties) {
    frm.clear_table("penalty_details");
    
    penalties.forEach(penalty => {
        let row = frm.add_child("penalty_details");
        row.attendance_date = penalty.attendance_date;
        row.attendance_name = penalty.attendance_name;
        row.shift_type = penalty.shift_type;
        row.actual_late_minutes = penalty.total_late_minutes || 0;
        row.actual_early_minutes = penalty.total_early_exit_minutes || 0;
        row.original_late_penalty = penalty.late_entry_penalty_minutes || 0;
        row.original_early_penalty = penalty.early_exit_penalty_minutes || 0;
        row.corrected_late_penalty = penalty.late_entry_penalty_minutes || 0;
        row.corrected_early_penalty = penalty.early_exit_penalty_minutes || 0;
        row.period_applied = Math.max(
            penalty.late_entry_period_applied || 0,
            penalty.early_exit_period_applied || 0
        );
        row.coefficient_used = penalty.coefficient_used || 0;
        row.is_corrected = 0;
    });
    
    frm.refresh_field("penalty_details");
    calculate_totals_from_details(frm);
}

function update_summary_totals(frm, summary) {
    frm.set_value("total_late_penalty", summary.total_late_penalty);
    frm.set_value("total_early_penalty", summary.total_early_penalty);
    frm.set_value("total_penalty_minutes", summary.total_penalty_minutes);
    frm.set_value("corrected_late_penalty", summary.total_late_penalty);
    frm.set_value("corrected_early_penalty", summary.total_early_penalty);
    frm.set_value("total_corrected_penalty", summary.total_penalty_minutes);
    
    frm.refresh_fields();
}

function calculate_totals_from_details(frm) {
    let total_original_late = 0;
    let total_original_early = 0;
    let total_corrected_late = 0;
    let total_corrected_early = 0;
    
    if (frm.doc.penalty_details) {
        frm.doc.penalty_details.forEach(row => {
            total_original_late += row.original_late_penalty || 0;
            total_original_early += row.original_early_penalty || 0;
            total_corrected_late += row.corrected_late_penalty || 0;
            total_corrected_early += row.corrected_early_penalty || 0;
        });
    }
    
    frm.set_value("total_late_penalty", total_original_late);
    frm.set_value("total_early_penalty", total_original_early);
    frm.set_value("total_penalty_minutes", total_original_late + total_original_early);
    frm.set_value("corrected_late_penalty", total_corrected_late);
    frm.set_value("corrected_early_penalty", total_corrected_early);
    frm.set_value("total_corrected_penalty", total_corrected_late + total_corrected_early);
    
    frm.refresh_fields();
}

function recalculate_penalty_totals(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__("يرجى حفظ المستند أولاً"));
        return;
    }
    frappe.call({
        method: 'aion_custom_hr.api.penalty_management.recalculate_penalty_management',
        args: {
            doc_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.set_value("corrected_late_penalty", r.message.totals.corrected_late_penalty);
                frm.set_value("corrected_early_penalty", r.message.totals.corrected_early_penalty);
                frm.set_value("total_corrected_penalty", r.message.totals.total_corrected_penalty);
                if (r.message.salary_slips_updated && r.message.salary_slips_updated.total_updated > 0) {
                    frappe.msgprint(__("تم إعادة احتساب العقوبات بنجاح. تم تحديث {0} قسيمة راتب", 
                        [r.message.salary_slips_updated.total_updated]));
                } else {
                    frappe.msgprint(__("تم إعادة احتساب العقوبات بنجاح. لم يتم العثور على قسائم راتب للتحديث"));
                }
                save_document(frm);
            } else {
                frappe.msgprint(__("حدث خطأ أثناء إعادة احتساب العقوبات: ") + (r.message.error || "خطأ غير معروف"));
            }
        }
    });
}