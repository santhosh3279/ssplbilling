"""Bank statement import and posting for the Bank Statement page.

The page parses the bank's Excel in the browser (column mapping is the operator's) and sends the
lines to import_statement(), which keeps each new line as an SSPL Bank Statement Entry and then
matches every Pending line against the bank ledger's GL entries. Lines with no voucher stay
Pending; post_entry() books one against a counter ledger picked on the page: a Customer /
Supplier / Employee becomes a Payment Entry, an Account a Journal Entry.

Sign convention (see _side): a statement deposit is a debit on the bank ledger, a withdrawal a
credit. Every voucher posted here carries the entry's marker ([BST-00001]) and all its statement
columns in its remarks, which is what the first matching pass looks for.
"""

import hashlib
import json
import re

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Max, Min, Sum
from frappe.utils import add_days, cint, flt, getdate, now_datetime

from ssplbilling.api.paytm_api import _require_desk_user

DOCTYPE = "SSPL Bank Statement Entry"
PARTY_TYPES = ("Customer", "Supplier", "Employee")
# Days a voucher's posting date may differ from the statement date for an amount + date match
DEFAULT_WINDOW = 3
# A voucher with the statement's own reference / cheque no may sit this far off (cheques clear late)
REF_WINDOW = 30
LIST_FIELDS = [
	"name",
	"bank_account",
	"company",
	"posting_date",
	"reference_no",
	"description",
	"withdrawal",
	"deposit",
	"balance",
	"status",
	"voucher_type",
	"voucher_no",
	"match_basis",
	"counter_party_type",
	"counter_party",
	"import_batch",
	"row_data",
]


def _side(withdrawal, deposit):
	"""(signed amount on the bank ledger, amount): deposit is +debit, withdrawal is -credit."""
	net = flt(deposit, 2) - flt(withdrawal, 2)
	return net, abs(net)


def _text(value):
	return re.sub(r"\s+", " ", str(value or "")).strip()


def _ref_key(value):
	"""Reference / cheque no compared on letters and digits only, leading zeros dropped."""
	return re.sub(r"[^0-9A-Z]", "", str(value or "").upper()).lstrip("0")


def _ref_tokens(text):
	"""Words of a remark as reference keys, so a ref matches a whole token, never digits of an amount."""
	return {_ref_key(t) for t in re.split(r"[^0-9A-Za-z]+", text or "") if t}


def _marker(name):
	return f"[{name}]"


def _bank_account(bank_account):
	acc = frappe.db.get_value(
		"Account", bank_account, ["name", "company", "account_type", "is_group"], as_dict=True
	)
	if not acc or acc.is_group or acc.account_type != "Bank":
		frappe.throw(_("{0} is not a bank ledger").format(bank_account))
	return acc


def _dedupe_key(bank_account, row, occurrence):
	"""With a running balance, date + amounts + balance pin the line, whatever the narration export
	looked like; without one, narration and ref tell lines apart, and identical lines their order."""
	parts = [bank_account, str(row["posting_date"]), f"{row['withdrawal']:.2f}", f"{row['deposit']:.2f}"]
	if row["balance"] is not None:
		parts.append(f"{row['balance']:.2f}")
	else:
		parts += [row["reference_no"].upper(), row["description"].upper(), f"#{occurrence}"]
	return hashlib.sha1("|".join(parts).encode()).hexdigest()


def _clean_row(row):
	"""A statement line from the page, normalised, or None when it is no transaction (opening /
	closing / total lines, no date, nothing or both sides filled)."""
	try:
		posting_date = getdate(row.get("posting_date"))
	except Exception:
		return None
	if not posting_date:
		return None
	withdrawal, deposit = abs(flt(row.get("withdrawal"), 2)), abs(flt(row.get("deposit"), 2))
	if bool(withdrawal) == bool(deposit):
		return None
	balance = row.get("balance")
	extra = row.get("extra") or {}
	return {
		"posting_date": posting_date,
		"withdrawal": withdrawal,
		"deposit": deposit,
		"balance": flt(balance, 2) if balance not in (None, "") else None,
		"reference_no": _text(row.get("reference_no"))[:140],
		"description": _text(row.get("description")),
		"extra": {_text(k): _text(v) for k, v in extra.items() if _text(k) and _text(v)},
	}


