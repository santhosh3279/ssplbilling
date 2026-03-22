// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Discount Rule", {
	refresh(frm) {
		apply_custom_logic_columns(frm);
	},
	discount_type(frm) {
		apply_custom_logic_columns(frm);
	},
	custom_logic_type(frm) {
		apply_custom_logic_columns(frm);
	},
});

function apply_custom_logic_columns(frm) {
	if (frm.doc.discount_type !== "Custom Logic") return;
	const grid = frm.fields_dict.custom_logic_table && frm.fields_dict.custom_logic_table.grid;
	if (!grid) return;
	const type = frm.doc.custom_logic_type;
	// Product selected → disable Percentage column; Percentage selected → disable Nos column
	grid.toggle_enable("nos", type !== "Percentage");
	grid.toggle_enable("percentage", type !== "Product");
	grid.refresh();
}
