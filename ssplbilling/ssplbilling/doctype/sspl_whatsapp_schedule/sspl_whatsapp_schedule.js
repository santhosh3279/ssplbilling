// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

const SCHEDULER = "ssplbilling.api.whatsapp_scheduler";

frappe.ui.form.on("SSPL WhatsApp Schedule", {
	setup(frm) {
		// Table MultiSelect has no grid: the query goes on the field itself
		frm.set_query("cost_centers", () => ({
			filters: { company: frm.doc.company, is_group: 0 },
		}));
	},

	onload(frm) {
		frappe.call("ssplbilling.api.whatsapp_api.get_settings").then(({ message }) => {
			const names = (message.sessions || []).map((s) => s.session_name);
			frm.set_df_property("session_name", "options", ["", ...names].join("\n"));
			if (!frm.doc.session_name && names.length === 1) frm.set_value("session_name", names[0]);
			frm.refresh_field("session_name");
		});
	},

	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Preview"), () => ask_date(frm, __("Preview"), preview));
		frm.add_custom_button(__("Send Now"), () => ask_date(frm, __("Send Now"), send_now));
	},
});

function ask_date(frm, title, action) {
	if (frm.is_dirty()) {
		frappe.msgprint(__("Save the schedule first"));
		return;
	}
	const today = frappe.datetime.get_today();
	frappe.prompt(
		{
			fieldname: "report_date",
			fieldtype: "Date",
			label: __("Report Date"),
			reqd: 1,
			default: frm.doc.report_period === "Previous Day" ? frappe.datetime.add_days(today, -1) : today,
		},
		(v) => action(frm, v.report_date),
		title,
		title,
	);
}

function preview(frm, report_date) {
	frappe.call(`${SCHEDULER}.preview`, { name: frm.doc.name, report_date }).then(({ message }) => {
		const accounts = (message.upi_accounts || []).join(", ") || __("none found");
		frappe.msgprint({
			title: __("Preview"),
			message:
				`<pre style="white-space:pre-wrap;font-family:inherit">${frappe.utils.escape_html(message.message)}</pre>` +
				(frm.doc.report_type === "Daily Sales Summary" && frm.doc.include_upi ? `<div class="text-muted small">${__("UPI accounts")}: ${frappe.utils.escape_html(accounts)}</div>` : ""),
		});
	});
}

function send_now(frm, report_date) {
	frappe
		.call({ method: `${SCHEDULER}.send_now`, args: { name: frm.doc.name, report_date }, freeze: true })
		.then(({ message }) => {
			const errors = (message.errors || []).map(frappe.utils.escape_html).join("<br>");
			frappe.msgprint({
				title: message.status,
				indicator: message.status === "Sent" ? "green" : message.status === "Partial" ? "orange" : "red",
				message:
					(message.skipped ? __("Nothing due on that day: no message sent.") : __("Sent to {0} recipient(s).", [message.sent])) +
					(errors ? `<br><br>${errors}` : ""),
			});
			frm.reload_doc();
		});
}
