# GEMINI.md

Instructional context for Gemini CLI when working on the **ssplbilling** project.

## Project Overview

**ssplbilling** is a custom Frappe/ERPNext v16 application developed for **Sundaram and Sons Private Ltd**. It provides a high-speed, keyboard-driven wholesale billing interface (Vue 3 SPA) built on top of standard ERPNext doctypes (`Sales Invoice`, `Customer`, `Item`, `Bin`).

### Main Technologies
- **Backend**: Frappe Framework (Python 3.14+), MariaDB.
- **Frontend**: Vue 3 (Composition API), Vite, Tailwind CSS, Frappe UI.
- **State Management**: Vue 3 Composables (primarily `useBilling.js`).
- **Offline Capabilities**: IndexedDB (via `localDb.js`) for caching items and customers.

## Repository Structure

- `ssplbilling/`: Core Frappe app directory.
    - `api/`: Whitelisted Python methods for frontend interaction.
        - `sales_api.py`: Main billing, ledger, and payment logic.
        - `dashboard_api.py`: Settings and dashboard-specific logic.
        - `pricelist_api.py`: Item price management.
        - `purchase_api.py`: Purchase invoice logic.
    - `doctype/`: Custom Frappe DocTypes.
- `frontend/`: Vue 3 Single Page Application.
    - `src/api.js`: Central API service layer (canonical fetch transport).
    - `src/pages/`: Main application views (SalesEntry, PurchaseEntry, CashierEntry, etc.).
    - `src/components/`: Reusable Vue components (Search modals, Print options).
    - `src/shortcuts/`: Keyboard shortcut definitions.
    - `src/services/`: Auxiliary services (IndexedDB wrapper, Dashboard API).

## Building and Running

### Frontend Development (inside `frontend/`)
- **Start Dev Server**: `yarn dev` (Proxies to Frappe; requires `ignore_csrf: 1` in `site_config.json`).
- **Production Build**: `yarn build` (Outputs to `ssplbilling/public/frontend/`).

### Frappe / Bench Commands (from bench root)
- **Start Environment**: `bench start`
- **Apply Migrations**: `bench --site <site> migrate`
- **Build App Assets**: `bench --site <site> build --app ssplbilling`
- **Run Python Tests**: `bench --site <site> run-tests --app ssplbilling`

## Architecture & Workflows

### 1. Two-Step Billing Workflow
1.  **Sales Entry** (`/sales`): Operator enters items and saves a **Draft** Sales Invoice.
2.  **Cashier Entry** (`/cashier`): Cashier selects the draft, processes the payment split (Cash/UPI), and submits the invoice.

### 2. Purchase Workflow
- **Purchase Entry** (`/purchase`): Rapid entry for recording purchases from suppliers into Draft Purchase Invoices.

### 3. Local Caching
The application syncs up to 5,000 items and customers to IndexedDB on dashboard load, allowing for near-instant offline-first search.

## Development Conventions

### Coding Style
- **Python**: Adheres to `ruff` standards. Double-quote strings, tab indentation, line length 110.
- **JavaScript/Vue**: Prettier + ESLint for formatting. Tailwind CSS for styling.
- **Backups**: Avoid deleting or confusing backup files (`.vue1`, `.bak`, etc.) with active source files.

### API Standards
- All Python methods exposed to the frontend must use the `@frappe.whitelist()` decorator.
- Favor `frappe.get_cached_doc` over `frappe.get_doc` for improved performance.
- Use `frontend/src/api.js` as the primary transport layer for all new frontend features.

### Testing
- Python unit tests are located within the `ssplbilling` package.
- CI/CD is managed via GitHub Actions (`ci.yml` and `linter.yml`).

## Git Workflow

- **Pre-Task Commit**: Immediately upon receiving a new prompt, before starting any work, you must check for uncommitted changes. If any exist, stage them (`git add .`) and commit them (`git commit -m "pre-task: capture changes before <brief summary of prompt>"`).
- **Post-Task Commit**: Immediately after completing the tasks requested in a prompt, stage all changes (`git add .`) and commit them with a concise description of the work performed (`git commit -m "<short description>"`).
- **Precedence**: These instructions take absolute precedence over any general mandates against automatic commits.
