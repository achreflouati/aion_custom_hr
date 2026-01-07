// Copyright (c) 2026, ard and contributors
// For license information, please see license.txt


frappe.ui.form.on("Late Entry Request", {
	from_datetime: function(frm) {
		// Always auto-fill to_datetime with from_datetime
		if (frm.doc.from_datetime) {
			frm.set_value("to_datetime", frm.doc.from_datetime);
			frm.set_df_property("to_datetime", "read_only", 1);
		}
	},
	reason: function(frm) {
		handle_reason_logic(frm);
	},
	from_time: function(frm) {
		calculate_nb_minutes_late(frm);
	},
	to_time: function(frm) {
		calculate_nb_minutes_late(frm);
	},
	from_date: function(frm) {
		handle_reason_logic(frm);
	},
	to_date: function(frm) {
		handle_reason_logic(frm);
	},
	shift: function(frm) {
		handle_reason_logic(frm);
	},
	employee: function(frm) {
		// Try to auto-fill shift from employee
		if (frm.doc.employee) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Employee",
					name: frm.doc.employee
				},
				callback: function(r) {
					if (r.message) {
						const emp = r.message;
						if (emp.default_shift) {
							frm.set_value("shift", emp.default_shift);
						} else {
							frm.set_value("shift", null);
							frappe.msgprint("This employee does not have a default shift assigned.", "Warning");
						}
					}
				}
			});
		}
		handle_reason_logic(frm);
	}
});

async function handle_reason_logic(frm) {
	const reason = frm.doc.reason;
	if (!frm.doc.shift || !frm.doc.employee) return;

	// Fetch shift timings from server (customize as needed)
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Shift Type",
			name: frm.doc.shift
		},
		callback: function(r) {
			if (!r.message) return;
			const shift = r.message;
			// Assume fields: start_time, end_time (adjust if needed)
			if (reason === "Late") {
				frm.set_df_property("from_time", "read_only", 0);
				frm.set_df_property("to_time", "read_only", 1);
				if (shift.end_time) {
					frm.set_value("to_time", shift.end_time);
				}
			} else if (reason === "Early Exit") {
				frm.set_df_property("from_time", "read_only", 1);
				frm.set_df_property("to_time", "read_only", 0);
				if (shift.start_time) {
					frm.set_value("from_time", shift.start_time);
				}
			} else {
				frm.set_df_property("from_time", "read_only", 0);
				frm.set_df_property("to_time", "read_only", 0);
			}
		}
	});
}


function calculate_nb_minutes_late(frm) {
	// Optionally, implement calculation based on from_date, to_date, from_time, to_time
	if (frm.doc.from_date && frm.doc.to_date && frm.doc.from_time && frm.doc.to_time) {
		const from = frappe.datetime.combine_date_and_time(frm.doc.from_date, frm.doc.from_time);
		const to = frappe.datetime.combine_date_and_time(frm.doc.to_date, frm.doc.to_time);
		if (from && to && to > from) {
			const diff_ms = to - from;
			const diff_hours = diff_ms / (1000 * 60 * 60);
			frm.set_value("nb_hours_late", Math.round(diff_hours * 100) / 100);
		} else {
			frm.set_value("nb_hours_late", 0);
		}
	} else {
		frm.set_value("nb_hours_late", 0);
	}
}
