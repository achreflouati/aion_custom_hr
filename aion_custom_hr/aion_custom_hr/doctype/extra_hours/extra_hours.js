// Copyright (c) 2025, ard and contributors
// For license information, please see license.txt


frappe.ui.form.on("Extra Hours", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('تطبيق مبررات الساعات الإضافية'), function() {
				apply_extra_hours_justifications(frm);
			});
		}
	}
});

function apply_extra_hours_justifications(frm) {
	if (!frm.doc.employee || !frm.doc.from_date || !frm.doc.to_date) {
		frappe.msgprint(__('يرجى اختيار الموظف والفترة الزمنية.'));
		return;
	}
	frappe.call({
		method: 'aion_custom_hr.aion_custom_hr.doctype.extra_hours.extra_hours.get_approved_extra_hours_justifications',
		args: {
			employee: frm.doc.employee,
			from_date: frm.doc.from_date,
			to_date: frm.doc.to_date
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				let justifications = r.message.justifications || [];
				if (justifications.length === 0) {
					frappe.msgprint(__('لم يتم العثور على أي مبرر معتمد لهذه الفترة.'));
					return;
				}
				// ملخص ديناميكي
				let summary = '<ul>';
				justifications.forEach(j => {
					summary += `<li>التاريخ: <b>${j.date}</b> - دقائق إضافية مبررة: <b>${j.extra_minutes}</b></li>`;
				});
				summary += '</ul>';
				frappe.confirm(
					__('سيتم تطبيق المبررات التالية:') + '<br>' + summary + '<br>' + __('هل تريد المتابعة؟'),
					function() {
						let applied_count = 0;
						let existing_names = (frm.doc.extra_hours_details || []).map(row => row.attendance_name);
						justifications.forEach(j => {
							if (!existing_names.includes(j.name)) {
								let row = frm.add_child('extra_hours_details');
								row.attendance_date = j.date;
								// Laisser attendance_name vide si pas d'attendance liée
								// row.attendance_name = "";
								row.extra_hours = (j.extra_minutes || 0) / 60.0;
								row.approved_extra_hours = (j.extra_minutes || 0) / 60.0;
								row.status = 'Approved';
								row.comments = __('مبرر مستورد من EXTRA HOURS REQUEST');
								applied_count++;
							}
						});
						frm.refresh_field('extra_hours_details');
						frappe.msgprint(__('تم تطبيق المبررات على {0} صف/صفوف.', [applied_count]));
					},
					function() {
						frappe.msgprint(__('لم يتم تطبيق أي تصحيح.'));
					}
				);
			} else {
				frappe.msgprint(__('حدث خطأ أثناء جلب المبررات: ') + (r.message && r.message.error || 'خطأ غير معروف'));
			}
		}
	});
}
