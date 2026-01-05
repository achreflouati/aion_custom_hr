frappe.listview_settings['penalty managment'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__('إنشاء عقوبات جماعية'), function () {
            let d = new frappe.ui.Dialog({
                title: __('تحديد الموظفين'),
                fields: [
                    {
                        fieldname: 'employees',
                        label: __('الموظفون'),
                        fieldtype: 'MultiSelectList',
                        reqd: 1,
                        options: [],
                        get_data: function(txt) {
                            return frappe.db.get_list('Employee', {
                                fields: ['name', 'employee_name'],
                                filters: txt ? { 'employee_name': ['like', '%' + txt + '%'] } : {},
                                limit: 20
                            }).then(r => {
                                return (r || []).map(emp => ({
                                    value: emp.name,
                                    description: emp.employee_name + ' (' + emp.name + ')'
                                }));
                            });
                        }
                    },
                    {
                        fieldname: 'from_date',
                        label: __('من تاريخ'),
                        fieldtype: 'Date',
                        reqd: 1
                    },
                    {
                        fieldname: 'to_date',
                        label: __('إلى تاريخ'),
                        fieldtype: 'Date',
                        reqd: 1
                    }
                ],
                primary_action_label: __('إنشاء'),
                primary_action(values) {
                    let selected_employees = values.employees || [];
                    if (!selected_employees.length) {
                        frappe.msgprint(__('يرجى تحديد موظف واحد على الأقل'));
                        return;
                    }
                    frappe.call({
                        method: 'aion_custom_hr.aion_custom_hr.doctype.penalty_managment.penalty_managment.bulk_create_penalty_managment',
                        args: {
                            employees: JSON.stringify(selected_employees),
                            from_date: values.from_date,
                            to_date: values.to_date
                        },
                        freeze: true,
                        callback: function(r) {
                            if (r.message && r.message.success) {
                                let created = r.message.created ? r.message.created.length : 0;
                                if (created > 0) {
                                    frappe.show_alert(__('تم إنشاء {0} عقوبة بنجاح', [created]));
                                }
                                if (r.message.without_shift && r.message.without_shift.length) {
                                    frappe.msgprint({
                                        title: __('موظفون بدون نوع دوام'),
                                        message: __('لم يتم إنشاء عقوبة للموظفين التاليين لعدم وجود نوع دوام:<br>{0}', [r.message.without_shift.join('<br>')]),
                                        indicator: 'orange'
                                    });
                                }
                                d.hide();
                                listview.refresh();
                            } else {
                                frappe.msgprint(__('حدث خطأ أثناء الإنشاء الجماعي'));
                            }
                        }
                    });
                }
            });
            d.show();
        });
    }
};
