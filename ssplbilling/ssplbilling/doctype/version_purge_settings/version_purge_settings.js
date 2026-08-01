// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Version Purge Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Purge Now"), () => {
			frappe.confirm(__("Are you sure you want to purge old Version history records now?"), () => {
				frm.call("purge_now").then(r => {
					const count = r.message || 0;
					frappe.msgprint({
						title: __("Purge Completed"),
						indicator: "green",
						message: __("Successfully purged {0} old Version records (without writing to Deleted Document).", [count])
					});
				});
			});
		});
	},
});
