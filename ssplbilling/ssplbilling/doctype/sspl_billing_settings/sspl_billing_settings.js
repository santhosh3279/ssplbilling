// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("SSPL Billing Settings", {
	refresh(frm) {
		load_series_options(frm);
	},
});

// Also refresh options when a row's detail form is opened (popup edit)
frappe.ui.form.on("SSPL Billing Series", {
	form_render(frm) {
		load_series_options(frm);
	},
});

function load_series_options(frm) {
	frappe.call({
		method: "ssplbilling.api.sales_api.get_naming_series",
		args: {
			doctypes: ["Sales Invoice", "Purchase Invoice"]
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
