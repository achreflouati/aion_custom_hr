frappe.listview_settings['penalty managment'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__('إنشاء عقوبات جماعية'), function () {
            let d = new frappe.ui.Dialog({
                title: __('تحديد الموظفين'),
                fields: [
                    {
                        fieldname: 'BRANCH',
                        label: __('الفرع'),
                        fieldtype: 'Link',
                        options: 'Branch',
                        reqd: 0,
                        default: frappe.defaults.get_user_default('BRANCH'),
                    },
                    {
                        fieldname: 'DEPARTMENT',
                        label: __('القسم'),
                        fieldtype: 'Link',
                        options: 'Department',
                        reqd: 0,
                        default: frappe.defaults.get_user_default('DEPARTMENT'),
                    },
                    {
                        fieldname: 'employees',
                        label: __('الموظفون'),
                        fieldtype: 'MultiSelectList',
                        reqd: 0,
                        options: [],
                        get_data: function(txt) {
                            // 'this' is the field, so use this.dialog to access dialog values
                            let dialog = this.dialog || (this.df && this.df.parent_dialog);
                            // fallback: try to get dialog from global if needed
                            dialog = dialog || frappe._cur_dialog;
                            let branch = dialog ? dialog.get_value('BRANCH') : null;
                            let department = dialog ? dialog.get_value('DEPARTMENT') : null;
                            let filters = {};
                            if (txt) {
                                filters['employee_name'] = ['like', '%' + txt + '%'];
                            }
                            if (branch) {
                                filters['branch'] = branch;
                            }
                            if (department) {
                                filters['department'] = department;
                            }
                            return frappe.db.get_list('Employee', {
                                fields: ['name', 'employee_name'],
                                filters: filters,
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
                    // Si aucun employé sélectionné, récupérer par BRANCH/DEPARTMENT
                    if (!selected_employees.length) {
                        let filters = {};
                        if (values.BRANCH) filters.branch = values.BRANCH;
                        if (values.DEPARTMENT) filters.department = values.DEPARTMENT;
                        frappe.db.get_list('Employee', {
                            fields: ['name'],
                            filters: filters,
                            limit: 1000
                        }).then(r => {
                            if (!r || !r.length) {
                                frappe.msgprint(__('يرجى تحديد موظف واحد على الأقل أو اختيار فرع/قسم به موظفين'));
                                return;
                            }
                            let employee_names = r.map(emp => emp.name);
                            call_bulk_create(employee_names);
                        });
                    } else {
                        call_bulk_create(selected_employees);
                    }

                    function call_bulk_create(employee_list) {
                        frappe.call({
                            method: 'aion_custom_hr.aion_custom_hr.doctype.penalty_managment.penalty_managment.bulk_create_penalty_managment',
                            args: {
                                employees: JSON.stringify(employee_list),
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
                }
            });
            d.show();
        });
    }
};
