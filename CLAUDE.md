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
│   │   ├── purchase_api.py      ← Purchase invoice management endpoints
│   │   ├── item_api.py          ← Item creation and metadata endpoints
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
    │   │   ├── ItemSearch.vue
    │   │   ├── ItemCreation.vue
    │   │   ├── CustomerSearchModal.vue
    │   │   └── PrintOptionsModal.vue
    │   ├── pages/
    │   │   ├── Login.vue
    │   │   ├── Dashboard.vue        ← Syncs items/customers to IndexedDB on load
    │   │   ├── SalesEntry.vue       ← Keyboard-driven draft invoice entry
    │   │   ├── Cashierpage.vue      ← Lists drafts; submits with multi-mode payment split
    │   │   ├── CustomerLedger.vue   ← GL ledger with running balance per customer
    │   │   ├── Payment.vue          ← Direct payment / receipt entry creation
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
2. **Cashierpage** (`/cashier`) — cashier selects a draft from the list, enters multi-mode payment split, and calls `submitInvoiceWithPayment`.

### API layer

- **`frontend/src/api.js`** — the canonical transport. Exports `frappeGet` / `frappePost` (low-level) plus all domain functions: customer search, naming series, barcode resolution, item search/price/stock, billing settings, draft invoice CRUD, customer ledger, payment/journal entry creation, supplier/account search.
- **`frontend/src/api/customer.js`** — higher-level helpers for creating Customer + linked Address + Contact in sequence.
- **`frontend/src/services/dashboard.js`** — `dashboardApi` object for dashboard-specific calls: billing settings, allowed series, bulk item/customer sync.
- **`frontend/src/services/api.js`** — older `frappe-ui call()` wrapper. Still referenced in some components; prefer `src/api.js` for new code.
- **`ssplbilling/api/SaleEntry_api.py`** — Python `@frappe.whitelist()` methods for Sales Entry: `search_items`, `get_item_insight`, `create_sales_invoice`, `update_sales_invoice`, `delete_sales_invoice`, `get_naming_series`, `get_discount_rules`.
- **`ssplbilling/api/cashier_api.py`** — `get_sales_invoices`, `get_sales_invoice`, `submit_invoice_with_payment`.
- **`ssplbilling/api/ledger_api.py`** — `get_ledger`, `get_customer_ledger`, `get_voucher_detail`, `get_outstanding_invoices`, `create_payment_entry`, `create_journal_entry`, `search_accounts`.
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

## Git Workflow

> **MANDATORY — do this for every task without exception.**

**Step 1 — before touching any file**, run the pre-task checkpoint commit:

```bash
git add -A && git commit -m "chore: checkpoint before <brief description of upcoming task>"
```

**Step 2 — after the task is fully done**, run the post-task commit:

```bash
git add -A && git commit -m "<type>: <description of what was done>"
```

Both commits are required for every task, no matter how small. The before-commit captures the baseline; the after-commit records the change. Skipping either is not allowed.

Use conventional commit types: `feat`, `fix`, `refactor`, `chore`, `docs`, `style`, `test`.

## Response Format

> **MANDATORY — include this at the end of every response that changes files.**

After completing a task, always include a line-count table for every affected file:

| File | Before | After | +/- |
|------|--------|-------|-----|
| `path/to/file.vue` | 210 | 245 | +35 |

Use `wc -l` to get accurate counts. Never estimate or skip this table.

## Adding a New Page

> **MANDATORY — a new page is not done until its tile is registered in the dashboard tile access list.**
> Skipping the tile registration means the page exists but no non-admin user can ever be granted it.

1. **Page** — create `frontend/src/pages/<Name>.vue`.
2. **Route** — `frontend/src/router.js`: add the import and a route entry with a unique `name`.
3. **Tile master (the tile access list)** — add a `("<tile-id>", "<Label>", "<Bucket>")` tuple to `DASHBOARD_TILES` in `ssplbilling/setup.py`. `sync_dashboard_tiles()` upserts the **SSPL Dashboard Tile** records on every `bench migrate` (via the `after_migrate` hook); those records are exactly what the **SSPL Dashboard Tile Access** doctype offers for selection. Existing buckets: `Sales`, `Purchase`, `Stock`, `Accounts`, `Ledger View`, `SSPL Special`, `Report`.
4. **Dashboard tile** — add `{ id, bucket, name, desc, icon, shortcut }` to the `allTiles` array in `frontend/src/pages/Dashboard.vue`. Bucket keys there are lowercase: `sales | purchase | stock | accounts | ledger | sspl | report`.
5. **Tile navigation** — `openModule()` in `Dashboard.vue` pushes `/<tile-id>`. If the route path differs from the tile id, add `'<tile-id>': '/actual/path'` to `routeAliases`. Either way add the tile id to `readyModules`, or clicking the tile alerts "Coming soon".
6. **Route permission** — `frontend/src/composables/usePermission.js`: add `'<tile-id>': '<RouteName>'` to `TILE_ROUTE_MAP`, and add `<RouteName>` to the relevant role set (`BILLER_ROUTES` / `CASHIER_EXTRA_ROUTES` / `ACCOUNTS_ROUTES`), which is the fallback used when no tile access record is configured.
7. **Apply** — `bench --site <site> migrate` (syncs the tile), then `yarn build` in `frontend/`.

Verify the tile landed:

```bash
bench --site <site> execute frappe.client.get_value \
  --kwargs "{'doctype':'SSPL Dashboard Tile','filters':{'name':'<tile-id>'},'fieldname':'tile_label'}"
```

**Sub-pages that have no tile of their own** (e.g. `/hrms/employees`, `/hrms/essl-machines`): skip steps 3–5, and do **not** add them to `TILE_ROUTE_MAP` — that map is reverse-searched by the license `features` gate, so a route mapped to a tile id absent from the license is blocked outright. Grant them explicitly inside the tile-override block of `canAccessRoute` instead, keyed on the parent tile:

```js
if (tileIds.includes('hrms')) allowed.add('EsslMachines')
```

## Key Conventions

- **Python style**: ruff, `line-length = 110`, tab indentation, `target-version = "py314"`, double-quote strings.
- **JS/Vue style**: prettier + eslint. Tailwind utility classes via `frappe-ui`'s Tailwind preset.
- **Frappe patterns**: All Python API functions must be `@frappe.whitelist()`. Use `frappe.get_cached_doc` for performance. Avoid raw SQL except when Frappe ORM is insufficient.
- **Backup files**: The repo contains `.vue1`, `.vue2`, `.vue3`, `.bak`, `.py1` files — do not delete or confuse them with active source files.
- **SSPL Billing Settings** is a Single DocType with a `billing_series` child table (each row: `series`, `print_format`, `price_list`, `tax_rate`). Fetched via `fetchBillingSettings()` in `api.js`.
