import frappe
from frappe.utils import flt, getdate


@frappe.whitelist()
def search_employees(query="", limit=20):
	"""Search active employees by name."""
	return frappe.get_all(
		"Employee",
                or_filters=[["name", "like", f"%{query}%"], ["employee_name", "like", f"%{query}%"]],
                filters=[["status", "=", "Active"]],
		fields=["name", "employee_name", "designation", "balance_incentive"],
		order_by="employee_name asc",
		limit_page_length=int(limit),
	)


@frappe.whitelist()
def get_employee_incentive_ledger(employee, from_date=None, to_date=None):
	"""
	Return all incentive ledger entries for an employee — earned (from submitted
	Invoice Incentive entries) and redeemed (Incentive Redeem),
	combined and sorted by date with a running balance.
	"""
	params = {"employee": employee}

	# ── Date filters ──────────────────────────────────────────────────────────
	earned_date_filter = ""
	redeem_date_filter = ""
	if from_date:
		fd = getdate(from_date)
		params["from_date"] = fd
		earned_date_filter += " AND ii.date >= %(from_date)s"
		redeem_date_filter += " AND posting_date >= %(from_date)s"
	if to_date:
		td = getdate(to_date)
		params["to_date"] = td
		earned_date_filter += " AND ii.date <= %(to_date)s"
		redeem_date_filter += " AND posting_date <= %(to_date)s"

	# ── Earned rows ───────────────────────────────────────────────────────────
	earned_rows = frappe.db.sql(
		f"""
		SELECT
			is_row.parent            AS incentive_entry,
			is_row.role              AS role,
			CAST(is_row.points AS DECIMAL(15,2)) AS points,
			ii.date                  AS posting_date,
			ii.inv_no                AS voucher_no,
			CASE
				WHEN si.name IS NOT NULL THEN 'Sales Invoice'
				WHEN pi.name IS NOT NULL THEN 'Purchase Invoice'
				WHEN se.name IS NOT NULL THEN 'Stock Entry'
				ELSE 'Sales Invoice'
			END AS voucher_type,
			CASE
				WHEN si.name IS NOT NULL THEN si.customer
				WHEN pi.name IS NOT NULL THEN pi.supplier
				ELSE NULL
			END AS party
		FROM `tabIncentive System` is_row
		INNER JOIN `tabInvoice Incentive` ii
			ON ii.name = is_row.parent AND is_row.parenttype = 'Invoice Incentive' AND ii.docstatus = 1
		LEFT JOIN `tabSales Invoice` si
			ON si.name = ii.inv_no
		LEFT JOIN `tabPurchase Invoice` pi
			ON pi.name = ii.inv_no
		LEFT JOIN `tabStock Entry` se
			ON se.name = ii.inv_no
		WHERE is_row.employee = %(employee)s
		  {earned_date_filter}
		ORDER BY posting_date ASC, is_row.parent ASC
		""",
		params,
		as_dict=True,
	)

	# ── Redeemed rows ─────────────────────────────────────────────────────────
	redeemed_rows = frappe.db.sql(
		f"""
		SELECT
			name           AS voucher_no,
			posting_date,
			redeem_points  AS points
		FROM `tabIncentive Redeem`
		WHERE employee = %(employee)s
		  AND docstatus = 1
		  {redeem_date_filter}
		ORDER BY posting_date ASC, name ASC
		""",
		params,
		as_dict=True,
	)

	# ── Merge ─────────────────────────────────────────────────────────────────
	entries = []
	for r in earned_rows:
		entries.append(
			{
				"date": str(r.posting_date) if r.posting_date else "",
				"voucher_no": r.voucher_no or "",
				"voucher_type": r.voucher_type or "",
				"role": r.role or "",
				"party": r.party or "",
				"earned": flt(r.points, 2),
				"redeemed": 0.0,
				"balance": 0.0,
			}
		)
	for r in redeemed_rows:
		entries.append(
			{
				"date": str(r.posting_date) if r.posting_date else "",
				"voucher_no": r.voucher_no or "",
				"voucher_type": "Incentive Redeem",
				"role": "",
				"party": "",
				"earned": 0.0,
				"redeemed": flt(r.points, 2),
				"balance": 0.0,
			}
		)

	entries.sort(key=lambda x: (x["date"], x["voucher_no"]))

	# Running balance
	running = 0.0
	for e in entries:
		running += e["earned"] - e["redeemed"]
		e["balance"] = round(running, 2)

	# ── Employee summary ──────────────────────────────────────────────────────
	emp = frappe.db.get_value(
		"Employee",
		employee,
		["employee_name", "designation", "total_incentive", "redeemed_incentive", "balance_incentive"],
		as_dict=True,
	)

	return {
		"entries": entries,
		"summary": {
			"employee": employee,
			"employee_name": emp.employee_name if emp else "",
			"designation": emp.designation if emp else "",
			"total_incentive": flt(emp.total_incentive if emp else 0, 2),
			"redeemed_incentive": flt(emp.redeemed_incentive if emp else 0, 2),
			"balance_incentive": flt(emp.balance_incentive if emp else 0, 2),
		},
	}
