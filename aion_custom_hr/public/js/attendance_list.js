

// Ajout du bouton personnalisé Exécuter sans modifier le reste du fichier
if (frappe.listview_settings['Attendance'] && frappe.listview_settings['Attendance'].onload) {
    const original_onload = frappe.listview_settings['Attendance'].onload;
    frappe.listview_settings['Attendance'].onload = function(listview) {
        original_onload(listview);
        listview.page.add_inner_button(__('Execute'), function() {
            frappe.call({
                method: 'aion_custom_hr.api.make_attendance.scheduled_auto_attendance_and_extra_hours',
                freeze: true,
                freeze_message: 'يرجى الانتظار... جاري تنفيذ الأتمتة الجماعية للحضور والساعات الإضافية',
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint({
                            title: __('تم التنفيذ'),
                            message: __('تم تنفيذ الأتمتة الجماعية بنجاح!'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint({
                            title: __('خطأ'),
                            message: __('حدث خطأ أثناء التنفيذ. يرجى المحاولة لاحقاً.'),
                            indicator: 'red'
                        });
                    }
                }
            });
        });
    };
} else {
    frappe.listview_settings['Attendance'] = frappe.listview_settings['Attendance'] || {};
    frappe.listview_settings['Attendance'].onload = function(listview) {
        listview.page.add_inner_button(__('Execute'), function() {
            frappe.call({
                method: 'aion_custom_hr.api.make_attendance.scheduled_auto_attendance_and_extra_hours',
                freeze: true,
                freeze_message: 'يرجى الانتظار... جاري تنفيذ الأتمتة الجماعية للحضور والساعات الإضافية',
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint({
                            title: __('تم التنفيذ'),
                            message: __('تم تنفيذ الأتمتة الجماعية بنجاح!'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint({
                            title: __('خطأ'),
                            message: __('حدث خطأ أثناء التنفيذ. يرجى المحاولة لاحقاً.'),
                            indicator: 'red'
                        });
                    }
                }
            });
        });
    };
}
