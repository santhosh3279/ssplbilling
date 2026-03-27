frappe.ui.form.on("Loading Receipt", {
	refresh(frm) {
		frm.trigger("calculate_total");
	},
	calculate_total(frm) {
		let total = 0;
		(frm.doc.loading_items || []).forEach((row) => {
			total += row.amount || 0;
		});
		frm.set_value("total", total);
	},
});

frappe.ui.form.on("Loading Receipt Item", {
	qty(frm, cdt, cdn) {
		calculate_row_amount(frm, cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		calculate_row_amount(frm, cdt, cdn);
	},
	loading_items_remove(frm) {
		frm.trigger("calculate_total");
	},
});

function calculate_row_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const amount = (row.qty || 0) * (row.rate || 0);
	frappe.model.set_value(cdt, cdn, "amount", amount);
	frm.trigger("calculate_total");
}
