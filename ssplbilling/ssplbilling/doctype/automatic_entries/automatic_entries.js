frappe.ui.form.on('Automatic Entries', {
	onload: function(frm) {
		frappe.call({
			method: 'ssplbilling.api.automatic_entries_api.get_payment_entry_series',
			callback: function(r) {
				if (r.message) {
					let options = r.message;
					if (Array.isArray(options)) {
						options = ['', ...options].join('\n');
					}
					frm.set_df_property('payment_entry_naming_settings', 'options', options);
					frm.refresh_field('payment_entry_naming_settings');
				}
			}
		});
	}
});
