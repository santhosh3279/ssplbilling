# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About

**ssplbilling** is a custom Frappe/ERPNext v16 app for Sundaram and Sons Private Ltd. It provides a fast wholesale billing front-end (Vue 3 SPA) layered on top of ERPNext's Sales Invoice, Customer, Item, and Bin doctypes.

## Repository Layout

```
ssplbilling/                     ← Frappe app root
├── ssplbilling/                 ← Python package
│   ├── api/
│   │   └── sales_api.py         ← Whitelisted Python API endpoints
│   ├── ssplbilling/
│   │   ├── doctype/
│   │   │   ├── sspl_billing_series/
│   │   │   └── sspl_billing_settings/
│   │   └── page/
│   │       └── wholesale_billing/  ← Legacy Frappe desk page (JS/HTML)
│   └── hooks.py                 ← Frappe app hooks
└── frontend/                    ← Vue 3 SPA
    ├── src/
    │   ├── api.js               ← Centralised Frappe REST transport layer
    │   ├── session.js           ← Auth state (isLoggedIn, user, fullName)
    │   ├── router.js            ← Vue Router (base: /frontend)
    │   ├── App.vue
    │   ├── composables/
    │   │   └── useBilling.js    ← All billing state + side-effects
    │   ├── components/
    │   │   └── ItemSearchModal.vue
    │   ├── pages/
    │   │   ├── Login.vue
    │   │   ├── Dashboard.vue
    │   │   ├── SalesEntry.vue       ← Keyboard-driven invoice entry
    │   │   └── WholesaleFastBilling.vue ← Barcode-scan POS screen
    │   └── services/
    │       └── api.js           ← Older frappe-ui `call()`-based helpers
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
pre-commit install                # Run once after cloning
pre-commit run --all-files        # Run all hooks manually
```

Pre-commit runs: **ruff** (import sort + lint), **ruff-format**, **prettier** (JS/Vue/SCSS), **eslint** (JS).

### Python tests

```bash
bench --site <site> run-tests --app ssplbilling
bench --site <site> run-tests --app ssplbilling --module ssplbilling.ssplbilling.doctype.sspl_billing_settings.test_sspl_billing_settings
```

## Architecture

### API Layer (two separate layers)

1. **`frontend/src/api.js`** — the canonical, low-level transport used by the Vue SPA. It uses raw `fetch()` with `X-Frappe-CSRF-Token` headers. All exported functions (`searchCustomers`, `fetchNamingSeries`, `resolveBarcode`, `searchItems`, `fetchItemPrice`, `fetchItemStock`, `fetchItemDetails`, `createSalesInvoice`) call standard Frappe client endpoints (`frappe.client.get_list`, `frappe.client.insert`, etc.).

2. **`frontend/src/services/api.js`** — an older helper using `frappe-ui`'s `call()` wrapper. Still used in some components; prefer `src/api.js` for new code.

3. **`ssplbilling/api/sales_api.py`** — Python-side `@frappe.whitelist()` methods (`get_item_details`, `search_items`, `get_item_insight`, `search_customers`, `quick_create_customer`, `create_sales_invoice`, `get_naming_series`, `get_next_bill_no`). These are alternative server-side endpoints; the Vue SPA currently uses Frappe's built-in client API methods instead.

### State management

All billing state lives in **`composables/useBilling.js`** — a Vue 3 composable (not a global store). It owns:
- `form` (header: date, customer, naming series, payment type)
- `rows` (line items array)
- `ui` (loading flags, validation errors, last saved invoice name)
- `toasts` (ephemeral notification queue)

Components import `useBilling()` and call its methods; they do not make API calls directly.

### Authentication

`session.js` exports a singleton object wrapping `frappe.auth.get_logged_user`. The Vue Router guard in `router.js` calls `session.init()` before every non-public route and redirects to `/login` if not authenticated.

### Build output

`vite build` writes to `ssplbilling/public/frontend/` (derived from the parent directory name). The SPA is served by Frappe at `/frontend` (set as `createWebHistory('/frontend')` in the router).

## Key Conventions

- **Python style**: ruff with `line-length = 110`, tab indentation, `target-version = "py314"`. Double-quote strings per ruff-format config.
- **JS/Vue style**: prettier + eslint (see `.eslintrc`). Tailwind utility classes via `frappe-ui`'s Tailwind preset.
- **Frappe patterns**: All Python API functions must be decorated with `@frappe.whitelist()`. Use `frappe.get_cached_doc` for performance. Avoid raw SQL except when Frappe ORM is insufficient.
- **Backup files**: The repo contains `.vue1`, `.vue2`, `.vue3`, `.bak`, `.py1` files that are work-in-progress backups — do not delete or confuse them with active source files.
