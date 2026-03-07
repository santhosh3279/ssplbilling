# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About

**ssplbilling** is a custom Frappe/ERPNext v16 app for Sundaram and Sons Private Ltd. It provides a fast wholesale billing front-end (Vue 3 SPA) layered on top of ERPNext's Sales Invoice, Customer, Item, and Bin doctypes.

## Repository Layout

```
ssplbilling/                     ← Frappe app root
├── ssplbilling/                 ← Python package
│   ├── api/
│   │   ├── sales_api.py         ← Whitelisted Python endpoints (customers, invoices, payments, ledger)
│   │   └── dashboard_api.py     ← Dashboard + settings endpoints (get_billing_settings, get_allowed_series)
│   ├── ssplbilling/
│   │   ├── doctype/
│   │   │   ├── sspl_billing_series/
│   │   │   └── sspl_billing_settings/
│   │   └── page/
│   │       └── wholesale_billing/  ← Legacy Frappe desk page (JS/HTML)
│   └── hooks.py
└── frontend/                    ← Vue 3 SPA
    ├── src/
    │   ├── api.js               ← Canonical fetch()-based transport (frappeGet, frappePost + all domain calls)
    │   ├── api/
    │   │   └── customer.js      ← Customer/Address/Contact CRUD helpers
    │   ├── session.js           ← Auth singleton (isLoggedIn, user, fullName)
    │   ├── router.js            ← Vue Router (base: /frontend)
    │   ├── encryption.js        ← Price cipher (digit→letter) + localStorage defaults
    │   ├── App.vue
    │   ├── composables/
    │   │   └── useBilling.js    ← All billing state + side-effects
    │   ├── components/
    │   │   ├── ItemSearchModal.vue
    │   │   ├── CustomerSearchModal.vue
    │   │   └── PrintOptionsModal.vue
    │   ├── pages/
    │   │   ├── Login.vue
    │   │   ├── Dashboard.vue        ← Syncs items/customers to IndexedDB on load
    │   │   ├── SalesEntry.vue       ← Keyboard-driven draft invoice entry
    │   │   ├── CashierEntry.vue     ← Lists drafts; submits with cash/UPI payment split
    │   │   ├── CustomerLedger.vue   ← GL ledger with running balance per customer
    │   │   ├── PaymentEntry.vue     ← Direct payment / journal entry creation
    │   │   └── WholesaleFastBilling.vue ← Barcode-scan POS (not in router, retained as backup)
    │   └── services/
    │       ├── api.js           ← Older frappe-ui call()-based helpers (avoid for new code)
    │       ├── dashboard.js     ← dashboardApi object (getBillingSettings, fetchAllItemsForSync, etc.)
    │       └── localDb.js       ← IndexedDB wrapper (items + customers stores for offline search)
    ├── vite.config.js
    ├── tailwind.config.js
    └── package.json
```

## Commands

### Frontend (inside `frontend/`)

```bash
yarn dev        # Dev server on :8080, proxies to Frappe on webserver_port
yarn build      # Production build → ssplbilling/public/frontend/
```

> Vite reads `../../../sites/common_site_config.json` for `webserver_port` and `socketio_port`. The dev server requires `"ignore_csrf": 1` in `site_config.json`.

### Frappe / bench (from bench root)

```bash
bench --site <site> migrate                  # Apply DB migrations / fixtures
bench --site <site> build --app ssplbilling  # Build frontend assets
bench start                                  # Start dev server (Frappe + workers)
```

### Python linting / formatting

```bash
pre-commit run --all-files        # ruff, ruff-format, prettier, eslint
```

### Python tests

```bash
bench --site <site> run-tests --app ssplbilling
bench --site <site> run-tests --app ssplbilling --module ssplbilling.ssplbilling.doctype.sspl_billing_settings.test_sspl_billing_settings
```

## Architecture

### Billing workflow (two-step)

1. **SalesEntry** (`/sales`) — operator picks customer, scans/searches items, saves a **Draft** Sales Invoice (`docstatus=0`, `update_stock=1`). Uses `useBilling.js` composable.
2. **CashierEntry** (`/cashier`) — cashier selects a draft from the list, enters cash/UPI split, and calls `submitInvoiceWithPayment` which submits the invoice and creates Payment Entry(ies) server-side.

### API layer

- **`frontend/src/api.js`** — the canonical transport. Exports `frappeGet` / `frappePost` (low-level) plus all domain functions: customer search, naming series, barcode resolution, item search/price/stock, billing settings, draft invoice CRUD, customer ledger, payment/journal entry creation, supplier/account search.
- **`frontend/src/api/customer.js`** — higher-level helpers for creating Customer + linked Address + Contact in sequence.
- **`frontend/src/services/dashboard.js`** — `dashboardApi` object for dashboard-specific calls: billing settings, allowed series, bulk item/customer sync.
- **`frontend/src/services/api.js`** — older `frappe-ui call()` wrapper. Still referenced in some components; prefer `src/api.js` for new code.
- **`ssplbilling/api/sales_api.py`** — Python `@frappe.whitelist()` methods: `search_customers`, `search_items`, `get_item_insight`, `quick_create_customer`, `create_sales_invoice`, `get_sales_invoices`, `get_sales_invoice`, `submit_invoice_with_payment`, `get_customer_ledger`, `get_voucher_detail`, `get_outstanding_invoices`, `create_payment_entry`, `create_journal_entry`, `search_suppliers`, `search_accounts`.
- **`ssplbilling/api/dashboard_api.py`** — `get_billing_settings`, `get_allowed_series`.

### State management

All billing state lives in **`composables/useBilling.js`** — a Vue 3 composable (not a global store). Owns `form` (header), `rows` (line items), `ui` (loading/errors), `toasts`. Components call its methods; they do not call APIs directly.

### Offline / local caching

**`services/localDb.js`** — IndexedDB wrapper (`sspl_billing_local_db`, v3) with two object stores: `items` (keyed by `item_code`) and `customers` (keyed by `name`). Dashboard syncs up to 5,000 items and customers on load; search components query IndexedDB first for instant results.

### Encryption / settings

**`encryption.js`** — maps price digits to configurable letters (cipher stored in `localStorage['wb-cipher']`) to obscure prices on screen. Also exports `getDefaultTaxRate`, `getDefaultWarehouse`, `getDefaultPriceList`, `getDefaultSeries` from localStorage keys (`wb-*`).

### Authentication

`session.js` exports a singleton wrapping `frappe.auth.get_logged_user`. Router guard calls `session.init()` before every non-public route and redirects to `/login` if unauthenticated.

### Build output

`vite build` writes to `ssplbilling/public/frontend/`. SPA served at `/frontend` (`createWebHistory('/frontend')`).

## Key Conventions

- **Python style**: ruff, `line-length = 110`, tab indentation, `target-version = "py314"`, double-quote strings.
- **JS/Vue style**: prettier + eslint. Tailwind utility classes via `frappe-ui`'s Tailwind preset.
- **Frappe patterns**: All Python API functions must be `@frappe.whitelist()`. Use `frappe.get_cached_doc` for performance. Avoid raw SQL except when Frappe ORM is insufficient.
- **Backup files**: The repo contains `.vue1`, `.vue2`, `.vue3`, `.bak`, `.py1` files — do not delete or confuse them with active source files.
- **SSPL Billing Settings** is a Single DocType with a `billing_series` child table (each row: `series`, `print_format`, `price_list`, `tax_rate`). Fetched via `fetchBillingSettings()` in `api.js`.
