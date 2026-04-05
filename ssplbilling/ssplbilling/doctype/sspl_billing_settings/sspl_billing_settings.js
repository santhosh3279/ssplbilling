// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("SSPL Billing Settings", {
	refresh(frm) {
		load_series_options(frm);
		load_tax_template_options(frm);
	},
});

// Also refresh options when a row's detail form is opened (popup edit)
frappe.ui.form.on("SSPL Billing Series", {
	form_render(frm) {
		load_series_options(frm);
		load_tax_template_options(frm);
	},
});

function load_series_options(frm) {
	frappe.call({
		method: "ssplbilling.api.SaleEntry_api.get_naming_series",
		args: {
			doctypes: ["Sales Invoice", "Purchase Invoice", "Sales Order", "Purchase Order", "Quotation"]
		},
		callback(r) {
			const series = r.message;
			if (!series || !series.length) return;

			const options = "\n" + series.join("\n");

			// 1. Patch Frappe's global meta cache so every future grid row
			//    render picks up the options without another API call.
			const docfield = frappe.meta.get_docfield("SSPL Billing Series", "series");
			if (docfield) docfield.options = options;

			// 2. Update the live grid's field definition.
			frm.fields_dict["billing_series"].grid.update_docfield_property(
				"series",
				"options",
				options
			);

			// 3. Re-render existing rows so they show the populated dropdown.
			frm.fields_dict["billing_series"].grid.refresh();
		},
	});
}

function load_tax_template_options(frm) {
	Promise.all([
		frappe.db.get_list("Sales Taxes and Charges Template", { fields: ["name"], limit: 0, order_by: "name asc" }),
		frappe.db.get_list("Purchase Taxes and Charges Template", { fields: ["name"], limit: 0, order_by: "name asc" }),
	]).then(([salesTemplates, purchaseTemplates]) => {
		const names = [
			...salesTemplates.map((t) => t.name),
			...purchaseTemplates.map((t) => t.name),
		];
		const options = "\n" + names.join("\n");

		// 1. Patch Frappe's global meta cache.
		const docfield = frappe.meta.get_docfield("SSPL Billing Series", "tax_template");
		if (docfield) docfield.options = options;

		// 2. Update the live grid's field definition.
		frm.fields_dict["billing_series"].grid.update_docfield_property(
			"tax_template",
			"options",
			options
		);

		// 3. Re-render existing rows.
		frm.fields_dict["billing_series"].grid.refresh();
	});
}
