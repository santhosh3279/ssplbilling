# Agent Memory — ssplbilling

## Key Files
- API transport: `frontend/src/api.js` (canonical, use for new code)
- Billing state: `frontend/src/composables/useBilling.js`
- Python endpoints: `ssplbilling/api/sales_api.py`
- Router base: `/frontend` (`frontend/src/router.js`)
- Auth: `frontend/src/session.js`

## Patterns & Pitfalls

### Frappe Link fields can store stale/partial account names
- `SSPL Billing Settings` child table `billing_series` stores account names (e.g. `cash_account`).
- These may not include the company abbreviation suffix (e.g. "NCK CASH" instead of "NCK CASH - SSPL").
- Always guard with `frappe.db.exists("Account", candidate)` before using a Link field value as a Payment Entry account. If it fails, fall through to the Mode of Payment / company default fallback.
- See: `_resolve_account` inner function in `submit_invoice_with_payment`, `sales_api.py` ~line 481.

### Payment Entry creation (`_create_pe`)
- `paid_to` must be a valid Account name or Frappe throws `LinkValidationError`.
- The three-tier fallback is: series config account → Mode of Payment Account table → company `default_cash_account`.
