/**
 * composables/useBilling.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Core state management for the WholesaleFastBilling screen.
 *
 * STATE ARCHITECTURE
 * ──────────────────
 *  form          – header fields (date, customer, series, payment)
 *  rows          – line items array (reactive)
 *  ui            – loading flags, active row, error messages
 *  toasts        – ephemeral notification queue
 *
 * All API side-effects live here; components only call composable methods.
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { ref, computed, nextTick } from "vue";
import {
  fetchNamingSeries,
  previewNextInvoiceNo,
  resolveBarcode,
  fetchItemDetails,
  searchItems as apiSearchItems,
  createSalesInvoice,
} from "../api.js";
import { searchCustomers } from "../customersearch.js";

// ─── Row factory ──────────────────────────────────────────────────────────────

let _uid = 0;
function makeRow(overrides = {}) {
  return {
    _uid: ++_uid,
    barcode: "",
    itemCode: "",
    itemName: "",
    rate: null,
    stock: null,
    qty: null,
    discount: null,
    amount: null,
    _loading: false,
    ...overrides,
  };
}

// ─── Composable ───────────────────────────────────────────────────────────────

export function useBilling() {
  // ── Header form state ────────────────────────────────────────────────────
  const form = ref({
    billDate: todayISO(),
    customer: "",
    customerName: "",    // display label
    namingSeries: "",
    invoiceNo: "—",
    paymentType: "Cash",
  });

  // ── Rows ─────────────────────────────────────────────────────────────────
  const rows = ref([makeRow()]);

  // ── UI state ─────────────────────────────────────────────────────────────
  const ui = ref({
    activeRowIdx: 0,
    saving: false,
    loadingMeta: true,
    errors: {},          // fieldname → message
    lastInvoiceName: "",
  });

  // ── Dropdowns / search ───────────────────────────────────────────────────
  const namingSeriesOptions = ref([]);
  const customerOptions = ref([]);
  const customerQuery = ref("");
  const customerDropdownOpen = ref(false);

  // ── Toasts ───────────────────────────────────────────────────────────────
  const toasts = ref([]);

  // ── Modal state ──────────────────────────────────────────────────────────
  const modalOpen = ref(false);
  const modalTargetIdx = ref(null);

  // ─── Computed ─────────────────────────────────────────────────────────────

  const validRows = computed(() =>
    rows.value.filter((r) => r.itemCode && Number(r.qty) > 0)
  );

  const subtotal = computed(() =>
    rows.value.reduce((s, r) => s + Number(r.qty || 0) * Number(r.rate || 0), 0)
  );

  const totalDiscount = computed(() =>
    rows.value.reduce((s, r) => {
      const base = Number(r.qty || 0) * Number(r.rate || 0);
      return s + base * (Number(r.discount || 0) / 100);
    }, 0)
  );

  const grandTotal = computed(() => subtotal.value - totalDiscount.value);

  // ─── Initialisation ────────────────────────────────────────────────────────

  async function init() {
    ui.value.loadingMeta = true;
    try {
      namingSeriesOptions.value = await fetchNamingSeries();
      if (namingSeriesOptions.value.length) {
        form.value.namingSeries = namingSeriesOptions.value[0];
        await refreshInvoiceNo();
      }
    } catch (e) {
      pushToast("Could not load invoice settings: " + e.message, "error");
    } finally {
      ui.value.loadingMeta = false;
    }
  }

  // ─── Naming Series ─────────────────────────────────────────────────────────

  async function refreshInvoiceNo() {
    if (!form.value.namingSeries) return;
    form.value.invoiceNo = "…";
    form.value.invoiceNo = await previewNextInvoiceNo(form.value.namingSeries);
  }

  // ─── Customer ──────────────────────────────────────────────────────────────

  let _custDebounce = null;

  async function onCustomerQueryChange() {
    clearTimeout(_custDebounce);
    if (!customerQuery.value.trim()) {
      customerOptions.value = [];
      return;
    }
    _custDebounce = setTimeout(async () => {
      try {
        customerOptions.value = await searchCustomers(customerQuery.value);
        customerDropdownOpen.value = true;
      } catch (e) {
        console.warn("[useBilling] customer search error:", e.message);
      }
    }, 220);
  }

  function pickCustomer(c) {
    form.value.customer = c.name;
    form.value.customerName = c.customer_name;
    customerQuery.value = c.customer_name;
    customerOptions.value = [];
    customerDropdownOpen.value = false;
    clearError("customer");
  }

  function clearCustomer() {
    form.value.customer = "";
    form.value.customerName = "";
    customerQuery.value = "";
  }

  // ─── Row: barcode scan / Enter ─────────────────────────────────────────────

  async function handleBarcodeEnter(idx) {
    const row = rows.value[idx];
    const raw = row.barcode.trim();
    if (!raw) return;

    row._loading = true;
    try {
      const itemCode = await resolveBarcode(raw);
      if (itemCode) {
        await populateRow(idx, itemCode);
        // Focus will be moved by component via ref
        return "focus-qty";
      } else {
        // Open search modal
        modalTargetIdx.value = idx;
        modalOpen.value = true;
        return "open-modal";
      }
    } catch (e) {
      pushToast("Barcode lookup failed: " + e.message, "error");
      return "error";
    } finally {
      row._loading = false;
    }
  }

  /**
   * Fill a row with item details (price + stock).
   */
  async function populateRow(idx, itemCode, itemName = "") {
    const row = rows.value[idx];
    row.itemCode = itemCode;
    row.itemName = itemName || itemCode;
    row._loading = true;
    try {
      const { price, stock } = await fetchItemDetails(itemCode);
      row.rate = price;
      row.stock = stock;
      row.qty = row.qty ?? 1;
      calcRow(idx);
    } finally {
      row._loading = false;
    }
  }

  /** Called when user selects an item from the search modal */
  async function onModalItemSelected(item) {
    const idx = modalTargetIdx.value;
    if (idx === null) return;
    rows.value[idx].barcode = item.item_code;
    await populateRow(idx, item.item_code, item.item_name);
    modalOpen.value = false;
    return idx; // component will focus qty
  }

  // ─── Row calculations ──────────────────────────────────────────────────────

  function calcRow(idx) {
    const r = rows.value[idx];
    const base = Number(r.qty || 0) * Number(r.rate || 0);
    const disc = base * (Number(r.discount || 0) / 100);
    r.amount = parseFloat((base - disc).toFixed(2));
  }

  // ─── Row management ────────────────────────────────────────────────────────

  function addRow() {
    rows.value.push(makeRow());
    return rows.value.length - 1; // return new idx for focusing
  }

  function removeRow(idx) {
    if (rows.value.length === 1) {
      rows.value[0] = makeRow();
    } else {
      rows.value.splice(idx, 1);
    }
  }

  function clearRow(idx) {
    const uid = rows.value[idx]._uid;
    rows.value[idx] = { ...makeRow(), _uid: uid };
  }

  // ─── Validation ────────────────────────────────────────────────────────────

  function validate() {
    const errors = {};

    if (!form.value.customer) {
      errors.customer = "Customer is required";
    }
    if (!form.value.billDate) {
      errors.billDate = "Date is required";
    }
    if (validRows.value.length === 0) {
      errors.items = "Add at least one item with qty > 0";
    }

    ui.value.errors = errors;
    return Object.keys(errors).length === 0;
  }

  function clearError(field) {
    delete ui.value.errors[field];
  }

  // ─── Save ──────────────────────────────────────────────────────────────────

  async function saveBill() {
    if (ui.value.saving) return;
    if (!validate()) {
      if (ui.value.errors.customer) {
        pushToast("Please select a customer", "error");
      } else if (ui.value.errors.items) {
        pushToast("Add at least one item with quantity > 0", "error");
      }
      return;
    }

    ui.value.saving = true;
    try {
      const doc = await createSalesInvoice({
        customer: form.value.customer,
        postingDate: form.value.billDate,
        namingSeries: form.value.namingSeries,
        paymentType: form.value.paymentType,
        grandTotal: grandTotal.value,
        items: validRows.value,
      });

      ui.value.lastInvoiceName = doc.name;
      pushToast(`✓ Invoice ${doc.name} saved successfully`, "success");
      resetForm();
      return doc.name;
    } catch (e) {
      pushToast("Save failed: " + e.message, "error");
      console.error("[useBilling] save error:", e);
    } finally {
      ui.value.saving = false;
    }
  }

  // ─── Reset ─────────────────────────────────────────────────────────────────

  function resetForm() {
    form.value.billDate = todayISO();
    form.value.customer = "";
    form.value.customerName = "";
    customerQuery.value = "";
    form.value.paymentType = "Cash";
    rows.value = [makeRow()];
    ui.value.errors = {};
    ui.value.activeRowIdx = 0;
    refreshInvoiceNo();
  }

  // ─── Toasts ────────────────────────────────────────────────────────────────

  function pushToast(message, type = "info") {
    const id = Date.now() + Math.random();
    toasts.value.push({ id, message, type });
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id);
    }, type === "error" ? 6000 : 4000);
  }

  function dismissToast(id) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  // ─── Item search (for modal) ────────────────────────────────────────────────

  async function searchItemsModal(query) {
    return apiSearchItems(query);
  }

  // ─── Helpers ───────────────────────────────────────────────────────────────

  return {
    // State
    form,
    rows,
    ui,
    toasts,
    namingSeriesOptions,
    customerOptions,
    customerQuery,
    customerDropdownOpen,
    modalOpen,
    modalTargetIdx,

    // Computed
    validRows,
    subtotal,
    totalDiscount,
    grandTotal,

    // Methods
    init,
    refreshInvoiceNo,
    onCustomerQueryChange,
    pickCustomer,
    clearCustomer,
    handleBarcodeEnter,
    populateRow,
    onModalItemSelected,
    calcRow,
    addRow,
    removeRow,
    clearRow,
    saveBill,
    resetForm,
    pushToast,
    dismissToast,
    searchItemsModal,
    clearError,
    makeRow,
  };
}

// ─── Utility ──────────────────────────────────────────────────────────────────

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}
