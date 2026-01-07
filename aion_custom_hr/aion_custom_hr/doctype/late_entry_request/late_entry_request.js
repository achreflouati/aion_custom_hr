// Copyright (c) 2026, ard and contributors
// For license information, please see license.txt


frappe.ui.form.on("Late Entry Request", {
	onload: function(frm) {
		// Auto-fill employee with current session user if empty
		if (!frm.doc.employee) {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Employee",
					filters: { user_id: frappe.session.user },
					fields: ["name", "employee_name"]
				},
				callback: function(r) {
					if (r.message && r.message.length > 0) {
						frm.set_value("employee", r.message[0].name);
						if (r.message[0].employee_name) {
							frm.set_value("employee_name", r.message[0].employee_name);
						} else {
							frappe.msgprint("Employee name not found for this user.", "Warning");
						}
					} else {
						frappe.msgprint("No Employee record is linked to your user account. Please contact HR.", "Warning");
					}
				},
				error: function() {
					frappe.msgprint("An error occurred while fetching the Employee record.", "Error");
				}
			});
		}
	},
	from_datetime: function(frm) {
		// Always auto-fill to_datetime with from_datetime
		if (frm.doc.from_datetime) {
			frm.set_value("to_datetime", frm.doc.from_datetime);
			frm.set_df_property("to_datetime", "read_only", 1);
		}
	},
	   reason: function(frm) {
		   handle_reason_logic(frm);
		   // Calcul automatique après changement de raison
		   setTimeout(function() {
			   calculate_nb_minutes_late(frm);
			   calculate_nb_minutes_early_exit(frm);
			   frm.refresh_field("nb_hours_late");
			   frm.refresh_field("nb_hours_early_exit");
		   }, 300);
	   },
	   from_time: function(frm) {
		   calculate_nb_minutes_late(frm);
		   calculate_nb_minutes_early_exit(frm);
	   },
	   to_time: function(frm) {
		   calculate_nb_minutes_late(frm);
		   calculate_nb_minutes_early_exit(frm);
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
		// Try to auto-fill shift from employee and set employee_name
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
						if (emp.employee_name) {
							frm.set_value("employee_name", emp.employee_name);
						} else {
							frappe.msgprint("Employee name not found for this employee record.", "Warning");
						}
					} else {
						frappe.msgprint("Employee record not found.", "Warning");
					}
				},
				error: function() {
					frappe.msgprint("An error occurred while fetching the Employee record.", "Error");
				}
			});
		} else {
			frappe.msgprint("Please select an employee.", "Warning");
		}
		handle_reason_logic(frm);
	}
});

async function handle_reason_logic(frm) {
	const reason = frm.doc.reason;
	   if (!frm.doc.shift || !frm.doc.employee) return;

	   frappe.call({
		   method: "frappe.client.get",
		   args: {
			   doctype: "Shift Type",
			   name: frm.doc.shift
		   },
		   callback: function(r) {
			   if (!r.message) return;
			   const shift = r.message;
			   if (reason === "Early Exit") {
				   frm.set_df_property("from_time", "read_only", 0);
				   frm.set_df_property("to_time", "read_only", 1);
				   if (shift.end_time) {
					   frm.set_value("to_time", shift.end_time);
				   }
				   frm.set_df_property("nb_hours_early_exit", "hidden", 0);
				   frm.set_df_property("nb_hours_late", "hidden", 1);
				   frm.refresh_field("nb_hours_early_exit");
				   frm.refresh_field("nb_hours_late");
			   } else if (reason === "Late") {
				   frm.set_df_property("from_time", "read_only", 1);
				   frm.set_df_property("to_time", "read_only", 0);
				   if (shift.start_time) {
					   frm.set_value("from_time", shift.start_time);
				   }
				   frm.set_df_property("nb_hours_early_exit", "hidden", 1);
				   frm.set_df_property("nb_hours_late", "hidden", 0);
				   frm.refresh_field("nb_hours_early_exit");
				   frm.refresh_field("nb_hours_late");
			   } else {
				   frm.set_df_property("from_time", "read_only", 0);
				   frm.set_df_property("to_time", "read_only", 0);
				   frm.set_df_property("nb_hours_early_exit", "hidden", 1);
				   frm.set_df_property("nb_hours_late", "hidden", 1);
				   frm.refresh_field("nb_hours_early_exit");
				   frm.refresh_field("nb_hours_late");
			   }
		   }
	   });
	}

 function calculate_nb_minutes_early_exit(frm) {
		console.log("Calculating nb_hours_early_exit...");

		if (frm.doc.reason === "Early Exit" && frm.doc.from_time && frm.doc.to_time) {
		// Conversion des heures "HH:MM:SS" en minutes
		
		function timeToMinutes(t) {
			const [h, m, s] = t.split(":").map(Number);
			return h * 60 + m + (s ? s / 60 : 0);
		}
		const fromMins = timeToMinutes(frm.doc.from_time);
		const toMins = timeToMinutes(frm.doc.to_time);
		let diff = toMins - fromMins;
		if (diff < 0) diff = 0;
		console.log("Difference in minutes:", diff);
		frm.set_value("nb_hours_early_exit", Math.round(diff));
	} else {
		frm.set_value("nb_hours_early_exit", 0);
	}
		  // Si le motif est "Early Exit", calculer la différence en minutes entre shift_end et to_time
		  
	   }
	  

function calculate_nb_minutes_late(frm) {
	console.log("Calculating nb_hours_late1...");
	// Si le motif est "Late", calculer la différence entre from_time et to_time en heures décimales
	if (frm.doc.reason === "Late" && frm.doc.from_time && frm.doc.to_time) {
		// Conversion des heures "HH:MM:SS" en minutes
		console.log("Calculating nb_hours_late...");
		function timeToMinutes(t) {
			const [h, m, s] = t.split(":").map(Number);
			return h * 60 + m + (s ? s / 60 : 0);
		}
		const fromMins = timeToMinutes(frm.doc.from_time);
		const toMins = timeToMinutes(frm.doc.to_time);
		let diff = toMins - fromMins;
		if (diff < 0) diff = 0;
		console.log("Difference in minutes:", diff);
		frm.set_value("nb_hours_late", Math.round(diff));
	} else {
		frm.set_value("nb_hours_late", 0);
	}
}

