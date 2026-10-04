import frappe
from frappe.utils import flt, getdate

def _cost_center_document_names(doctype, child_doctype, date_field, from_date, to_date, cost_center, company):
        """Find documents assigned to a cost center on the header or a detail row."""
        parent_meta = frappe.get_meta(doctype)
        header_match = "doc.cost_center = %s" if parent_meta.has_field("cost_center") else None
        child_match = None
        if child_doctype and frappe.get_meta(child_doctype).has_field("cost_center"):
                child_match = (
                        f"EXISTS (SELECT 1 FROM `tab{child_doctype}` child "
                        "WHERE child.parent = doc.name AND child.cost_center = %s)"
                )
        matches = [part for part in (header_match, child_match) if part]
        if not matches:
                return []
        params = [from_date, to_date]
        conditions = [f"doc.{date_field} BETWEEN %s AND %s", "doc.docstatus < 2"]
        if company and parent_meta.has_field("company"):
                conditions.append("doc.company = %s")
                params.append(company)
        params.extend([cost_center] * len(matches))
        return frappe.db.sql(
                f"SELECT doc.name FROM `tab{doctype}` doc "
                f"WHERE {' AND '.join(conditions)} AND ({' OR '.join(matches)})",
                tuple(params), pluck=True,
        )


def _filter_cost_center(filters, doctype, child_doctype, date_field, from_date, to_date, cost_center, company):
        if cost_center:
                names = _cost_center_document_names(
                        doctype, child_doctype, date_field, from_date, to_date, cost_center, company
                )
                filters["name"] = ["in", names or [""]]


def _add_journal_accounts_and_parties(journals):
        """Summarize account sides and party display names without duplicating journals."""
        if not journals:
                return journals
        lines = frappe.get_all(
                "Journal Entry Account",
                filters={"parent": ["in", [journal.name for journal in journals]],
                         "parenttype": "Journal Entry", "parentfield": "accounts"},
                fields=["parent", "account", "party_type", "party", "debit", "credit",
                        "debit_in_account_currency", "credit_in_account_currency"],
                order_by="parent asc, idx asc",
                limit=0,
        )
        parties_by_type = {}
        for line in lines:
                if line.party_type and line.party:
                        parties_by_type.setdefault(line.party_type, set()).add(line.party)
        party_names = {}
        for party_type, names in parties_by_type.items():
                title_field = frappe.get_meta(party_type).title_field or "name"
                for party in frappe.get_all(
                        party_type, filters={"name": ["in", list(names)]},
                        fields=["name", f"{title_field} as party_name"], limit=0,
                ):
                        party_names[(party_type, party.name)] = party.party_name or party.name

        details = {journal.name: {"paid_from": [], "paid_to": [], "party_name": []} for journal in journals}
        for line in lines:
                detail = details[line.parent]
                if line.account and (flt(line.credit) or flt(line.credit_in_account_currency)):
                        detail["paid_from"].append(line.account)
                if line.account and (flt(line.debit) or flt(line.debit_in_account_currency)):
                        detail["paid_to"].append(line.account)
                if line.party:
                        detail["party_name"].append(party_names.get((line.party_type, line.party), line.party))
        for journal in journals:
                for field, values in details[journal.name].items():
                        journal[field] = ", ".join(dict.fromkeys(values))
        return journals


