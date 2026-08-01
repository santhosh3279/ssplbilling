// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Version Purge Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Purge Now"), () => {
			frappe.confirm(__("Are you sure you want to purge old records now?"), () => {
				frm.call("purge_now").then(r => {
					const res = r.message || { versions: 0, deleted_docs: 0 };
					frappe.msgprint({
						title: __("Purge Completed"),
						indicator: "green",
						message: __("Successfully purged:<br>- {0} Version records (without writing to Deleted Document)<br>- {1} Deleted Document records.", [res.versions || 0, res.deleted_docs || 0])
					});
				});
			});
		});
	},
});
