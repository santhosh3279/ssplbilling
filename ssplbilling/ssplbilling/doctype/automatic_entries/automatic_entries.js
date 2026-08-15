frappe.ui.form.on('Automatic Entries', {
	onload: function(frm) {
		const naming_fields = [
			['payment_entry_naming_settings', 'ssplbilling.api.automatic_entries_api.get_payment_entry_series'],
			['journal_entry_naming_settings', 'ssplbilling.api.automatic_entries_api.get_journal_entry_series'],
		];
		naming_fields.forEach(function([fieldname, method]) {
			frappe.call({
				method: method,
				callback: function(r) {
					if (r.message) {
						let options = r.message;
						if (Array.isArray(options)) {
							options = ['', ...options].join('\n');
						}
						frm.set_df_property(fieldname, 'options', options);
						frm.refresh_field(fieldname);
					}
				}
			});
		});
	}
});
