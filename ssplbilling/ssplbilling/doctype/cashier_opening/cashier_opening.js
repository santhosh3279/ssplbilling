// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

const DENOMINATIONS = [500, 200, 100, 50, 20, 10, 5, 2, 1];

function calculate_total(frm) {
	let total = 0;
	DENOMINATIONS.forEach((d) => {
		const count = parseFloat(frm.doc[String(d)]) || 0;
		total += count * d;
	});
	frm.set_value("total", total);
}

frappe.ui.form.on("Cashier_Opening", {
	refresh(frm) {
		frm.set_df_property("total", "read_only", 1);
		calculate_total(frm);
	},
	"500": calculate_total,
	"200": calculate_total,
	"100": calculate_total,
	"50": calculate_total,
	"20": calculate_total,
	"10": calculate_total,
	"5": calculate_total,
	"2": calculate_total,
	"1": calculate_total,
});