@frappe.whitelist()
def get_bank_accounts():
	"""Bank ledgers for the page's selector, with how many lines of each are still Pending."""
	_require_desk_user()
	accounts = frappe.get_all(
		"Account",
		filters={"account_type": "Bank", "is_group": 0, "disabled": 0},
		fields=["name", "account_name", "company"],
		order_by="company, account_name",
	)
	bse = frappe.qb.DocType(DOCTYPE)
	pending = dict(
		frappe.qb.from_(bse)
		.select(bse.bank_account, Count(bse.name))
		.where(bse.status == "Pending")
		.groupby(bse.bank_account)
		.run()
	)
	for a in accounts:
		a.pending = pending.get(a.name, 0)
	return accounts


@frappe.whitelist(methods=["POST"])
def import_statement(bank_account, rows, file_name=None, window=DEFAULT_WINDOW):
	"""Keep each new statement line, skip lines already imported, then match the whole date range."""
	_require_desk_user()
	acc = _bank_account(bank_account)
	if isinstance(rows, str):
		rows = json.loads(rows)

	batch = f"{now_datetime().strftime('%Y-%m-%d %H:%M')} {file_name or ''}".strip()[:140]
	inserted, duplicates, skipped = 0, 0, 0
	dates = []
	seen = {}
	for raw in rows or []:
		row = _clean_row(raw)
		if not row:
			skipped += 1
			continue
		base = tuple(row[k] for k in ("posting_date", "withdrawal", "deposit", "reference_no", "description"))
		seen[base] = seen.get(base, 0) + 1
		key = _dedupe_key(bank_account, row, seen[base])
		dates.append(row["posting_date"])
		if frappe.db.exists(DOCTYPE, {"dedupe_key": key}):
			duplicates += 1
			continue
		frappe.get_doc(
			{
				"doctype": DOCTYPE,
				"bank_account": bank_account,
				"company": acc.company,
				"posting_date": row["posting_date"],
				"reference_no": row["reference_no"],
				"description": row["description"],
				"withdrawal": row["withdrawal"],
				"deposit": row["deposit"],
				"balance": row["balance"],
				"status": "Pending",
				"import_batch": batch,
				"dedupe_key": key,
				"row_data": json.dumps(row["extra"], indent=1, ensure_ascii=False) if row["extra"] else None,
			}
		).insert(ignore_permissions=True)
		inserted += 1

	result = {"inserted": inserted, "duplicates": duplicates, "skipped": skipped}
	if dates:
		result.update(_match(bank_account, min(dates), max(dates), window))
		result.update({"from_date": min(dates), "to_date": max(dates)})
	frappe.db.commit()
	return result


@frappe.whitelist()
def get_entries(bank_account, from_date=None, to_date=None, status=None, limit=2000):
	_require_desk_user()
	filters = {"bank_account": bank_account}
	if from_date and to_date:
		filters["posting_date"] = ("between", [from_date, to_date])
	if status:
		filters["status"] = status
	return frappe.get_all(
		DOCTYPE,
		filters=filters,
		fields=LIST_FIELDS,
		# newest first, so the limit drops the oldest lines; the page shows them oldest first
		order_by="posting_date desc, creation desc",
		limit_page_length=cint(limit) or 2000,
	)


@frappe.whitelist(methods=["POST"])
def rematch(bank_account, from_date=None, to_date=None, window=DEFAULT_WINDOW):
	"""Re-run matching for the range, e.g. after vouchers were booked elsewhere or cancelled."""
	_require_desk_user()
	_bank_account(bank_account)
	if not (from_date and to_date):
		bse = frappe.qb.DocType(DOCTYPE)
		from_date, to_date = (
			frappe.qb.from_(bse)
			.select(Min(bse.posting_date), Max(bse.posting_date))
			.where(bse.bank_account == bank_account)
			.run()[0]
		)
		if not from_date:
			return {"matched": 0, "reopened": 0, "pending": 0}
	result = _match(bank_account, getdate(from_date), getdate(to_date), window)
	frappe.db.commit()
	return result


