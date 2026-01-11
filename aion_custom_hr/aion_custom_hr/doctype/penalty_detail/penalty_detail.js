// Ajoute un popup de justification sur le bouton justifications_btn2
frappe.ui.form.on('Penalty Detail', {
    justifications_btn2: function(frm) {
        frappe.prompt([
            {
                fieldtype: 'Small Text',
                label: 'Justification',
                fieldname: 'justification',
                reqd: 1
            }
        ],
        function(values) {
            frm.set_value('correction_note', values.justification);
            frm.save();
        },
        'Justification',
        'Enregistrer'
        );
    }
});
