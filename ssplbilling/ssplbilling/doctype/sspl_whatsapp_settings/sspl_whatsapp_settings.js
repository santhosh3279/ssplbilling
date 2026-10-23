// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

const AUTO_REFRESH_GAP_MS = 30 * 1000;

frappe.ui.form.on("SSPL WhatsApp Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Refresh Status"), () => refresh_session(frm, false));

		// Desk reuses this form across visits, so gate on time: each reopen refreshes, while the
		// reload that follows a refresh (which fires `refresh` again) does not loop
		const now = Date.now();
		if (
			!frm.__session_refreshed_at ||
			now - frm.__session_refreshed_at > AUTO_REFRESH_GAP_MS
		) {
			frm.__session_refreshed_at = now;
			refresh_session(frm, true);
		}
	},
});

// get_status mirrors the gateway's session onto this record, so the form only needs a reload after it
function refresh_session(frm, auto) {
	if (frm.is_dirty()) {
		// Reloading would throw away the unsaved edits
		if (!auto) frappe.msgprint(__("Save the settings before refreshing the session status"));
		return;
	}
	if (!frm.doc.base_url) return;

	frappe.call({
		method: "ssplbilling.api.whatsapp_api.get_status",
		type: "POST",
		// A dead or unconfigured gateway must not pop an error just for opening the form
		silent: auto,
		freeze: !auto,
		freeze_message: __("Checking OpenWA session..."),
		callback() {
			frm.reload_doc();
			if (!auto)
				frappe.show_alert({ message: __("Session status refreshed"), indicator: "green" });
		},
	});
}
