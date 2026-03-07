/**
 * api.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Centralised ERPNext / Frappe API service layer.
 * All functions are async and throw on failure so callers can
 * handle errors with try / catch.
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * FRAPPE CALL PATTERNS USED
 * ─────────────────────────
 *  GET  /api/method/frappe.client.get_list?doctype=...&fields=...&filters=...
 *  GET  /api/method/frappe.client.get_meta?doctype=...
 *  POST /api/method/frappe.model.get_series_name  { series }
 *  POST /api/method/frappe.client.insert          { doc }
 *
 * CSRF token is automatically injected from window.csrf_token
 * which Frappe populates on every page load.
 */

// ─── Low-level transport ──────────────────────────────────────────────────────

function csrfToken() {
  return window.csrf_token ?? "fetch";
}

function postHeaders() {
  return {
    "Content-Type": "application/json",
    "X-Frappe-CSRF-Token": csrfToken(),
  };
}

/** Parse Frappe's exc field into a human-readable string */
function parseExc(exc) {
  if (!exc) return "Unknown server error";
  try {
    const lines = JSON.parse(exc);
    const text = Array.isArray(lines) ? lines.join("\n") : String(lines);
    // Return only the last meaningful line (the exception message)
    return text.split("\n").filter(Boolean).pop() ?? "Unknown error";
  } catch {
    return String(exc).split("\n").filter(Boolean).pop() ?? "Unknown error";
  }
}

/**
 * GET a Frappe whitelisted method.
 * @param {string} method  e.g. "frappe.client.get_list"
 * @param {Object} params  key-value pairs; objects/arrays will be JSON-stringified
 */
export async function frappeGet(method, params = {}) {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    qs.set(k, typeof v === "object" ? JSON.stringify(v) : String(v));
  }
  const res = await fetch(`/api/method/${method}?${qs}`, {
    headers: { "X-Frappe-CSRF-Token": csrfToken() },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} — ${res.statusText}`);
  const json = await res.json();
  if (json.exc) throw new Error(parseExc(json.exc));
  return json.message ?? json;
}

/**
 * POST to a Frappe whitelisted method.
 */
export async function frappePost(method, body = {}) {
  const res = await fetch(`/api/method/${method}`, {
    method: "POST",
    headers: postHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} — ${res.statusText}`);
  const json = await res.json();
  if (json.exc) throw new Error(parseExc(json.exc));
  return json.message ?? json;
}

// ─── Customer ─────────────────────────────────────────────────────────────────

/**
 * Search customers by name or ID (partial match) via custom API.
 * Returns customer info including mobile_no and current balance.
 *
 * PYTHON CALL: ssplbilling.api.sales_api.search_customers
 *
 * @returns {Promise<Array<{name: string, customer_name: string, mobile_no: string, balance: number}>>}
 */
export async function searchCustomers(query = "") {
  return frappeGet("ssplbilling.api.sales_api.search_customers", { query });
}

// ─── Naming Series ─────────────────────────────────────────────────────────────

/**
 * Fetch the naming_series options defined on Sales Invoice.
 *
 * FRAPPE CALL:
 *   frappe.client.get_meta("Sales Invoice")
 *   → meta.fields.find(f => f.fieldname === "naming_series").options
 *
 * @returns {Promise<string[]>}  e.g. ["SINV-.YYYY.-", "WINV-.YYYY.-"]
 */
export async function fetchNamingSeries() {
  try {
    const meta = await frappeGet("frappe.client.get_meta", {
      doctype: "Sales Invoice",
    });
    const field = (meta?.fields ?? []).find(
      (f) => f.fieldname === "naming_series"
    );
    if (field?.options) {
      return field.options
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
    }
  } catch (e) {
    console.warn("[api] fetchNamingSeries fallback:", e.message);
  }
  return ["SINV-.YYYY.-", "WINV-.YYYY.-"];
}

/**
 * Preview the NEXT invoice number for a given naming series.
 *
 * FRAPPE CALL:
 *   frappe.model.get_series_name({ series })
 *
 * @returns {Promise<string>}
 */
