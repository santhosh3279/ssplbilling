// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Incentive Redeem", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.incentive_ledger) {
			frappe.db.get_single_value("Incentive Rule", "incentive_ledger").then((val) => {
				if (val) {
					frm.set_value("incentive_ledger", val);
				}
			});
		}
	},
});
