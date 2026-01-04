// Copyright (c) 2026, ard and contributors
// For license information, please see license.txt

frappe.ui.form.on("Late Entry Request", {
	from_datetime: function(frm) {
		calculate_nb_minutes_late(frm);
	},
	to_datetime: function(frm) {
		calculate_nb_minutes_late(frm);
	}
});

function calculate_nb_minutes_late(frm) {
	if (frm.doc.from_datetime && frm.doc.to_datetime) {
		const from = frappe.datetime.str_to_obj(frm.doc.from_datetime);
		const to = frappe.datetime.str_to_obj(frm.doc.to_datetime);
		if (from && to && to > from) {
			const diff_ms = to - from;
			const diff_minutes = diff_ms / (1000 * 60);
			frm.set_value("nb_hours_late", Math.round(diff_minutes));
		} else {
			frm.set_value("nb_hours_late", 0);
		}
	} else {
		frm.set_value("nb_hours_late", 0);
	}
}