export async function previewNextInvoiceNo(series) {
  try {
    const result = await frappePost("frappe.model.get_series_name", { series });
    return result ?? "Auto";
  } catch {
    return "Auto";
  }
}

// ─── Barcode & Item Lookup ─────────────────────────────────────────────────────

/**
 * Resolve a barcode string to an item_code.
 * Checks Item Barcode child table first, then falls back to direct item_code match.
 *
 * FRAPPE CALLS:
 *   frappe.client.get_list("Item Barcode", { filters: [["barcode","=",barcode]] })
 *   frappe.client.get_list("Item",         { filters: [["item_code","=",barcode]] })
 *
 * @param {string} barcode
 * @returns {Promise<string|null>}  item_code or null if not found
 */
export async function resolveBarcode(barcode) {
  // 1. Item Barcode child table lookup
  const bcRows = await frappeGet("frappe.client.get_list", {
    doctype: "Item Barcode",
    fields: ["parent"],
    filters: [["barcode", "=", barcode]],
    limit_page_length: 1,
  });
  if (bcRows.length) return bcRows[0].parent;

  // 2. Direct item_code match
  const items = await frappeGet("frappe.client.get_list", {
    doctype: "Item",
    fields: ["item_code"],
    filters: [
      ["item_code", "=", barcode],
      ["disabled", "=", 0],
    ],
    limit_page_length: 1,
  });
  return items.length ? items[0].item_code : null;
}

/**
 * Search items by item_code OR item_name (parallel queries, deduplicated).
 *
 * FRAPPE CALLS (parallel):
 *   frappe.client.get_list("Item", { filters: [["item_code","like","%q%"]] })
 *   frappe.client.get_list("Item", { filters: [["item_name","like","%q%"]] })
 *
 * @returns {Promise<Array<{item_code: string, item_name: string}>>}
 */
export async function searchItems(query) {
  if (!query?.trim()) return [];
  const q = query.trim();

  const [byCode, byName] = await Promise.all([
    frappeGet("frappe.client.get_list", {
      doctype: "Item",
      fields: ["item_code", "item_name"],
      filters: [
        ["item_code", "like", `%${q}%`],
        ["disabled", "=", 0],
      ],
      limit_page_length: 25,
    }),
    frappeGet("frappe.client.get_list", {
      doctype: "Item",
      fields: ["item_code", "item_name"],
      filters: [
        ["item_name", "like", `%${q}%`],
        ["disabled", "=", 0],
      ],
      limit_page_length: 25,
    }),
  ]);

  const seen = new Set();
  return [...byCode, ...byName].filter((i) => {
    if (seen.has(i.item_code)) return false;
    seen.add(i.item_code);
    return true;
  });
}

/**
 * Fetch the selling price of an item from Item Price.
 *
 * FRAPPE CALL:
 *   frappe.client.get_list("Item Price", {
 *     filters: [item_code, price_list, selling=1],
 *     fields: ["price_list_rate"]
 *   })
 *
 * @returns {Promise<number>}
 */
export async function fetchItemPrice(
  itemCode,
  priceList = "Standard Selling"
) {
  try {
    const rows = await frappeGet("frappe.client.get_list", {
      doctype: "Item Price",
      fields: ["price_list_rate"],
      filters: [
        ["item_code", "=", itemCode],
        ["price_list", "=", priceList],
        ["selling", "=", 1],
      ],
      limit_page_length: 1,
      order_by: "valid_from desc",
    });
    return rows.length ? Number(rows[0].price_list_rate) : 0;
  } catch {
    return 0;
  }
}

/**
 * Fetch available stock (sum of actual_qty across all Bin rows).
 *
 * FRAPPE CALL:
 *   frappe.client.get_list("Bin", {
 *     filters: [["item_code","=",itemCode]],
 *     fields: ["actual_qty","warehouse"]
 *   })
 *
 * @returns {Promise<number>}
 */
export async function fetchItemStock(itemCode, warehouse = null) {
  try {
    const filters = [["item_code", "=", itemCode]];
    if (warehouse) filters.push(["warehouse", "=", warehouse]);

    const bins = await frappeGet("frappe.client.get_list", {
      doctype: "Bin",
      fields: ["actual_qty", "warehouse"],
      filters,
      limit_page_length: 100,
    });
    return bins.reduce((s, b) => s + Number(b.actual_qty || 0), 0);
  } catch {
    return 0;
  }
}