def _bank_vouchers(bank_account, from_date, to_date):
	"""Every submitted voucher touching the bank ledger in the range, netted per voucher:
	{(voucher_type, voucher_no): {posting_date, net, amount, ref, remarks}}."""
	gle = frappe.qb.DocType("GL Entry")
	rows = (
		frappe.qb.from_(gle)
		.select(
			gle.voucher_type,
			gle.voucher_no,
			Max(gle.posting_date).as_("posting_date"),
			Sum(gle.debit).as_("debit"),
			Sum(gle.credit).as_("credit"),
			Max(gle.remarks).as_("remarks"),
		)
		.where(
			(gle.account == bank_account)
			& (gle.is_cancelled == 0)
			& (gle.posting_date >= from_date)
			& (gle.posting_date <= to_date)
		)
		.groupby(gle.voucher_type, gle.voucher_no)
		.run(as_dict=True)
	)
	refs = {}
	for doctype, field in (("Payment Entry", "reference_no"), ("Journal Entry", "cheque_no")):
		names = [r.voucher_no for r in rows if r.voucher_type == doctype]
		if names:
			for name, ref in frappe.get_all(
				doctype, filters={"name": ("in", names)}, fields=["name", field], as_list=True
			):
				refs[(doctype, name)] = ref
	vouchers = {}
	for r in rows:
		net = flt(r.debit, 2) - flt(r.credit, 2)
		if not net:
			continue
		key = (r.voucher_type, r.voucher_no)
		vouchers[key] = {
			"posting_date": getdate(r.posting_date),
			"net": net,
			"ref": _ref_key(refs.get(key)),
			"remarks": r.remarks or "",
			"tokens": _ref_tokens(r.remarks),
		}
	return vouchers


def _reopen_cancelled(bank_account):
	"""Matched / Posted lines whose voucher is no longer submitted go back to Pending."""
	rows = frappe.get_all(
		DOCTYPE,
		filters={"bank_account": bank_account, "status": ("in", ["Matched", "Posted"])},
		fields=["name", "voucher_type", "voucher_no"],
	)
	live = set()
	for doctype in {r.voucher_type for r in rows if r.voucher_type}:
		names = [r.voucher_no for r in rows if r.voucher_type == doctype and r.voucher_no]
		live.update(
			(doctype, n)
			for n in frappe.get_all(doctype, filters={"name": ("in", names), "docstatus": 1}, pluck="name")
		)
	reopened = 0
	for r in rows:
		if (r.voucher_type, r.voucher_no) not in live:
			frappe.db.set_value(
				DOCTYPE,
				r.name,
				{
					"status": "Pending",
					"voucher_type": None,
					"voucher_no": None,
					"match_basis": None,
					"counter_party_type": None,
					"counter_party": None,
				},
			)
			reopened += 1
	return reopened


def _match(bank_account, from_date, to_date, window=DEFAULT_WINDOW):
	"""Link Pending lines in the range to the bank ledger's vouchers, one voucher per line, in three
	passes: this page's marker in the voucher remarks, then the same reference / cheque no within
	REF_WINDOW days, then amount + side with the nearest posting date within window days."""
	window = max(0, cint(window))
	reopened = _reopen_cancelled(bank_account)
	pending = frappe.get_all(
		DOCTYPE,
		filters={
			"bank_account": bank_account,
			"status": "Pending",
			"posting_date": ("between", [from_date, to_date]),
		},
		fields=["name", "posting_date", "withdrawal", "deposit", "reference_no"],
		order_by="posting_date asc, creation asc",
	)
	if not pending:
		return {"matched": 0, "reopened": reopened, "pending": 0}

	span = max(window, REF_WINDOW)
	vouchers = _bank_vouchers(bank_account, add_days(from_date, -span), add_days(to_date, span))
	claimed = {
		(r.voucher_type, r.voucher_no)
		for r in frappe.get_all(
			DOCTYPE,
			filters={"bank_account": bank_account, "status": ("in", ["Matched", "Posted"])},
			fields=["voucher_type", "voucher_no"],
		)
	}
	free = {k: v for k, v in vouchers.items() if k not in claimed}
	by_net = {}
	for k, v in free.items():
		by_net.setdefault(round(v["net"], 2), []).append(k)
	for p in pending:
		p.net = round(_side(p.withdrawal, p.deposit)[0], 2)
		p.ref = _ref_key(p.reference_no)
		p.posting_date = getdate(p.posting_date)

	found = {}

	def claim(p, key, basis):
		found[p.name] = (key, basis)
		free.pop(key)

	def candidates(p):
		"""Free vouchers with the line's amount on the same side of the bank ledger."""
		return [(k, free[k]) for k in by_net.get(p.net, ()) if k in free]

	def days(p, v):
		return abs((v["posting_date"] - p.posting_date).days)

	for p in pending:
		marker = _marker(p.name)
		key = next((k for k, v in free.items() if marker in v["remarks"]), None)
		if key:
			claim(p, key, "Remark marker")

	for p in pending:
		if p.name in found or len(p.ref) < 4:
			continue
		hits = [
			(days(p, v), k)
			for k, v in candidates(p)
			if days(p, v) <= REF_WINDOW
			and (v["ref"] == p.ref or p.ref in v["tokens"])
		]
		if hits:
			claim(p, min(hits)[1], "Reference no")

	# Nearest dates first across all lines, so a close match is never taken by a far one
	for gap in range(window + 1):
		for p in pending:
			if p.name in found:
				continue
			hits = sorted(k for k, v in candidates(p) if days(p, v) == gap)
			if hits:
				claim(p, hits[0], "Amount + date" if not gap else f"Amount, {gap} day(s) apart")

	for name, ((voucher_type, voucher_no), basis) in found.items():
		frappe.db.set_value(
			DOCTYPE,
			name,
			{
				"status": "Matched",
				"voucher_type": voucher_type,
				"voucher_no": voucher_no,
				"match_basis": basis,
			},
		)
	return {"matched": len(found), "reopened": reopened, "pending": len(pending) - len(found)}


