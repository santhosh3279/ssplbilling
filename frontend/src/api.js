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

/** Parse Frappe's exc field into a human-readable string (last line only) */
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

/** Parse Frappe's exc field into the full traceback string */
function parseExcFull(exc) {
  if (!exc) return "Unknown server error";
  try {
    const lines = JSON.parse(exc);
    return Array.isArray(lines) ? lines.join("\n") : String(lines);
  } catch {
    return String(exc);
  }
}

/** Show full error traceback in a browser alert */
function alertPostError(context, fullTrace) {
  window.alert(`POST ERROR — ${context}\n\n${fullTrace}`);
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
 * On any error the full traceback is shown in a browser alert before throwing.
 */
export async function frappePost(method, body = {}) {
  let res;
  try {
    res = await fetch(`/api/method/${method}`, {
      method: "POST",
      headers: postHeaders(),
      body: JSON.stringify(body),
    });
  } catch (networkErr) {
    const msg = `Network error: ${networkErr.message}`;
    alertPostError(method, msg);
    throw new Error(msg);
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status} — ${res.statusText}`;
    try {
      const errJson = await res.clone().json();
      if (errJson.exc) {
        detail += "\n\n" + parseExcFull(errJson.exc);
      } else if (errJson.message) {
        detail += "\n\n" + JSON.stringify(errJson.message, null, 2);
      } else {
        detail += "\n\n" + JSON.stringify(errJson, null, 2);
      }
    } catch {
      try { detail += "\n\n" + (await res.text()); } catch { /* ignore */ }
    }
    alertPostError(method, detail);
    throw new Error(detail);
  }

  const json = await res.json();
  if (json.exc) {
    const fullTrace = parseExcFull(json.exc);
    const shortMsg = parseExc(json.exc);
    alertPostError(method, fullTrace);
    throw new Error(shortMsg);
  }
  return json.message ?? json;
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
  priceList = "Standard Selling",
  uom = null
) {
  try {
    const filters = [
      ["item_code", "=", itemCode],
      ["price_list", "=", priceList],
      ["selling", "=", 1],
    ];
    if (uom) filters.push(["uom", "=", uom]);
    
    const rows = await frappeGet("frappe.client.get_list", {
      doctype: "Item Price",
      fields: ["price_list_rate"],
      filters: filters,
      limit_page_length: 1,
      order_by: "valid_from desc",
    });
    
    if (rows.length) return Number(rows[0].price_list_rate);
    
    // If not found with specific UOM, try without UOM filter
    if (uom) {
      const rowsAnyUom = await frappeGet("frappe.client.get_list", {
        doctype: "Item Price",
        fields: ["price_list_rate"],
        filters: [
          ["item_code", "=", itemCode],
          ["price_list", "=", priceList],
          ["selling", "=", 1],
          ["uom", "=", ""],
        ],
        limit_page_length: 1,
        order_by: "valid_from desc",
      });
      return rowsAnyUom.length ? Number(rowsAnyUom[0].price_list_rate) : 0;
    }
    
    return 0;
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
export async function fetchBillingSettings(user = null) {
  if (user) {
    return frappeGet('ssplbilling.api.dashboard_api.get_billing_settings', { user })
  }
  return frappeGet('frappe.client.get', {
    doctype: 'SSPL Billing Settings',
    name: 'SSPL Billing Settings',
  })
}

/**
 * Fetch dashboard/billing settings resolved for the current user.
 * 
 * PYTHON CALL: ssplbilling.api.dashboard_api.get_billing_settings
 */
export async function fetchDashboardSettings(user = null) {
  return frappeGet("ssplbilling.api.dashboard_api.get_billing_settings", { user });
}

/**
 * Fetch the dashboard tiles allowed via SSPL Dashboard Tile Access, resolved for the
 * given (inherited) user — admin only; the server falls back to the logged-in user.
 * Returns { configured: bool, tiles: string[]|null }; tiles is null when no
 * user/group record applies and the caller should fall back to role-based filtering.
 *
 * PYTHON CALL: ssplbilling.api.dashboard_api.get_allowed_tiles
 */
export async function fetchAllowedTiles(user = null) {
  return frappeGet("ssplbilling.api.dashboard_api.get_allowed_tiles", user ? { user } : {});
}

// ─── Cashier / Draft Invoice Helpers ─────────────────────────────────────────

/**
 * Fetch all Draft Sales Invoices, optionally filtered by query.
 *
 * PYTHON CALL: ssplbilling.api.cashier_api.get_sales_invoices
 *
 * @param {string} [query]  Search text (invoice name or customer name)
 * @param {number} [limit]  Max rows to return (default 50)
 * @param {string} [postingDate]
 * @returns {Promise<Array<{name,customer,customer_name,posting_date,grand_total,outstanding_amount,docstatus}>>}
 */
export async function fetchDraftInvoices(query = "", limit = 50, postingDate = "", namingSeries = "") {
  const company = localStorage.getItem("wb-company") || "";
  return frappeGet("ssplbilling.api.cashier_api.get_sales_invoices", {
    query,
    limit,
    ...(postingDate && { posting_date: postingDate }),
    ...(namingSeries && { naming_series: namingSeries }),
    ...(company && { company }),
    draft_only: true
  });
}

/**
 * Fetch full details of a single Sales Invoice (must be Draft).
 *
 * PYTHON CALL: ssplbilling.api.cashier_api.get_sales_invoice
 *
 * @param {string} invoiceName
 * @returns {Promise<Object>}  Invoice doc with items array
 */
export async function getInvoiceDetails(invoiceName) {
  return frappeGet("ssplbilling.api.cashier_api.get_sales_invoice", {
    invoice_name: invoiceName,
  });
}

/**
 * Submit a Draft Sales Invoice and create Payment Entry(ies).
 *
 * PYTHON CALL: ssplbilling.api.cashier_api.submit_invoice_with_payment
 *
 * @param {{invoice_name: string, cash_amount: number, upi_amount: number}} payload
 * @returns {Promise<{invoice_name, payment_entries, grand_total, status}>}
 */
export async function submitInvoiceWithPayment(payload) {
  return frappePost("ssplbilling.api.cashier_api.submit_invoice_with_payment", {
    data: JSON.stringify(payload),
  });
}

/**
 * Fetch GL Entry rows for a ledger (Customer, Supplier, or Account) with running balance.
 *
 * @param {string} ledgerName
 * @param {string} ledgerType  'Customer', 'Supplier', or 'Account'
 * @param {string} fromDate    ISO date
 * @param {string} toDate      ISO date
 */
export async function fetchLedger(ledgerName, ledgerType, fromDate, toDate) {
  return frappeGet("ssplbilling.api.ledger_api.get_ledger", {
    ledger_name: ledgerName,
    ledger_type: ledgerType,
    from_date: fromDate,
    to_date: toDate,
    company: localStorage.getItem('wb-company') || '',
  });
}

// ─── Customer Ledger ──────────────────────────────────────────────────────────

/**
 * Fetch GL Entry rows for a customer with running balance.
 *
 * PYTHON CALL: ssplbilling.api.ledger_api.get_customer_ledger
 *
 * @param {string} customer   Customer name / ID
 * @param {string} fromDate   ISO date "YYYY-MM-DD"
 * @param {string} toDate     ISO date "YYYY-MM-DD"
 * @returns {Promise<{customer, customer_name, from_date, to_date,
 *   opening_balance, closing_balance, total_debit, total_credit, entries}>}
 */
export async function fetchCustomerLedger(customer, fromDate, toDate) {
  return frappeGet("ssplbilling.api.ledger_api.get_customer_ledger", {
    customer,
    from_date: fromDate,
    to_date: toDate,
    company: localStorage.getItem('wb-company') || '',
  });
}

/**
 * Fetch summary detail for a voucher (Sales Invoice, Payment Entry, etc.)
 *
 * PYTHON CALL: ssplbilling.api.ledger_api.get_voucher_detail
 *
 * @param {string} voucherType  e.g. "Sales Invoice"
 * @param {string} voucherNo    e.g. "SINV-2026-001"
 * @returns {Promise<Object>}
 */
export async function fetchVoucherDetail(voucherType, voucherNo) {
  return frappeGet("ssplbilling.api.ledger_api.get_voucher_detail", {
    voucher_type: voucherType,
    voucher_no: voucherNo,
  });
}

// ─── Stock Ledger ─────────────────────────────────────────────────────────────

/**
 * Fetch Stock Ledger Entry rows for an item with summary stats.
 *
 * @param {string} itemCode
 * @param {string} fromDate
 * @param {string} toDate
 * @param {string|null} warehouse
 * @returns {Promise<Object>}
 */
export async function fetchStockLedger(itemCode, fromDate, toDate, warehouse = null, company = null) {
  return frappeGet("ssplbilling.api.ledger_api.get_erpnext_stock_ledger", {
    item_code: itemCode,
    from_date: fromDate,
    to_date: toDate,
    warehouse: warehouse,
    company: company,
  });
}

// ─── Payment Entry (direct) ───────────────────────────────────────────────────

/**
 * Fetch outstanding invoices for a customer using ERPNext's Payment Ledger Entry
 * (same logic as the "Get Outstanding Invoices" button in Payment Entry doctype).
 * Returns objects with: voucher_type, voucher_no, invoice_amount, outstanding_amount, due_date
 */
export async function fetchOutstandingInvoices(customer) {
  return frappeGet("ssplbilling.api.ledger_api.get_outstanding_invoices", { party: customer, party_type: "Customer" })
}

/**
 * Fetch submitted Purchase Invoices with outstanding balance for a supplier.
 */
export async function fetchOutstandingPurchaseInvoices(supplier) {
  return frappeGet("ssplbilling.api.supplier_creator_api.get_outstanding_purchase_invoices", { supplier })
}

/**
 * Create and submit a Payment Entry (Receive / Pay / Internal Transfer).
 */
export async function createPaymentEntry(payload) {
  return frappePost("ssplbilling.api.ledger_api.create_payment_entry", {
    data: JSON.stringify(payload),
  })
}

/**
 * Create and submit a Journal Entry.
 */
export async function createJournalEntry(payload) {
  return frappePost("ssplbilling.api.ledger_api.create_journal_entry", {
    data: JSON.stringify(payload),
  })
}

/**
 * Search suppliers by name.
 */
export async function searchSuppliers(query = "") {
  return frappeGet("ssplbilling.api.supplier_creator_api.search_suppliers", { query })
}

/**
 * Search chart of accounts.
 * @param {string} query  Partial account name
 * @param {string|null} accountType  Optional filter: "Cash", "Bank", "CashBank", etc.
 */
export async function searchAccounts(query = "", accountType = null) {
  return frappeGet("ssplbilling.api.ledger_api.search_accounts", {
    query,
    ...(accountType && { account_type: accountType }),
  })
}

// ─── Reconciliation Helpers ───────────────────────────────────────────

export async function getUnlinkedEntries(partyType, party) {
  return frappeGet("ssplbilling.api.reconcile_api.get_unlinked_entries", {
    party_type: partyType,
    party,
  })
}

export async function getUnlinkedOppositeEntries(partyType, party) {
  return frappeGet("ssplbilling.api.reconcile_api.get_unlinked_opposite_entries", {
    party_type: partyType,
    party,
  })
}

export async function getOutstandingDocs(partyType, party) {
  return frappeGet("ssplbilling.api.reconcile_api.get_outstanding_docs", {
    party_type: partyType,
    party,
  })
}

export async function postReconciliation(partyType, party, allocations) {
  return frappePost("ssplbilling.api.reconcile_api.post_reconciliation", {
    party_type: partyType,
    party,
    allocations: JSON.stringify(allocations),
  })
}

export async function postCrossReconciliation(partyType, party, allocations) {
  return frappePost("ssplbilling.api.reconcile_api.post_cross_reconciliation", {
    party_type: partyType,
    party,
    allocations: JSON.stringify(allocations),
  })
}

export async function searchEmployees(query = "") {
  return frappeGet("ssplbilling.api.incentive_ledger_api.search_employees", { query })
}

// ─── Purchase Invoice Helpers ─────────────────────────────────────────

/**
 * Fetch Purchase Invoices.
 */
export async function fetchPurchaseInvoices(query = "", limit = 50, postingDate = "", draftOnly = false) {
  return frappeGet("ssplbilling.api.purchase_api.get_purchase_invoices", {
    query,
    limit,
    ...(postingDate && { posting_date: postingDate }),
    ...(draftOnly && { draft_only: true }),
  });
}

/**
 * Fetch full details of a single Purchase Invoice.
 */
export async function getPurchaseInvoiceDetails(invoiceName) {
  return frappeGet("ssplbilling.api.purchase_api.get_purchase_invoice", {
    invoice_name: invoiceName,
  });
}

/**
 * Submit a Draft Purchase Invoice.
 */
export async function submitPurchaseInvoice(invoiceName) {
  return frappePost("ssplbilling.api.purchase_api.submit_purchase_invoice", {
    invoice_name: invoiceName,
  });
}

/**
 * Link a supplier to multiple items in the Item Master.
 */
export async function linkSupplierToItems(supplier, items) {
  return frappePost("ssplbilling.api.purchase_api.link_supplier_to_items", {
    supplier,
    items: JSON.stringify(items),
  });
}


// ─── Item Creation Helpers ─────────────────────────────────────────

/**
 * Fetch metadata for item creation.
 */
let _itemCreationMetadataCache = null
export async function fetchItemCreationMetadata() {
  if (!_itemCreationMetadataCache) {
    _itemCreationMetadataCache = await frappeGet("ssplbilling.api.item_api.get_item_creation_metadata")
  }
  return _itemCreationMetadataCache
}

/**
 * Get next barcode from naming series.
 */
export async function getNextBarcode(namingSeries) {
  return frappeGet("ssplbilling.api.item_api.get_next_barcode", { naming_series: namingSeries });
}

/**
 * Create a new item.
 */
export async function createItem(data) {
  return frappePost("ssplbilling.api.item_api.create_item", { data });
}

export async function getItemForEdit(itemCode) {
  return frappeGet("ssplbilling.api.item_api.get_item_for_edit", { item_code: itemCode });
}

export async function updateItem(data) {
  return frappePost("ssplbilling.api.item_api.update_item", { data });
}

/**
 * Upload a file using Frappe's standard /api/method/upload_file endpoint.
 * @param {File} file
 * @param {Object} [args]  Optional additional parameters like is_private, folder
 * @returns {Promise<Object>} The uploaded file document
 */
export async function uploadFile(file, args = {}) {
  const formData = new FormData();
  formData.append("file", file, file.name);
  formData.append("is_private", args.is_private ? "1" : "0");
  formData.append("folder", args.folder || "Home");

  if (args.doctype) formData.append("doctype", args.doctype);
  if (args.docname) formData.append("docname", args.docname);
  if (args.fieldname) formData.append("fieldname", args.fieldname);

  const res = await fetch("/api/method/upload_file", {
    method: "POST",
    headers: {
      "X-Frappe-CSRF-Token": csrfToken(),
    },
    body: formData,
  });

  if (!res.ok) throw new Error(`Upload failed: HTTP ${res.status} — ${res.statusText}`);
  const json = await res.json();
  if (json.exc) throw new Error(parseExc(json.exc));
  return json.message ?? json;
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
  const company = localStorage.getItem("wb-company") || undefined;

  const doc = {
    doctype: "Sales Invoice",
    company,
    naming_series: payload.namingSeries,
    customer: payload.customer,
    customer_address: payload.customer_address,
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


// ─── Single Entry (Bulk Payment) ─────────────────────────────────────────────

/**
 * Closing balance for one party row in the bulk payment screen.
 * @param {string} party
 * @param {string} partyType  'Customer' | 'Supplier'
 */
export async function fetchPartyBalance(party, partyType = "Customer") {
  return frappeGet("ssplbilling.api.single_entry_api.get_party_balance", {
    party,
    party_type: partyType,
  });
}

/**
 * Outstanding invoices + unlinked entries for a party — single round-trip.
 * Returns { docs, payment_entries, journal_entries }
 */
export async function fetchPartyDocs(partyType, party) {
  return frappeGet("ssplbilling.api.single_entry_api.get_party_docs", {
    party_type: partyType,
    party,
  });
}

/**
 * Create and submit one Payment Entry row from the bulk entry screen.
 * @param {Object} payload  Same shape as createPaymentEntry
 */
export async function createBulkPaymentEntry(payload) {
  return frappePost("ssplbilling.api.single_entry_api.create_bulk_payment", {
    data: JSON.stringify(payload),
  });
}

// ─── GST & India Compliance ──────────────────────────────────────────────────

/**
 * Validate a GSTIN and fetch business details using India Compliance.
 * @param {string} gstin
 * @returns {Promise<Object>}
 */
export async function validateGstin(gstin) {
  return frappeGet("ssplbilling.api.gst_api.validate_gstin", { gstin });
}

// ─── Reports ──────────────────────────────────────────────────────────────────

/**
 * Fetch Sales Tax Account Register rows for a naming series + date range.
 * @param {string} series   e.g. "SINV-.YYYY.-"
 * @param {string} fromDate  "YYYY-MM-DD"
 * @param {string} toDate    "YYYY-MM-DD"
 * @returns {Promise<Array>}
 */
export async function getSalesTaxRegister(series, fromDate, toDate) {
  return frappeGet("ssplbilling.api.reports_api.get_sales_tax_register", {
    series,
    from_date: fromDate,
    to_date: toDate,
    company: localStorage.getItem("wb-company") || undefined,
  });
}

/**
 * Fetch naming series options for Quotation doctype.
 */
export async function getQuotationSeries() {
  return frappeGet("ssplbilling.api.reports_api.get_quotation_series", {});
}

/**
 * Fetch Cashflow Report data.
 */
export async function getCashflowReport(fromDate, toDate, company) {
  return frappeGet("ssplbilling.api.reports_api.get_cashflow_report", {
    from_date: fromDate,
    to_date: toDate,
    company: company || localStorage.getItem("wb-company") || undefined,
  });
}

/**
 * Fetch Quotation Tax Register data.
 */
export async function getQuotationTaxRegister(series, fromDate, toDate) {
  return frappeGet("ssplbilling.api.reports_api.get_quotation_tax_register", {
    series,
    from_date: fromDate,
    to_date: toDate,
    company: localStorage.getItem("wb-company") || undefined,
  });
}

/**
 * Fetch HSN Summary Report for Sales Invoices.
 */
export async function getHsnSummaryReport(series, fromDate, toDate) {
  return frappeGet("ssplbilling.api.reports_api.get_hsn_summary_report", {
    series,
    from_date: fromDate,
    to_date: toDate,
    company: localStorage.getItem("wb-company") || undefined,
  });
}

/**
 * Fetch HSN Summary Report for Quotations.
 */
export async function getQuotationHsnSummaryReport(series, fromDate, toDate) {
  return frappeGet("ssplbilling.api.reports_api.get_quotation_hsn_summary_report", {
    series,
    from_date: fromDate,
    to_date: toDate,
    company: localStorage.getItem("wb-company") || undefined,
  });
}

/**
 * Fetch Item Sales Summary Report.
 */
export async function getItemSummaryReport(series, fromDate, toDate) {
  return frappeGet("ssplbilling.api.reports_api.get_item_summary_report", {
    series,
    from_date: fromDate,
    to_date: toDate,
    company: localStorage.getItem("wb-company") || undefined,
  });
}

export async function getStoreWiseItemSalesReport(fromDate, toDate, incomeAccount) {
  return frappeGet("ssplbilling.api.reports_api.get_store_wise_item_sales_report", {
    from_date: fromDate,
    to_date: toDate,
    income_account: incomeAccount,
    company: localStorage.getItem("wb-company") || undefined,
  });
}

/**
 * Fetch Fast Moving Items Report.
 */
export async function getFastMovingItemsReport(fromDate, toDate, series, incomeAccount, limit, company) {
  return frappeGet("ssplbilling.api.reports_api.get_fast_moving_items_report", {
    from_date: fromDate,
    to_date: toDate,
    series: series,
    income_account: incomeAccount,
    limit: limit,
    company: company || localStorage.getItem("wb-company") || undefined,
  });
}

/**
 * Fetch list of income accounts.
 */
export async function getIncomeAccounts() {
  return frappeGet("ssplbilling.api.reports_api.get_income_accounts", {
    company: localStorage.getItem("wb-company") || undefined,
  });
}

/**
 * Fetch Store Sale Report (Sales by Store/Cost Center from Direct Income).
 */
export async function getStoreSaleReport(fromDate, toDate, company) {
  return frappeGet("ssplbilling.api.reports_api.get_store_sale_report", {
    from_date: fromDate,
    to_date: toDate,
    company: company || localStorage.getItem("wb-company") || undefined,
  });
}

/**
 * Fetch Cost Center Sale Report (Sales by Cost Center from Direct Income).
 */
export async function getCostCenterSaleReport(fromDate, toDate, company) {
  return frappeGet("ssplbilling.api.reports_api.get_cost_center_sale_report", {
    from_date: fromDate,
    to_date: toDate,
    company: company || localStorage.getItem("wb-company") || undefined,
  });
}

export async function getCompanies() {
  return frappeGet("ssplbilling.api.reports_api.get_companies");
}

export async function getUnpostedBills(user, costCenter) {
  const params = { user };
  if (costCenter) params.cost_center = costCenter;
  return frappeGet("ssplbilling.api.incentive_api.get_unposted_bills", params);
}

export async function calculateBillIncentive(doctype, name) {
  return frappeGet("ssplbilling.api.incentive_api.calculate_bill_incentive", { doctype, name });
}

/* ── Cheque register (clearing-account flow) ─────────────────────────── */

export async function fetchCheques(status = "Pending", direction = "All", company = "", party = null) {
  const params = { status, direction, company };
  if (party) {
    params.party = party;
  }
  return frappeGet("ssplbilling.api.cheque_api.get_cheques", params);
}

export async function fetchChequeParties(status = "Pending", company = "") {
  return frappeGet("ssplbilling.api.cheque_api.get_cheque_parties", { status, company });
}

export async function createCheque(payload) {
  return frappePost("ssplbilling.api.cheque_api.create_cheque", {
    data: JSON.stringify(payload),
  });
}

export async function clearCheque(name, bankAccount, clearanceDate) {
  return frappePost("ssplbilling.api.cheque_api.clear_cheque", {
    name,
    bank_account: bankAccount,
    clearance_date: clearanceDate,
  });
}

export async function bounceCheque(name) {
  return frappePost("ssplbilling.api.cheque_api.bounce_cheque", { name });
}

export async function cancelCheque(name) {
  return frappePost("ssplbilling.api.cheque_api.cancel_cheque", { name });
}

export async function fetchChequeBankAccounts() {
  return frappeGet("ssplbilling.api.cheque_api.get_bank_accounts");
}

/* ── Stock Report Endpoints ─────────────────────────── */

export async function fetchStockReportFilters(company) {
  return frappeGet("ssplbilling.api.purchase_api.get_stock_report_filters", { company });
}

export async function fetchStockReportData(filters = {}) {
  return frappeGet("ssplbilling.api.purchase_api.get_stock_report_data", filters);
}

export async function getStockAgingReport(toDate, warehouse, company) {
  return frappeGet("ssplbilling.api.reports_api.get_stock_aging_report", {
    to_date: toDate,
    warehouse,
    company: company || localStorage.getItem("wb-company") || undefined,
  });
}

export async function getOutstandingCustomersReport(asOnDate, partyType = "Customer", company) {
  return frappeGet("ssplbilling.api.reports_api.get_outstanding_customers_report", {
    as_on_date: asOnDate,
    party_type: partyType,
    company: company || localStorage.getItem("wb-company") || undefined,
  });
}

export async function getLedgerWiseSalesPurchaseReport(fromDate, toDate) {
  return frappeGet("ssplbilling.api.reports_api.get_ledger_wise_sales_purchase_report", {
    from_date: fromDate,
    to_date: toDate,
    company: localStorage.getItem("wb-company") || undefined,
  });
}

export async function getMaterialTransferReport(fromDate, toDate, company) {
  return frappeGet("ssplbilling.api.reports_api.get_material_transfer_report", {
    from_date: fromDate,
    to_date: toDate,
    company: company || localStorage.getItem("wb-company") || undefined,
  });
}

// ─── Tab Session (license-enforced concurrent tab limit) ────────────────────

export async function registerTab(tabId) {
  return frappePost("ssplbilling.api.tab_session_api.register_tab", { tab_id: tabId });
}

export async function releaseTab(tabId) {
  return frappePost("ssplbilling.api.tab_session_api.release_tab", { tab_id: tabId });
}

/* ── Employee / HRMS ─────────────────────────── */

// status defaults to "" — frappeGet stringifies every param, so an undefined
// status would reach the server as the literal "undefined" and filter out every row
export async function fetchEmployees(status = "") {
  return frappeGet("ssplbilling.api.employee_api.get_employee_list", { status });
}

export async function createEmployee(payload) {
  return frappePost("ssplbilling.api.employee_api.create_employee", {
    data: JSON.stringify(payload),
  });
}

export async function getEmployeeDetails(employee) {
  return frappeGet("ssplbilling.api.employee_api.get_employee_details", { employee });
}

export async function updateEmployee(payload) {
  return frappePost("ssplbilling.api.employee_api.update_employee", {
    data: JSON.stringify(payload),
  });
}

export async function fetchLeaveTypes() {
  return frappeGet("ssplbilling.api.employee_api.get_leave_types");
}

export async function createLeaveApplication(payload) {
  return frappePost("ssplbilling.api.employee_api.create_leave_application", {
    data: JSON.stringify(payload),
  });
}

export async function fetchLeaveApprovers() {
  return frappeGet("ssplbilling.api.employee_api.get_leave_approvers");
}

/* ── eSSL attendance machines ────────────────── */

// No params by design: frappeGet stringifies every value, so an optional filter
// would arrive as the literal "undefined". Filtering happens client-side.
export async function fetchEsslMachines() {
  return frappeGet("ssplbilling.api.essl_machine_api.get_essl_machines");
}

export async function saveEsslMachine(payload) {
  return frappePost("ssplbilling.api.essl_machine_api.save_essl_machine", {
    data: JSON.stringify(payload),
  });
}

// Changing the IP renames the record, so the returned name may differ from the one sent.
export async function updateEsslMachine(payload) {
  return frappePost("ssplbilling.api.essl_machine_api.update_essl_machine", {
    data: JSON.stringify(payload),
  });
}

export async function deleteEsslMachine(name) {
  return frappePost("ssplbilling.api.essl_machine_api.delete_essl_machine", { name });
}

// Pulls logs off the devices themselves (ZK protocol, TCP 4370). Nothing is
// stored server-side — the caller caches the result. POST so the params travel
// as JSON instead of being stringified into a query string.
export async function syncEsslAttendance({ machine = null, fromDate = null } = {}) {
  return frappePost("ssplbilling.api.essl_machine_api.sync_essl_attendance", {
    machine,
    from_date: fromDate,
  });
}

/* ── Shift roaster (hrms Shift Assignment) ── */

export async function fetchShiftTypes() {
  return frappeGet("ssplbilling.api.shift_api.get_shift_types");
}

export async function saveShiftType(payload) {
  return frappePost("ssplbilling.api.shift_api.save_shift_type", payload);
}

export async function fetchShiftAssignments({
  employee = "",
  shiftType = "",
  fromDate = "",
  toDate = "",
} = {}) {
  return frappeGet("ssplbilling.api.shift_api.get_shift_assignments", {
    employee,
    shift_type: shiftType,
    from_date: fromDate,
    to_date: toDate,
  });
}

export async function saveShiftAssignment(payload) {
  return frappePost("ssplbilling.api.shift_api.save_shift_assignment", {
    data: JSON.stringify(payload),
  });
}

export async function cancelShiftAssignment(name) {
  return frappePost("ssplbilling.api.shift_api.cancel_shift_assignment", { name });
}

export async function deleteShiftAssignment(name) {
  return frappePost("ssplbilling.api.shift_api.delete_shift_assignment", { name });
}

// Serial number + clock read straight off the device. IP/comm key come from the
// form, so this also works for a machine that has not been saved yet.
export async function fetchEsslMachineInfo({ ipAddress, commKey = null } = {}) {
  return frappePost("ssplbilling.api.essl_machine_api.get_machine_info", {
    ip_address: ipAddress,
    comm_key: commKey,
  });
}

// timestamp must be local wall-clock "YYYY-MM-DD HH:MM:SS" — never toISOString(),
// which is UTC and would leave IST devices 5:30 off.
export async function setEsslMachineTime({ ipAddress, commKey = null, timestamp = null } = {}) {
  return frappePost("ssplbilling.api.essl_machine_api.set_machine_time", {
    ip_address: ipAddress,
    comm_key: commKey,
    timestamp,
  });
}

/* ── eSSL enrollment (device users, fingerprints) ── */

export async function fetchMachineUsers(machine) {
  return frappePost("ssplbilling.api.essl_enroll_api.get_machine_users", { machine });
}

// Machine to machine. Fingerprints travel with the user; face templates cannot.
export async function copyMachineUsers({ source, target, userIds = null }) {
  return frappePost("ssplbilling.api.essl_enroll_api.copy_users", {
    source,
    target,
    user_ids: JSON.stringify(userIds || []),
  });
}

export async function fetchNextEmployeeCode() {
  return frappeGet("ssplbilling.api.essl_enroll_api.next_employee_code");
}

export async function createEmployeeAndEnroll(payload) {
  return frappePost("ssplbilling.api.essl_enroll_api.create_employee_and_enroll", {
    data: JSON.stringify(payload),
  });
}

export async function deleteMachineUser({ machine, userId }) {
  return frappePost("ssplbilling.api.essl_enroll_api.delete_machine_user", {
    machine,
    user_id: userId,
  });
}

// Rewrites the user in place; the uid and code stay put so fingerprints survive.
export async function updateMachineUser({ machine, userId, name, privilege }) {
  return frappePost("ssplbilling.api.essl_enroll_api.update_machine_user", {
    machine,
    user_id: userId,
    name,
    privilege,
  });
}

/* ── eSSL employee mapping + attendance creation ── */

export async function fetchEsslMappings() {
  return frappeGet("ssplbilling.api.essl_attendance_api.get_mappings");
}

export async function saveEsslMapping(payload) {
  return frappePost("ssplbilling.api.essl_attendance_api.save_mapping", {
    data: JSON.stringify(payload),
  });
}

export async function deleteEsslMapping(name) {
  return frappePost("ssplbilling.api.essl_attendance_api.delete_mapping", { name });
}

export async function fetchEsslDeviceUsers(machine = null) {
  return frappePost("ssplbilling.api.essl_attendance_api.get_device_users", { machine });
}

export async function autoMapEsslUsers(machine = null) {
  return frappePost("ssplbilling.api.essl_attendance_api.auto_map_by_name", { machine });
}

// Creates Employee Checkin + Attendance documents. Idempotent — a punch already
// recorded is skipped, so calling it twice changes nothing the second time.
export async function syncEsslAttendanceToErp({ machine = null, fromDate = null } = {}) {
  return frappePost("ssplbilling.api.essl_attendance_api.sync_attendance", {
    machine,
    from_date: fromDate,
  });
}

export async function fetchAttendanceRecords({ fromDate = null, toDate = null, employee = null } = {}) {
  return frappePost("ssplbilling.api.essl_attendance_api.get_attendance_records", {
    from_date: fromDate,
    to_date: toDate,
    employee,
  });
}

// Counts per day or per employee, aggregated server-side for the bar chart.
export async function fetchAttendanceSummary({
  fromDate = null,
  toDate = null,
  groupBy = "date",
  employee = null,
} = {}) {
  return frappePost("ssplbilling.api.essl_attendance_api.get_attendance_summary", {
    from_date: fromDate,
    to_date: toDate,
    group_by: groupBy,
    employee,
  });
}

export async function createManualAttendance(payload) {
  return frappePost("ssplbilling.api.essl_attendance_api.create_manual_attendance", {
    data: JSON.stringify(payload),
  });
}

// A submitted Attendance is cancelled and replaced by an amendment server-side,
// so the returned name may differ from the one passed in.
export async function updateAttendance(payload) {
  return frappePost("ssplbilling.api.essl_attendance_api.update_attendance", {
    data: JSON.stringify(payload),
  });
}

export async function deleteAttendance(name) {
  return frappePost("ssplbilling.api.essl_attendance_api.delete_attendance", { name });
}

export async function fetchEsslSyncSettings() {
  return frappeGet("ssplbilling.api.essl_attendance_api.get_sync_settings");
}