/**
 * Fetch available stock summed across a specific list of warehouses.
 * Pass an empty array to sum all warehouses.
 *
 * @param {string} itemCode
 * @param {string[]} warehouses  e.g. ["Stores - SSPL", "Finished Goods - SSPL"]
 * @returns {Promise<number>}
 */
export async function fetchItemStockForWarehouses(itemCode, warehouses = []) {
  try {
    const filters = [["item_code", "=", itemCode]];
    if (warehouses.length) filters.push(["warehouse", "in", warehouses]);
    const bins = await frappeGet("frappe.client.get_list", {
      doctype: "Bin",
      fields: ["actual_qty"],
      filters,
      limit_page_length: 100,
    });
    return bins.reduce((s, b) => s + Number(b.actual_qty || 0), 0);
  } catch {
    return 0;
  }
}

/**
 * Convenience: fetch price + stock in parallel.
 * @returns {Promise<{price: number, stock: number}>}
 */
export async function fetchItemDetails(
  itemCode,
  priceList = "Standard Selling",
  warehouse = null
) {
  const [price, stock] = await Promise.all([
    fetchItemPrice(itemCode, priceList),
    fetchItemStock(itemCode, warehouse),
  ]);
  return { price, stock };
}

// ─── SSPL Billing Settings ────────────────────────────────────────────────────

/**
 * Fetch the SSPL Billing Settings Single DocType.
 * Returns the document including the billing_series child table rows,
 * each with: series, print_format, price_list, tax_rate.
 * @returns {Promise<Object>}
 */
export async function fetchBillingSettings() {
  return frappeGet('frappe.client.get', {
    doctype: 'SSPL Billing Settings',
    name: 'SSPL Billing Settings',
  })
}

// ─── Cashier / Draft Invoice Helpers ─────────────────────────────────────────

/**
 * Fetch all Draft Sales Invoices (docstatus=0), optionally filtered by query.
 *
 * PYTHON CALL: ssplbilling.api.sales_api.get_sales_invoices
 *
 * @param {string} [query]  Search text (invoice name or customer name)
 * @param {number} [limit]  Max rows to return (default 50)
 * @returns {Promise<Array<{name,customer,customer_name,posting_date,grand_total}>>}
 */
export async function fetchDraftInvoices(query = "", limit = 50, postingDate = "") {
  return frappeGet("ssplbilling.api.sales_api.get_sales_invoices", {
    query,
    limit,
    ...(postingDate && { posting_date: postingDate }),
  });
}

/**
 * Fetch full details of a single Sales Invoice (must be Draft).
 *
 * PYTHON CALL: ssplbilling.api.sales_api.get_sales_invoice
 *
 * @param {string} invoiceName
 * @returns {Promise<Object>}  Invoice doc with items array
 */
export async function getInvoiceDetails(invoiceName) {
  return frappeGet("ssplbilling.api.sales_api.get_sales_invoice", {
    invoice_name: invoiceName,
  });
}

/**
 * Submit a Draft Sales Invoice and create Payment Entry(ies).
 *
 * PYTHON CALL: ssplbilling.api.sales_api.submit_invoice_with_payment
 *
 * @param {{invoice_name: string, cash_amount: number, upi_amount: number}} payload
 * @returns {Promise<{invoice_name, payment_entries, grand_total, status}>}
 */
export async function submitInvoiceWithPayment(payload) {
  return frappePost("ssplbilling.api.sales_api.submit_invoice_with_payment", {
    data: JSON.stringify(payload),
  });
}

// ─── Customer Ledger ──────────────────────────────────────────────────────────

/**
 * Fetch GL Entry rows for a customer with running balance.
 *
 * PYTHON CALL: ssplbilling.api.sales_api.get_customer_ledger
 *
 * @param {string} customer   Customer name / ID
 * @param {string} fromDate   ISO date "YYYY-MM-DD"
 * @param {string} toDate     ISO date "YYYY-MM-DD"
 * @returns {Promise<{customer, customer_name, from_date, to_date,
 *   opening_balance, closing_balance, total_debit, total_credit, entries}>}
 */