def _remarks(doc, extra_remarks=None):
	"""Voucher remarks: the entry marker plus every statement column, so the line can be traced
	from the voucher and re-matched by its marker."""
	parts = [f"Bank statement {_marker(doc.name)} {doc.posting_date}"]
	if doc.description:
		parts.append(doc.description)
	if doc.reference_no:
		parts.append(f"Ref {doc.reference_no}")
	if doc.row_data:
		try:
			parts.extend(f"{k}: {v}" for k, v in json.loads(doc.row_data).items())
		except ValueError:
			pass
	if extra_remarks and extra_remarks.strip():
		parts.append(extra_remarks.strip())
	return " | ".join(parts)


def _cost_center(cost_center, company):
	if cost_center and frappe.db.get_value("Cost Center", cost_center, "company") == company:
		return cost_center
	return frappe.get_cached_value("Company", company, "cost_center")


def _bank_mode_of_payment(bank_account):
	return (
		frappe.db.get_value("Mode of Payment Account", {"default_account": bank_account}, "parent")
		or frappe.db.get_value("Mode of Payment", {"type": "Bank", "enabled": 1}, "name")
		or "Cash"
	)


@frappe.whitelist(methods=["POST"])
def post_entry(name, counter_type, counter, remarks=None, cost_center=None):
	"""Book one Pending line against the counter ledger, once: the row lock stops a double click
	from booking it twice. A Customer / Supplier / Employee gets a Payment Entry (Receive for a
	deposit, Pay for a withdrawal); an Account a Journal Entry (Contra Entry when it is another
	bank / cash ledger, else Bank Entry). Posted in the bank ledger's company on the statement date."""
	_require_desk_user()
	status = frappe.db.get_value(DOCTYPE, name, "status", for_update=True)
	if not status:
		frappe.throw(_("Statement line {0} not found").format(name))
	if status != "Pending":
		frappe.throw(_("Statement line {0} is already {1}").format(name, status))
	if not counter_type or not counter:
		frappe.throw(_("Select the counter ledger"))

	doc = frappe.get_doc(DOCTYPE, name)
	company = frappe.db.get_value("Account", doc.bank_account, "company")
	cost_center = _cost_center(cost_center, company)
	net, amount = _side(doc.withdrawal, doc.deposit)
	reference_no = doc.reference_no or doc.name
	text = _remarks(doc, remarks)

	if counter_type in PARTY_TYPES:
		voucher_type = "Payment Entry"
		voucher_no = _post_payment_entry(
			doc, counter_type, counter, company, cost_center, net, amount, reference_no, text
		)
	elif counter_type == "Account":
		voucher_type = "Journal Entry"
		voucher_no = _post_journal_entry(doc, counter, company, cost_center, net, amount, reference_no, text)
	else:
		frappe.throw(_("Unknown counter ledger type {0}").format(counter_type))

	doc.update(
		{
			"status": "Posted",
			"voucher_type": voucher_type,
			"voucher_no": voucher_no,
			"match_basis": "Posted here",
			"counter_party_type": counter_type,
			"counter_party": counter,
		}
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	if voucher_type == "Payment Entry":
		try:
			from ssplbilling.api.automatic_entries_api import mirror_standalone_payment_entry

			mirror_standalone_payment_entry(frappe.get_doc("Payment Entry", voucher_no))
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "Automatic Entries: payment mirror failed")

	return {k: doc.get(k) for k in LIST_FIELDS}