@frappe.whitelist()
def get_daily_reports(report_type, from_date, to_date, naming_series=None, company=None, cost_center=None):
        """
        Returns a list of documents for a specific date range and type.
        report_type: 'Sales Invoice', 'Purchase Invoice', 'Payment', 'Journal', 'Quotation', 'Loading'
        """
        if not from_date: from_date = frappe.utils.today()
        if not to_date: to_date = frappe.utils.today()

        if report_type == 'Sales Invoice':
                filters = {
                        "posting_date": ["between", [from_date, to_date]],
                        "docstatus": ["<", 2]
                }
                if company:
                        filters["company"] = company
                _filter_cost_center(filters, "Sales Invoice", "Sales Invoice Item", "posting_date", from_date, to_date, cost_center, company)
                if naming_series:
                        if isinstance(naming_series, str):
                                if naming_series.startswith("[") and naming_series.endswith("]"):
                                        import json
                                        try:
                                                naming_series = json.loads(naming_series)
                                        except Exception:
                                                pass
                        if isinstance(naming_series, list):
                                if len(naming_series) > 0:
                                        filters["naming_series"] = ["in", naming_series]
                        else:
                                filters["naming_series"] = naming_series

                return frappe.get_all(
                        "Sales Invoice",
                        filters=filters,
                        fields=["name", "customer_name", "net_total", "grand_total", "total_taxes_and_charges", "docstatus", "posting_date", "posting_time", "naming_series"],
                        order_by="posting_date desc, posting_time desc"
                )

        elif report_type == 'Purchase Invoice':
                filters = {
                        "posting_date": ["between", [from_date, to_date]],
                        "docstatus": ["<", 2]
                }
                if company:
                        filters["company"] = company
                _filter_cost_center(filters, "Purchase Invoice", "Purchase Invoice Item", "posting_date", from_date, to_date, cost_center, company)
                if naming_series:
                        if isinstance(naming_series, str):
                                if naming_series.startswith("[") and naming_series.endswith("]"):
                                        import json
                                        try:
                                                naming_series = json.loads(naming_series)
                                        except Exception:
                                                pass
                        if isinstance(naming_series, list):
                                if len(naming_series) > 0:
                                        filters["naming_series"] = ["in", naming_series]
                        else:
                                filters["naming_series"] = naming_series

                return frappe.get_all(
                        "Purchase Invoice",
                        filters=filters,
                        fields=["name", "supplier_name", "net_total", "grand_total", "total_taxes_and_charges", "docstatus", "posting_date", "posting_time", "naming_series"],
                        order_by="posting_date desc, posting_time desc"
                )

        elif report_type == 'Payment':
                filters = {"posting_date": ["between", [from_date, to_date]], "docstatus": ["<", 2]}
                if company:
                        filters["company"] = company
                _filter_cost_center(filters, "Payment Entry", None, "posting_date", from_date, to_date, cost_center, company)
                return frappe.get_all(
                        "Payment Entry",
                        filters=filters,
                        fields=["name", "party_name", "paid_from", "paid_to", "paid_amount", "received_amount", "mode_of_payment", "docstatus", "posting_date", "payment_type"],
                        order_by="posting_date desc, creation desc"
                )

        elif report_type == 'Journal':
                filters = {"posting_date": ["between", [from_date, to_date]], "docstatus": ["<", 2]}
                if company:
                        filters["company"] = company
                _filter_cost_center(filters, "Journal Entry", 'Journal Entry Account', "posting_date", from_date, to_date, cost_center, company)
                journals = frappe.get_all(
                        "Journal Entry",
                        filters=filters,
                        fields=["name", "voucher_type", "total_debit", "total_credit", "docstatus", "user_remark", "posting_date"],
                        order_by="posting_date desc, creation desc"
                )
                return _add_journal_accounts_and_parties(journals)

        elif report_type == 'Quotation':
                filters = {"transaction_date": ["between", [from_date, to_date]], "docstatus": ["<", 2]}
                if company:
                        filters["company"] = company
                _filter_cost_center(filters, "Quotation", 'Quotation Item', "transaction_date", from_date, to_date, cost_center, company)
                return frappe.get_all(
                        "Quotation",
                        filters=filters,
                        fields=["name", "customer_name", "grand_total", "docstatus", "status", "transaction_date"],
                        order_by="transaction_date desc, creation desc"
                )

        elif report_type == 'Loading':
                company_condition = ""
                params = [from_date, to_date]
                if company and frappe.get_meta("Loading Receipt").has_field("company"):
                        company_condition = " AND lr.company = %s"
                        params.append(company)
                cost_center_condition = ""
                if cost_center:
                        # Loading Receipt has no cost center; its bill number links to a Sales Invoice.
                        cost_center_condition = """ AND EXISTS (
                                SELECT 1 FROM `tabSales Invoice` si
                                WHERE si.name = lr.bill_no AND si.docstatus < 2
                                  AND (si.cost_center = %s OR EXISTS (
                                        SELECT 1 FROM `tabSales Invoice Item` sii
                                        WHERE sii.parent = si.name AND sii.cost_center = %s
                                  ))
                        )"""
                        params.extend([cost_center, cost_center])
                return frappe.db.sql("""
                        SELECT 
                                lr.name, lr.date, lr.customer_name, lr.bill_no,
                                lri.item, lri.item_name, lri.qty, lri.rate, lri.amount
                        FROM `tabLoading Receipt` lr
                        JOIN `tabLoading Receipt Item` lri ON lri.parent = lr.name
                        WHERE lr.date BETWEEN %s AND %s{company_condition}{cost_center_condition}
                        ORDER BY lr.date DESC, lr.creation DESC
                """.format(company_condition=company_condition, cost_center_condition=cost_center_condition), tuple(params), as_dict=True)

        return []

