// Copyright (c) 2026, ard and contributors
// For license information, please see license.txt


frappe.ui.form.on("EXTRA HOURS REQUEST", {
	from_datetime: function(frm) {
		calculate_extra_minutes(frm);
	},
	to_datetime: function(frm) {
		calculate_extra_minutes(frm);
	}
});

// function calculate_extra_minutes(frm) {
// 	if (frm.doc.from_datetime && frm.doc.to_datetime) {
// 		let from = frappe.datetime.moment(frm.doc.from_datetime);
// 		let to = frappe.datetime.moment(frm.doc.to_datetime);
// 		let diff = to.diff(from, 'minutes');
// 		frm.set_value('nb_minutes_extra', diff > 0 ? diff : 0);
// 	} else {
// 		frm.set_value('nb_minutes_extra', 0);
// 	}
// }


function calculate_extra_minutes(frm) {
	if (frm.doc.from_datetime && frm.doc.to_datetime) {
		const from = frappe.datetime.str_to_obj(frm.doc.from_datetime);
		const to = frappe.datetime.str_to_obj(frm.doc.to_datetime);
		if (from && to && to > from) {
			const diff_ms = to - from;
			const diff_minutes = diff_ms / (1000 * 60);
			frm.set_value("nb_minutes_extra", Math.round(diff_minutes));
		} else {
			frm.set_value("nb_minutes_extra", 0);
		}
	} else {
		frm.set_value("nb_minutes_extra", 0);
	}
}