def _post_payment_entry(doc, party_type, party, company, cost_center, net, amount, reference_no, text):
	from ssplbilling.api.paymentv2_api import _insert_payment_entry_with_retry

	return _insert_payment_entry_with_retry(
		{
			"payment_type": "Receive" if net > 0 else "Pay",
			"party_type": party_type,
			"party": party,
			"amount": amount,
			"mop_account": doc.bank_account,
			"mode_of_payment": _bank_mode_of_payment(doc.bank_account),
			"reference_no": reference_no,
			"reference_date": doc.posting_date,
			"posting_date": doc.posting_date,
			"company": company,
			"cost_center": cost_center,
			"remarks": text,
			# keeps these remarks instead of ERPNext's generated "Amount INR ... received from ..."
			"Custom Remarks": 1,
		}
	)


def _post_journal_entry(doc, account, company, cost_center, net, amount, reference_no, text):
	acc = frappe.db.get_value(
		"Account", account, ["company", "account_type", "is_group", "disabled"], as_dict=True
	)
	if not acc or acc.is_group or acc.disabled:
		frappe.throw(_("{0} is not a ledger that can be posted to").format(account))
	if acc.company != company:
		frappe.throw(_("{0} belongs to {1}, the bank ledger to {2}").format(account, acc.company, company))
	if account == doc.bank_account:
		frappe.throw(_("Counter ledger must differ from the bank ledger"))
	if acc.account_type in ("Receivable", "Payable"):
		frappe.throw(
			_("{0} needs a party: pick the Customer / Supplier instead of the account").format(account)
		)

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Contra Entry" if acc.account_type in ("Bank", "Cash") else "Bank Entry"
	je.company = company
	je.posting_date = doc.posting_date
	je.cheque_no = reference_no
	je.cheque_date = doc.posting_date
	je.user_remark = text
	bank_debit = amount if net > 0 else 0
	je.append(
		"accounts",
		{
			"account": doc.bank_account,
			"debit_in_account_currency": bank_debit,
			"credit_in_account_currency": amount - bank_debit,
			"cost_center": cost_center,
			# GL Entry remarks come from the row's user remark, which is what matching reads
			"user_remark": text,
		},
	)
	je.append(
		"accounts",
		{
			"account": account,
			"debit_in_account_currency": amount - bank_debit,
			"credit_in_account_currency": bank_debit,
			"cost_center": cost_center,
			"user_remark": text,
		},
	)
	je.insert()
	je.submit()
	return je.name


def _set_status(name, allowed_from, to, clear_voucher=False):
	status = frappe.db.get_value(DOCTYPE, name, "status", for_update=True)
	if status not in allowed_from:
		frappe.throw(_("Statement line {0} is {1}").format(name, status))
	values = {"status": to}
	if clear_voucher:
		values.update({"voucher_type": None, "voucher_no": None, "match_basis": None})
	frappe.db.set_value(DOCTYPE, name, values)
	frappe.db.commit()
	return frappe.db.get_value(DOCTYPE, name, LIST_FIELDS, as_dict=True)


@frappe.whitelist(methods=["POST"])
def set_ignored(name, ignored=1):
	"""Ignore a Pending line (nothing to book, e.g. booked in another ledger) or bring it back."""
	_require_desk_user()
	if cint(ignored):
		return _set_status(name, ("Pending",), "Ignored")
	return _set_status(name, ("Ignored",), "Pending")


@frappe.whitelist(methods=["POST"])
def unmatch(name):
	"""Send a wrongly matched line back to Pending; its voucher becomes free for other lines."""
	_require_desk_user()
	return _set_status(name, ("Matched",), "Pending", clear_voucher=True)


@frappe.whitelist(methods=["POST"])
def delete_entries(names):
	"""Delete Pending / Ignored lines (e.g. a wrong upload). Matched / Posted lines are kept."""
	_require_desk_user()
	if isinstance(names, str):
		names = json.loads(names)
	deleted = []
	for name in names or []:
		if frappe.db.get_value(DOCTYPE, name, "status", for_update=True) in ("Pending", "Ignored"):
			frappe.delete_doc(DOCTYPE, name, ignore_permissions=True)
			deleted.append(name)
	frappe.db.commit()
	return {"deleted": deleted}
