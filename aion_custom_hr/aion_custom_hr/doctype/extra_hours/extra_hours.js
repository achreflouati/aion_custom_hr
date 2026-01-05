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
						// تطبيق التصحيح بعد التأكيد
						let applied_count = 0;
						justifications.forEach(j => {
							// (frm.doc.details || []).forEach(row => {
							//     if (row.attendance_date === j.date) {
							//         row.extra_minutes_justified = (row.extra_minutes_justified || 0) + (j.extra_minutes || 0);
							//         applied_count++;
							//     }
							// });
						});
						frappe.msgprint(__('تم تطبيق المبررات على {0} صف/صفوف.', [applied_count]));
						// frm.refresh_field('details');
						// schedule_save(frm);
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
