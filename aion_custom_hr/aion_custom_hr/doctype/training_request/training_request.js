// Copyright (c) 2025, ard and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Training Request", {
// 	refresh(frm) {

// 	},
// });


// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Training Request", {
	onload_post_render: function (frm) {
		frm.get_field("employees").grid.set_multiple_add("employee");
	},
	refresh: function (frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.docstatus === 1) { // Si le document est soumis
				frm.add_custom_button(__("Create Training Event"), function () {
					frappe.model.with_doctype("Training Event", function() {
						let training_event = frappe.model.get_new_doc("Training Event");
						
						// Copier les informations de base
						training_event.training_request = frm.doc.name;
						training_event.event_name = frm.doc.training_name || frm.doc.name;
						training_event.training_program = frm.doc.training_program;
						training_event.type = frm.doc.type;
						training_event.trainer_name = frm.doc.trainer_name;
						training_event.trainer_email = frm.doc.trainer_email;
						training_event.course = frm.doc.course;
                        training_event.start_time = frm.doc.start_time;
                        training_event.end_time = frm.doc.end_time;
						training_event.company = frm.doc.company;
						training_event.location = frm.doc.location;
						training_event.introduction = frm.doc.introduction;
						
						// Copier la liste des employés
						if (frm.doc.employees) {
							frm.doc.employees.forEach(function(employee) {
								let attendee = frappe.model.add_child(training_event, "employees");
								attendee.employee = employee.employee;
								attendee.employee_name = employee.employee_name;
							});
						}
						
						frappe.set_route("Form", "Training Event", training_event.name);
					});
				}, __("Create"));
			}
			
			frm.add_custom_button(__("Training Result"), function () {
				frappe.route_options = {
					training_event: frm.doc.name,
				};
				frappe.set_route("List", "Training Result");
			});
			frm.add_custom_button(__("Training Feedback"), function () {
				frappe.route_options = {
					training_event: frm.doc.name,
				};
				frappe.set_route("List", "Training Feedback");
			});
		}
		frm.events.set_employee_query(frm);
	},

	set_employee_query: function (frm) {
		let emp = [];
		for (let d in frm.doc.employees) {
			if (frm.doc.employees[d].employee) {
				emp.push(frm.doc.employees[d].employee);
			}
		}
		frm.set_query("employee", "employees", function () {
			return {
				filters: {
					name: ["NOT IN", emp],
					status: "Active",
				},
			};
		});
	},
});

frappe.ui.form.on("Training Event Employee", {
	employee: function (frm) {
		frm.events.set_employee_query(frm);
	},
});