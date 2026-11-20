"""Bank accounts of a Customer or Supplier, kept in ERPNext's standard Bank Account doctype.

When the india_banking app is installed it adds rules of its own to Bank Account: IFSC and email
are mandatory, the holder and bank names allow only letters, digits, dots (holder only) and single
spaces, and new records start in the "Pending" state of its approval workflow. The checks here
match those rules so the operator sees a plain message instead of a failed save.
"""

import re

import frappe

PARTY_TYPES = ("Customer", "Supplier")
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
# Same patterns india_banking validates with
HOLDER_RE = re.compile(r"^[A-Za-z0-9.]+(?: [A-Za-z0-9.]+)*$")
BANK_RE = re.compile(r"^[A-Za-z0-9]+(?: [A-Za-z0-9]+)*$")
BASE_FIELDS = ["name", "account_name", "bank", "bank_account_no", "branch_code", "is_default"]


def _check_party_type(party_type):
	if party_type not in PARTY_TYPES:
		frappe.throw(f"Bank accounts are kept for Customer or Supplier only, not {party_type}")


def _strict_names():
	return "india_banking" in frappe.get_installed_apps()


def _has_email_field():
	return frappe.get_meta("Bank Account").has_field("email")


def _fields():
	return BASE_FIELDS + (["email"] if _has_email_field() else [])


def _rules():
	meta = frappe.get_meta("Bank Account")
	strict = _strict_names()
	return {
		"strict_names": strict,
		"ifsc_required": strict or bool(meta.get_field("branch_code").reqd),
		"email_field": _has_email_field(),
		"email_required": bool(_has_email_field() and meta.get_field("email").reqd),
	}


@frappe.whitelist()
def get_bank_form_meta():
	"""Bank names for suggestions, and which bank fields this site requires."""
	return {
		"banks": frappe.get_all("Bank", pluck="name", order_by="name asc", limit_page_length=0),
		**_rules(),
	}


@frappe.whitelist()
def get_party_bank_accounts(party_type, party):
	"""Active bank accounts of one party, default first."""
	_check_party_type(party_type)
	frappe.has_permission(party_type, "read", doc=party, throw=True)
	return party_bank_accounts(party_type, party)


def party_bank_accounts(party_type, party):
	"""Same as get_party_bank_accounts, for callers that already checked access."""
	rows = frappe.get_all(
		"Bank Account",
		filters={"party_type": party_type, "party": party, "disabled": 0, "is_company_account": 0},
		fields=_fields(),
		order_by="is_default desc, creation asc",
	)
	for r in rows:
		r["is_default"] = 1 if r.is_default else 0
		for f in ("account_name", "bank_account_no", "branch_code", "email"):
			r[f] = r.get(f) or ""
	return rows


def _holder_from_party(party):
	"""Party names often carry '&', '/' or '-', which strict holder names reject."""
	if not _strict_names():
		return party
	return re.sub(r"[^A-Za-z0-9.]+", " ", party).strip() or "Account"


def _clean_row(row, party, rules, party_email):
	account_no = re.sub(r"\s+", "", str(row.get("bank_account_no") or ""))
	bank = re.sub(r"\s+", " ", (row.get("bank") or "").strip())
	ifsc = (row.get("branch_code") or "").strip().upper()
	holder = re.sub(r"\s+", " ", (row.get("account_name") or "").strip()) or _holder_from_party(party)
	email = (row.get("email") or "").strip() or party_email
	if not account_no and not bank:
		return None
	if not bank:
		frappe.throw(f"Bank name is required for account {account_no}")
	if not account_no:
		frappe.throw(f"Account number is required for the {bank} account")
	if not account_no.isascii() or not account_no.isdigit():
		frappe.throw(f"Account number {account_no} must contain digits only")
	if ifsc and not IFSC_RE.match(ifsc):
		frappe.throw(f"IFSC {ifsc} is not valid: 4 letters, then 0, then 6 letters or digits")
	if not ifsc and rules["ifsc_required"]:
		frappe.throw(f"IFSC is required for account {account_no}")
	if rules["strict_names"]:
		if not HOLDER_RE.match(holder):
			frappe.throw(f"Account holder name '{holder}' may contain only letters, digits, dots and spaces")
		if not BANK_RE.match(bank):
			frappe.throw(f"Bank name '{bank}' may contain only letters, digits and spaces")
	if not email and rules["email_required"]:
		frappe.throw(f"Email is required for the bank account {account_no}")
	return {
		"name": (row.get("name") or "").strip(),
		"account_name": holder,
		"bank": bank,
		"bank_account_no": account_no,
		"branch_code": ifsc,
		"email": email,
		"is_default": 1 if frappe.utils.cint(row.get("is_default")) else 0,
	}


