// Copyright (c) 2026, SSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("SSPL WhatsApp Template", {
	refresh(frm) {
		render_fields(frm);
		// Clicking a field button blurs Message, so remember where its cursor was
		frm.__msg_cursor = null;
		frm.fields_dict.message?.$input?.off("blur.sspl").on("blur.sspl", function () {
			frm.__msg_cursor = [this.selectionStart, this.selectionEnd];
		});
	},
	usage_area(frm) {
		frm.__fields_doctype = null;
		render_fields(frm);
	},
});

// Lists the placeholders the chosen usage area fills; clicking one inserts it into Message
function render_fields(frm) {
	const wrapper = frm.fields_dict.available_fields?.$wrapper;
	if (!wrapper) return;
	const area = frm.doc.usage_area;
	if (!area) {
		wrapper.empty();
		return;
	}
	frappe.call({
		method: "ssplbilling.api.whatsapp_api.get_template_fields",
		args: { usage_area: area, doctype: frm.__fields_doctype },
		callback(r) {
			// A slower reply for an area since changed must not overwrite the newer list
			if (frm.doc.usage_area !== area) return;
			const data = r.message;
			if (!data) {
				wrapper.empty();
				return;
			}
			wrapper.html(fields_html(data));
			wrapper.find("[data-placeholder]").on("click", function () {
				insert_placeholder(frm, $(this).attr("data-placeholder"));
			});
			wrapper.find("select[data-doctype]").on("change", function () {
				frm.__fields_doctype = $(this).val();
				render_fields(frm);
			});
		},
	});
}

function fields_html(data) {
	const esc = frappe.utils.escape_html;
	const chip = (f, own) => `
		<button type="button" class="btn btn-xs ${own ? "btn-primary" : "btn-default"}"
			style="margin: 0 6px 6px 0" data-placeholder="${esc(f.placeholder)}" title="${esc(f.label)}">
			{{${esc(f.placeholder)}}} <span class="${own ? "" : "text-muted"}">${esc(f.label)}</span>
		</button>`;
	const own = data.fields.slice(0, data.own_count);
	const doc_fields = data.fields.slice(data.own_count);
	const picker =
		data.doctypes.length > 1
			? `<select data-doctype class="form-control input-xs" style="display:inline-block;width:auto;margin-left:6px">
				${data.doctypes
					.map(
						(d) =>
							`<option value="${esc(d)}" ${d === data.doctype ? "selected" : ""}>${esc(
								__(d)
							)}</option>`
					)
					.join("")}
			</select>`
			: esc(__(data.doctype));
	return `
		<div class="form-group">
			<label class="control-label">${__("Available Fields")}</label>
			${data.note ? `<p class="text-muted small">${esc(data.note)}</p>` : ""}
			${own.length ? `<div>${own.map((f) => chip(f, true)).join("")}</div>` : ""}
			<p class="text-muted small" style="margin-top:6px">${__("Fields of")} ${picker}</p>
			<div style="max-height:220px;overflow-y:auto">${doc_fields.map((f) => chip(f, false)).join("")}</div>
		</div>`;
}

// Inserts {{placeholder}} where the Message cursor last was (at the end when it was never focused)
function insert_placeholder(frm, placeholder) {
	const token = `{{${placeholder}}}`;
	const input = frm.fields_dict.message?.$input?.get(0);
	const text = frm.doc.message || "";
	const [start, end] = frm.__msg_cursor || [text.length, text.length];
	const at = start + token.length;
	frm.set_value("message", text.slice(0, start) + token + text.slice(end)).then(() => {
		frm.__msg_cursor = [at, at];
		if (!input) return;
		input.focus();
		input.setSelectionRange(at, at);
	});
}
