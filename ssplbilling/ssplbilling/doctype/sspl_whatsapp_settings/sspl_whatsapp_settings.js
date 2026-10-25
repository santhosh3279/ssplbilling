// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

const AUTO_REFRESH_GAP_MS = 30 * 1000;

frappe.ui.form.on("SSPL WhatsApp Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Refresh Status"), () => refresh_session(frm, false));
		load_session_names(frm);
		set_user_session_options(frm);

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

frappe.ui.form.on("SSPL WhatsApp Session", {
	session_name(frm, cdt, cdn) {
		fill_session_row(frm, cdt, cdn);
		set_user_session_options(frm);
	},
	sessions_remove(frm) {
		set_user_session_options(frm);
	},
});

// Users per Session offers the sessions listed in the Sessions table above
function set_user_session_options(frm) {
	const names = (frm.doc.sessions || []).map((row) => row.session_name).filter(Boolean);
	frm.fields_dict.session_users.grid.update_docfield_property(
		"session_name",
		"options",
		["", ...new Set(names)].join("\n")
	);
	frm.refresh_field("session_users");
}

// Picking a session fills its read-only details from the gateway, so the row shows what it links
function fill_session_row(frm, cdt, cdn) {
	const name = locals[cdt][cdn].session_name;
	const clear = { session_id: "", status: "", phone: "", push_name: "" };
	if (!name) {
		frappe.model.set_value(cdt, cdn, clear);
		return;
	}
	frappe.call({
		method: "ssplbilling.api.whatsapp_api.get_gateway_session",
		args: { session_name: name },
		callback(r) {
			// A slower reply for a name since changed again must not overwrite the newer one
			if (locals[cdt][cdn]?.session_name !== name) return;
			frappe.model.set_value(cdt, cdn, { ...clear, ...(r.message || {}) });
		},
	});
}

// Session Name offers the gateway's sessions; the rows' own names stay listed so a session
// missing from the gateway still shows instead of turning blank
function load_session_names(frm) {
	frappe.call({
		method: "ssplbilling.api.whatsapp_api.list_gateway_sessions",
		// A dead or unconfigured gateway must not pop an error just for opening the form
		silent: true,
		callback(r) {
			const names = new Set(r.message || []);
			(frm.doc.sessions || []).forEach((row) => row.session_name && names.add(row.session_name));
			frm.fields_dict.sessions.grid.update_docfield_property(
				"session_name",
				"options",
				["", ...[...names].sort()].join("\n")
			);
			frm.refresh_field("sessions");
		},
	});
}

// refresh_sessions mirrors each row's gateway session onto this record, so only a reload follows
function refresh_session(frm, auto) {
	if (frm.is_dirty()) {
		// Reloading would throw away the unsaved edits
		if (!auto) frappe.msgprint(__("Save the settings before refreshing the session status"));
		return;
	}
	if (!frm.doc.base_url) return;

	frappe.call({
		method: "ssplbilling.api.whatsapp_api.refresh_sessions",
		type: "POST",
		// A dead or unconfigured gateway must not pop an error just for opening the form
		silent: auto,
		freeze: !auto,
		freeze_message: __("Checking OpenWA sessions..."),
		callback() {
			frm.reload_doc();
			if (!auto)
				frappe.show_alert({ message: __("Session status refreshed"), indicator: "green" });
		},
	});
}