def _ensure_bank(bank):
	existing = frappe.db.exists("Bank", bank)
	if existing:
		return existing
	doc = frappe.get_doc({"doctype": "Bank", "bank_name": bank})
	doc.insert(ignore_permissions=True)
	return doc.name


def _free_account_name(holder, bank, account_no):
	"""Bank Account is named '<account_name> - <bank>' across all parties: pick an unused account_name."""
	tail = account_no[-4:]
	candidates = [holder, f"{holder} {tail}"] + [f"{holder} {tail} {i}" for i in range(2, 50)]
	for name in candidates:
		if not frappe.db.exists("Bank Account", f"{name} - {bank}"):
			return name
	frappe.throw(f"Could not find a free name for the {bank} account of {holder}")


def _default_company():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)


def sync_party_bank_accounts(party_type, party, rows):
	"""Make the party's active bank accounts match `rows`.

	A row whose `name` matches a record with the same holder, bank, number and IFSC keeps that
	record (only email and default can change in place). Any other row creates a new record, and
	active records of this party not kept are deleted, or disabled when a transaction links them.
	"""
	_check_party_type(party_type)
	rules = _rules()
	party_email = frappe.db.get_value(party_type, party, "email_id") or ""
	cleaned = [r for r in (_clean_row(r, party, rules, party_email) for r in rows or []) if r]

	defaults = [r for r in cleaned if r["is_default"]]
	for r in cleaned:
		r["is_default"] = 0
	if cleaned:
		(defaults[0] if defaults else cleaned[0])["is_default"] = 1

	existing = {
		d.name: d
		for d in frappe.get_all(
			"Bank Account",
			filters={"party_type": party_type, "party": party, "disabled": 0, "is_company_account": 0},
			fields=BASE_FIELDS,
		)
	}

	# Clear the old default first so ERPNext's own default handling never sees two
	for name, d in existing.items():
		if d.is_default:
			frappe.db.set_value("Bank Account", name, "is_default", 0, update_modified=False)

	# The approval workflow (india_banking) approves the number and IFSC: a change to either, or to
	# the holder/bank that make up the record name, replaces the record so it starts Pending again.
	to_insert, to_remove = [], set(existing)
	for r in cleaned:
		r["bank"] = _ensure_bank(r["bank"])
		old = existing.get(r["name"]) if r["name"] else None
		same = old and all(
			(old.get(f) or "") == r[f] for f in ("account_name", "bank", "bank_account_no", "branch_code")
		)
		if not same:
			to_insert.append(r)
			continue
		to_remove.discard(old.name)
		if rules["email_field"] and (frappe.db.get_value("Bank Account", old.name, "email") or "") != r["email"]:
			doc = frappe.get_doc("Bank Account", old.name)
			doc.email = r["email"]
			doc.save(ignore_permissions=True)
		if r["is_default"]:
			frappe.db.set_value("Bank Account", old.name, "is_default", 1, update_modified=False)

	# Removals first: india_banking can require account numbers to be unique among active accounts
	for name in to_remove:
		frappe.db.savepoint("bank_account_delete")
		try:
			frappe.delete_doc("Bank Account", name, ignore_permissions=True)
		except frappe.LinkExistsError:
			# on_trash already ran before the link check: undo it and only disable
			frappe.db.rollback(save_point="bank_account_delete")
			frappe.clear_last_message()
			frappe.db.set_value("Bank Account", name, {"disabled": 1, "is_default": 0})

	company = _default_company()
	for r in to_insert:
		doc = frappe.get_doc({
			"doctype": "Bank Account",
			"account_name": _free_account_name(r["account_name"], r["bank"], r["bank_account_no"]),
			"bank": r["bank"],
			"bank_account_no": r["bank_account_no"],
			"branch_code": r["branch_code"],
			"is_default": r["is_default"],
			"party_type": party_type,
			"party": party,
			# india_banking takes the currency from the party, else from this company
			"company": company,
		})
		if rules["email_field"]:
			doc.email = r["email"]
		doc.insert(ignore_permissions=True)