export async function fetchCustomerLedger(customer, fromDate, toDate) {
  return frappeGet("ssplbilling.api.sales_api.get_customer_ledger", {
    customer,
    from_date: fromDate,
    to_date: toDate,
  });
}

/**
 * Fetch summary detail for a voucher (Sales Invoice, Payment Entry, etc.)
 *
 * PYTHON CALL: ssplbilling.api.sales_api.get_voucher_detail
 *
 * @param {string} voucherType  e.g. "Sales Invoice"
 * @param {string} voucherNo    e.g. "SINV-2026-001"
 * @returns {Promise<Object>}
 */
export async function fetchVoucherDetail(voucherType, voucherNo) {
  return frappeGet("ssplbilling.api.sales_api.get_voucher_detail", {
    voucher_type: voucherType,
    voucher_no: voucherNo,
  });
}

// ─── Payment Entry (direct) ───────────────────────────────────────────────────

/**
 * Fetch submitted Sales Invoices with outstanding balance for a customer.
 */
export async function fetchOutstandingInvoices(customer) {
  return frappeGet("ssplbilling.api.sales_api.get_outstanding_invoices", { customer })
}

/**
 * Fetch submitted Purchase Invoices with outstanding balance for a supplier.
 */
export async function fetchOutstandingPurchaseInvoices(supplier) {
  return frappeGet("ssplbilling.api.sales_api.get_outstanding_purchase_invoices", { supplier })
}

/**
 * Create and submit a Payment Entry (Receive / Pay / Internal Transfer).
 */
export async function createPaymentEntry(payload) {
  return frappePost("ssplbilling.api.sales_api.create_payment_entry", {
    data: JSON.stringify(payload),
  })
}

/**
 * Create and submit a Journal Entry.
 */
export async function createJournalEntry(payload) {
  return frappePost("ssplbilling.api.sales_api.create_journal_entry", {
    data: JSON.stringify(payload),
  })
}

/**
 * Search suppliers by name.
 */
export async function searchSuppliers(query = "") {
  return frappeGet("ssplbilling.api.sales_api.search_suppliers", { query })
}

/**
 * Search chart of accounts.
 * @param {string} query  Partial account name
 * @param {string|null} accountType  Optional filter: "Cash", "Bank", "CashBank", etc.
 */
export async function searchAccounts(query = "", accountType = null) {
  return frappeGet("ssplbilling.api.sales_api.search_accounts", {
    query,
    ...(accountType && { account_type: accountType }),
  })
}

// ─── Sales Invoice ─────────────────────────────────────────────────────────────

/**
 * Create and submit a Sales Invoice.
 *
 * FRAPPE CALL:
 *   frappe.client.insert({ doctype: "Sales Invoice", ... })
 *
 * @param {{
 *   customer: string,
 *   postingDate: string,
 *   namingSeries: string,
 *   paymentType: "Cash"|"Credit",
 *   grandTotal: number,
 *   items: Array<{itemCode, itemName, qty, rate, discount, amount}>
 * }} payload
 *
 * @returns {Promise<{name: string, ...}>}  Saved doc from Frappe
 */
export async function createSalesInvoice(payload) {
  const isCash = payload.paymentType === "Cash";

  const doc = {
    doctype: "Sales Invoice",
    naming_series: payload.namingSeries,
    customer: payload.customer,
    posting_date: payload.postingDate,
    due_date: payload.postingDate,
    is_pos: 0,
    update_stock: 1,
    items: payload.items.map((r) => ({
      item_code: r.itemCode,
      item_name: r.itemName,
      qty: Number(r.qty),
      rate: Number(r.rate),
      discount_percentage: Number(r.discount || 0),
      amount: Number(r.amount),
    })),
    ...(isCash && {
      payments: [
        {
          mode_of_payment: "Cash",
          amount: payload.grandTotal,
        },
      ],
    }),
  };

  return frappePost("frappe.client.insert", { doc });
}