def _voucher_detail_fields(meta, available_keys):
        from frappe.model import no_value_fields, table_fields

        return [
                {"fieldname": field.fieldname, "label": field.label or field.fieldname,
                 "fieldtype": field.fieldtype}
                for field in meta.fields
                if field.fieldname in available_keys
                and field.fieldtype not in (*no_value_fields, *table_fields, "Password")
        ]


@frappe.whitelist()
def get_daily_voucher_details(doctype, name):
        """Return complete readable payment/journal fields and child rows for the detail view."""
        from frappe.model import table_fields

        if doctype not in ("Payment Entry", "Journal Entry"):
                frappe.throw("Only payments and journals are supported.")
        doc = frappe.get_doc(doctype, name)
        doc.check_permission("read")
        doc.apply_fieldlevel_read_permissions()
        data = doc.as_dict()
        if doctype == "Payment Entry":
                received = flt(data.get("received_amount"))
                data["display_amount"] = received if received > 0 else flt(data.get("paid_amount"))
        else:
                data["display_amount"] = flt(data.get("total_debit")) or flt(data.get("total_credit"))
        meta = frappe.get_meta(doctype)
        fields = [
                {"fieldname": key, "label": label, "fieldtype": fieldtype}
                for key, label, fieldtype in [
                        ("company", "Company", "Link"),
                        ("company_gstin", "GSTIN", "Data"),
                        ("payment_type" if doctype == "Payment Entry" else "voucher_type", "Entry Type", "Select"),
                        ("naming_series", "Series", "Data"),
                        ("posting_date", "Posting Date", "Date"),
                        ("owner", "Created By", "Data"),
                        ("display_amount", "Amount", "Currency"),
                ] if key in data
        ]
        tables = []
        for field in meta.fields:
                if field.fieldtype not in table_fields or field.fieldname not in data:
                        continue
                rows = data[field.fieldname] or []
                available_keys = set().union(*(row.keys() for row in rows)) if rows else set()
                tables.append({
                        "fieldname": field.fieldname,
                        "label": field.label or field.fieldname,
                        "fields": _voucher_detail_fields(frappe.get_meta(field.options), available_keys),
                })
        if doctype == "Payment Entry":
                entries = frappe.get_all(
                        "GL Entry",
                        filters={"voucher_type": doctype, "voucher_no": name,
                                 "company": doc.company, "is_cancelled": 0},
                        fields=["name", "account", "party_type", "party", "debit", "credit",
                                "cost_center", "remarks"],
                        order_by="creation asc, name asc", limit=0,
                )
                for entry in entries:
                        entry["party_name"] = (
                                data.get("party_name") if entry.party and entry.party == data.get("party") else entry.party
                        ) or entry.party or ""
                data["accounting_entries"] = entries
                tables.insert(0, {
                        "fieldname": "accounting_entries",
                        "label": "Accounting Entries",
                        "empty_message": "No posted accounting entries.",
                        "fields": [
                                {"fieldname": key, "label": label, "fieldtype": fieldtype}
                                for key, label, fieldtype in [
                                        ("account", "Account", "Link"),
                                        ("party_type", "Party Type", "Data"),
                                        ("party_name", "Party Name", "Data"),
                                        ("debit", "Debit", "Currency"),
                                        ("credit", "Credit", "Currency"),
                                        ("cost_center", "Cost Center", "Link"),
                                        ("remarks", "Remarks", "Small Text"),
                                ]
                        ],
                        "totals": {
                                "debit": sum(flt(entry.debit) for entry in entries),
                                "credit": sum(flt(entry.credit) for entry in entries),
                        },
                })
        return {"document": data, "fields": fields, "tables": tables}


@frappe.whitelist()
def get_current_fiscal_year_dates():
        """
        Returns the year_start_date and year_end_date of the current Fiscal Year.
        """
        today = frappe.utils.today()
        fy = frappe.db.get_value("Fiscal Year", 
                {"year_start_date": ["<=", today], "year_end_date": [">=", today]}, 
                ["year_start_date", "year_end_date"], as_dict=True)
        
        if not fy:
                # Fallback to the latest fiscal year if today isn't covered
                fy = frappe.db.get_value("Fiscal Year", {}, ["year_start_date", "year_end_date"], 
                        order_by="year_start_date desc", as_dict=True)
        
        if fy:
                return {
                        "from": str(fy.year_start_date),
                        "to": str(fy.year_end_date)
                }
        return None
