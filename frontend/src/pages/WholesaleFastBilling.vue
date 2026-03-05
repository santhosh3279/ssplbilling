<template>
  <div class="billing-root" @keydown="onGlobalKey">

    <!-- ══ TOP BAR ════════════════════════════════════════════════════════════ -->
    <header class="topbar">
      <div class="topbar-brand">
        <span class="brand-bolt">⚡</span>
        <span class="brand-text">FAST&nbsp;BILLING</span>
        <span class="brand-sep">·</span>
        <span class="brand-sub">Wholesale POS</span>
      </div>

      <div class="topbar-right">
        <span v-if="ui.lastInvoiceName" class="last-invoice-badge">
          ✓ {{ ui.lastInvoiceName }}
        </span>
        <div class="hotkey-chips">
          <span class="chip"><kbd>F9</kbd> Save</span>
          <span class="chip"><kbd>F2</kbd> New Row</span>
          <span class="chip"><kbd>Esc</kbd> Clear Row</span>
          <span class="chip"><kbd>Del</kbd> Remove Row</span>
        </div>
      </div>
    </header>

    <!-- ══ HEADER FIELDS ══════════════════════════════════════════════════════ -->
    <section class="header-bar">

      <!-- Date -->
      <div class="hf-group" :class="{ 'hf-error': ui.errors.billDate }">
        <label class="hf-label">BILL DATE</label>
        <input
          ref="dateRef"
          v-model="form.billDate"
          type="date"
          class="hf-input hf-date"
          @keydown.enter.prevent="focusField('customerInputRef')"
        />
        <span v-if="ui.errors.billDate" class="hf-err-msg">{{ ui.errors.billDate }}</span>
      </div>

      <!-- Customer -->
      <div class="hf-group hf-wide" :class="{ 'hf-error': ui.errors.customer }">
        <label class="hf-label">CUSTOMER <span class="req-star">*</span></label>
        <div class="autocomplete-wrap">
          <input
            ref="customerInputRef"
            v-model="customerQuery"
            type="text"
            class="hf-input"
            placeholder="Search customer…"
            autocomplete="off"
            spellcheck="false"
            @input="onCustomerQueryChange"
            @focus="customerDropdownOpen = customerOptions.length > 0"
            @blur="closeCustomerDropdown"
            @keydown.down.prevent="customerCursor = Math.min(customerCursor + 1, customerOptions.length - 1)"
            @keydown.up.prevent="customerCursor = Math.max(customerCursor - 1, 0)"
            @keydown.enter.prevent="pickCustomerByKey"
            @keydown.esc="closeCustomerDropdown"
          />
          <Transition name="dropdown-fade">
            <ul
              v-if="customerDropdownOpen && customerOptions.length"
              class="dropdown-list"
            >
              <li
                v-for="(c, idx) in customerOptions"
                :key="c.name"
                :class="{ 'dd-active': idx === customerCursor }"
                @mousedown.prevent="pickCustomer(c)"
              >
                <span class="dd-name">{{ c.customer_name }}</span>
                <span class="dd-code">{{ c.name }}</span>
              </li>
            </ul>
          </Transition>
        </div>
        <span v-if="ui.errors.customer" class="hf-err-msg">{{ ui.errors.customer }}</span>
      </div>

      <!-- Naming Series -->
      <div class="hf-group">
        <label class="hf-label">SERIES</label>
        <select
          ref="seriesRef"
          v-model="form.namingSeries"
          class="hf-input hf-select"
          @change="refreshInvoiceNo"
          @keydown.enter.prevent="focusFirstBarcode"
          :disabled="ui.loadingMeta"
        >
          <option v-for="s in namingSeriesOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <!-- Bill No (read-only) -->
      <div class="hf-group">
        <label class="hf-label">BILL NO</label>
        <input
          :value="form.invoiceNo"
          type="text"
          class="hf-input hf-readonly"
          readonly
          tabindex="-1"
        />
      </div>

      <!-- Payment Type -->
      <div class="hf-group">
        <label class="hf-label">PAYMENT MODE</label>
        <div class="pay-toggle">
          <button
            type="button"
            :class="['pay-btn', 'pay-cash', { active: form.paymentType === 'Cash' }]"
            @click="form.paymentType = 'Cash'"
          >
            <span class="pay-icon">💵</span>
            Cash
          </button>
          <button
            type="button"
            :class="['pay-btn', 'pay-credit', { active: form.paymentType === 'Credit' }]"
            @click="form.paymentType = 'Credit'"
          >
            <span class="pay-icon">📋</span>
            Credit
          </button>
        </div>
      </div>

    </section>

    <!-- ══ ITEM GRID ══════════════════════════════════════════════════════════ -->
    <section class="grid-section">
      <div class="grid-scroll" ref="gridScrollRef">
        <table class="billing-grid">
          <colgroup>
            <col style="width:38px" />      <!-- # -->
            <col style="width:130px" />     <!-- barcode -->
            <col style="width:120px" />     <!-- item code -->
            <col />                         <!-- item name (flex) -->
            <col style="width:110px" />     <!-- price -->
            <col style="width:90px" />      <!-- stock -->
            <col style="width:80px" />      <!-- qty -->
            <col style="width:80px" />      <!-- disc % -->
            <col style="width:110px" />     <!-- amount -->
            <col style="width:36px" />      <!-- del -->
          </colgroup>
          <thead>
            <tr>
              <th class="th-idx">#</th>
              <th>BARCODE</th>
              <th>ITEM CODE</th>
              <th>ITEM NAME</th>
              <th class="th-r">PRICE</th>
              <th class="th-r">STOCK</th>
              <th class="th-r">QTY</th>
              <th class="th-r">DISC %</th>
              <th class="th-r">AMOUNT</th>
              <th></th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="(row, idx) in rows"
              :key="row._uid"
              :class="{
                'row-active':   ui.activeRowIdx === idx,
                'row-loading':  row._loading,
                'row-filled':   !!row.itemCode,
              }"
              @click="ui.activeRowIdx = idx"
            >
              <!-- Index -->
              <td class="td-idx">{{ idx + 1 }}</td>

              <!-- Barcode -->
              <td class="td-barcode">
                <input
                  :ref="(el) => setBarcodeRef(el, idx)"
                  v-model="row.barcode"
                  type="text"
                  class="grid-cell barcode-cell"
                  placeholder="Scan / type…"
                  @focus="ui.activeRowIdx = idx"
                  @keydown.enter.prevent="() => onBarcodeEnterKey(idx)"
                  @keydown.tab.prevent="() => onBarcodeEnterKey(idx)"
                />
              </td>

              <!-- Item Code (read-only) -->
              <td class="td-code">
                <span class="cell-display code-display">{{ row.itemCode || '—' }}</span>
              </td>

              <!-- Item Name (read-only) -->
              <td class="td-name">
                <span class="cell-display name-display">
                  <span v-if="row._loading" class="loading-shimmer">Loading…</span>
                  <span v-else>{{ row.itemName }}</span>
                </span>
              </td>

              <!-- Price (read-only) -->
              <td class="td-r">
                <span class="cell-display">{{ fmtOrDash(row.rate) }}</span>
              </td>

              <!-- Stock -->
              <td class="td-r">
                <span
                  class="cell-display"
                  :class="{
                    'stock-ok':   row.stock !== null && row.stock > 10,
                    'stock-warn': row.stock !== null && row.stock > 0 && row.stock <= 10,
                    'stock-zero': row.stock !== null && row.stock <= 0,
                  }"
                >{{ row.stock !== null ? row.stock : '—' }}</span>
              </td>

              <!-- Qty -->
              <td class="td-r">
                <input
                  :ref="(el) => setQtyRef(el, idx)"
                  v-model.number="row.qty"
                  type="number"
                  min="0"
                  step="1"
                  class="grid-cell qty-cell"
                  placeholder="0"
                  @focus="($event.target.select(), ui.activeRowIdx = idx)"
                  @input="calcRow(idx)"
                  @keydown.enter.prevent="focusDisc(idx)"
                  @keydown.tab.prevent="focusDisc(idx)"
                  @keydown.esc.prevent="clearRow(idx)"
                />
              </td>

              <!-- Discount % -->
              <td class="td-r">
                <input
                  :ref="(el) => setDiscRef(el, idx)"
                  v-model.number="row.discount"
                  type="number"
                  min="0"
                  max="100"
                  step="0.5"
                  class="grid-cell disc-cell"
                  placeholder="0"
                  @focus="$event.target.select()"
                  @input="calcRow(idx)"
                  @keydown.enter.prevent="advanceFromDisc(idx)"
                  @keydown.tab.prevent="advanceFromDisc(idx)"
                  @keydown.esc.prevent="clearRow(idx)"
                />
              </td>

              <!-- Amount -->
              <td class="td-r td-amount">
                <span class="amount-val">{{ fmtOrDash(row.amount) }}</span>
              </td>

              <!-- Delete -->
              <td class="td-del">
                <button
                  class="del-btn"
                  type="button"
                  tabindex="-1"
                  title="Remove row"
                  @click.stop="removeRow(idx)"
                >✕</button>
              </td>
            </tr>

            <!-- Empty placeholder row -->
            <tr v-if="!rows.length" class="row-empty">
              <td colspan="10">
                Scan a barcode or press <kbd>F2</kbd> to add the first item
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Add Row button -->
      <div class="grid-footer">
        <button type="button" class="add-row-btn" @click="addRowAndFocus">
          <span>＋ Add Row</span>
          <kbd>F2</kbd>
        </button>
        <span v-if="ui.errors.items" class="items-err">{{ ui.errors.items }}</span>
      </div>
    </section>

    <!-- ══ TOTALS + ACTIONS ═══════════════════════════════════════════════════ -->
    <footer class="billing-footer">
      <div class="footer-left">
        <span class="row-count">
          {{ validRows.length }} item{{ validRows.length !== 1 ? 's' : '' }}
        </span>
        <button type="button" class="btn-clear" @click="onClear" :disabled="ui.saving">
          🗑 Clear Bill
        </button>
      </div>

      <div class="totals-block">
        <div class="total-row">
          <span class="total-lbl">Subtotal</span>
          <span class="total-val">{{ fmtCurrency(subtotal) }}</span>
        </div>
        <div class="total-row discount-row">
          <span class="total-lbl">Discount</span>
          <span class="total-val disc-val">− {{ fmtCurrency(totalDiscount) }}</span>
        </div>
        <div class="total-row grand-total-row">
          <span class="total-lbl grand-lbl">GRAND TOTAL</span>
          <span class="total-val grand-val">{{ fmtCurrency(grandTotal) }}</span>
        </div>
      </div>

      <div class="footer-right">
        <div class="payment-display">
          <span class="pd-label">Mode:</span>
          <span :class="['pd-val', form.paymentType === 'Cash' ? 'pd-cash' : 'pd-credit']">
            {{ form.paymentType === 'Cash' ? '💵 Cash' : '📋 Credit' }}
          </span>
        </div>
        <button
          type="button"
          class="btn-save"
          :class="{ 'saving': ui.saving }"
          :disabled="ui.saving"
          @click="saveBill"
        >
          <span v-if="ui.saving" class="save-spinner">⟳</span>
          <span v-else>⚡ Save Bill</span>
          <kbd>F9</kbd>
        </button>
      </div>
    </footer>

    <!-- ══ ITEM SEARCH MODAL ══════════════════════════════════════════════════ -->
    <ItemSearchModal
      v-model="modalOpen"
      :price-list="DEFAULT_PRICE_LIST"
      @selected="onModalItemSelected"
    />

    <!-- ══ TOAST STACK ════════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div class="toast-stack">
        <TransitionGroup name="toast-anim" tag="div">
          <div
            v-for="t in toasts"
            :key="t.id"
            :class="['toast', `toast-${t.type}`]"
            @click="dismissToast(t.id)"
          >
            <span class="toast-icon">{{ t.type === 'success' ? '✓' : t.type === 'error' ? '✕' : 'ℹ' }}</span>
            <span class="toast-msg">{{ t.message }}</span>
          </div>
        </TransitionGroup>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from "vue";
import ItemSearchModal from "../components/ItemSearchModal.vue";
import { useBilling } from "../composables/useBilling.js";

// ─── Constants ────────────────────────────────────────────────────────────────
const DEFAULT_PRICE_LIST = "Standard Selling";

// ─── Composable ───────────────────────────────────────────────────────────────
const {
  form,
  rows,
  ui,
  toasts,
  namingSeriesOptions,
  customerOptions,
  customerQuery,
  customerDropdownOpen,
  modalOpen,
  validRows,
  subtotal,
  totalDiscount,
  grandTotal,
  init,
  refreshInvoiceNo,
  onCustomerQueryChange,
  pickCustomer,
  clearCustomer,
  handleBarcodeEnter,
  onModalItemSelected: composableOnModalItemSelected,
  calcRow,
  addRow,
  removeRow,
  clearRow,
  saveBill,
  resetForm,
  dismissToast,
  pushToast,
} = useBilling();

// ─── Template refs ────────────────────────────────────────────────────────────
const dateRef         = ref(null);
const customerInputRef = ref(null);
const seriesRef       = ref(null);
const gridScrollRef   = ref(null);

// Keyed maps for dynamic grid cells
const barcodeRefs = new Map();
const qtyRefs     = new Map();
const discRefs    = new Map();

function setBarcodeRef(el, idx) { el ? barcodeRefs.set(idx, el) : barcodeRefs.delete(idx); }
function setQtyRef(el, idx)     { el ? qtyRefs.set(idx, el)     : qtyRefs.delete(idx); }
function setDiscRef(el, idx)    { el ? discRefs.set(idx, el)    : discRefs.delete(idx); }

// ─── Customer dropdown ────────────────────────────────────────────────────────
const customerCursor = ref(0);

function closeCustomerDropdown() {
  setTimeout(() => { customerDropdownOpen.value = false; }, 150);
}

function pickCustomerByKey() {
  const opt = customerOptions.value[customerCursor.value];
  if (opt) pickCustomer(opt);
  else if (customerOptions.value.length) pickCustomer(customerOptions.value[0]);
}

// ─── Focus helpers ────────────────────────────────────────────────────────────
const namedRefs = { dateRef, customerInputRef, seriesRef };

function focusField(name) {
  nextTick(() => namedRefs[name]?.value?.focus());
}

function focusFirstBarcode() {
  nextTick(() => barcodeRefs.get(0)?.focus());
}

function focusBarcode(idx) {
  nextTick(() => barcodeRefs.get(idx)?.focus());
}

function focusQty(idx) {
  nextTick(() => {
    const el = qtyRefs.get(idx);
    if (el) { el.focus(); el.select(); }
  });
}

function focusDisc(idx) {
  nextTick(() => {
    const el = discRefs.get(idx);
    if (el) { el.focus(); el.select(); }
  });
}

// ─── Barcode Enter handler ────────────────────────────────────────────────────
async function onBarcodeEnterKey(idx) {
  const action = await handleBarcodeEnter(idx);
  if (action === "focus-qty") {
    focusQty(idx);
  }
  // "open-modal" — modal will open via modalOpen reactive state
  // component watches modalOpen and handles focus internally
}

// ─── Advance from discount to next barcode ────────────────────────────────────
function advanceFromDisc(idx) {
  if (idx === rows.value.length - 1) {
    addRowAndFocus();
  } else {
    focusBarcode(idx + 1);
  }
}

// ─── Add row and focus its barcode ────────────────────────────────────────────
function addRowAndFocus() {
  const newIdx = addRow();
  nextTick(() => {
    focusBarcode(newIdx);
    // Scroll new row into view
    gridScrollRef.value?.scrollTo({
      top: gridScrollRef.value.scrollHeight,
      behavior: "smooth",
    });
  });
}

// ─── Modal selection ──────────────────────────────────────────────────────────
async function onModalItemSelected(item) {
  const idx = await composableOnModalItemSelected(item);
  if (idx !== null && idx !== undefined) {
    focusQty(idx);
  }
}

// ─── Clear bill ───────────────────────────────────────────────────────────────
function onClear() {
  const hasItems = validRows.value.length > 0;
  if (hasItems && !confirm("Clear the current bill and start over?")) return;
  resetForm();
  nextTick(() => dateRef.value?.focus());
}

// ─── Global keyboard shortcuts ────────────────────────────────────────────────
function onGlobalKey(e) {
  // F9 → Save
  if (e.key === "F9") {
    e.preventDefault();
    saveBill();
    return;
  }
  // F2 → Add row
  if (e.key === "F2") {
    e.preventDefault();
    addRowAndFocus();
    return;
  }
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  await init();
  nextTick(() => dateRef.value?.focus());
});

// ─── Formatting helpers ───────────────────────────────────────────────────────
function fmtOrDash(val) {
  if (val === null || val === undefined || val === "") return "—";
  return Number(val).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function fmtCurrency(val) {
  return Number(val || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
</script>

<style>
/* ── Global resets & font imports ─────────────────────────────────────────── */
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Barlow+Condensed:wght@400;500;600;700;800&display=swap");

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app { height: 100%; overflow: hidden; }

:root {
  /* Core palette */
  --bg-root:     #060810;
  --bg-surface:  #0b0e19;
  --bg-surface2: #0f1320;
  --bg-surface3: #131828;
  --bg-row-hover:#0e1628;
  --bg-row-active: rgba(56, 130, 246, 0.05);

  /* Borders */
  --border:     #161c2e;
  --border2:    #1e2840;
  --border-focus: #3b82f6;

  /* Text */
  --text:       #d4dff0;
  --text2:      #6a85aa;
  --text3:      #2d4060;
  --text-dim:   #1a2840;

  /* Accent */
  --accent:     #3b82f6;
  --accent-glow: rgba(59, 130, 246, 0.15);
  --accent-dim:  rgba(59, 130, 246, 0.08);

  /* Semantic */
  --green:  #10b981;
  --yellow: #f59e0b;
  --red:    #ef4444;
  --green-dim:  rgba(16, 185, 129, 0.12);
  --yellow-dim: rgba(245, 158, 11, 0.10);
  --red-dim:    rgba(239, 68, 68, 0.10);

  /* Fonts */
  --font-mono: "JetBrains Mono", "Consolas", monospace;
  --font-disp: "Barlow Condensed", sans-serif;

  /* Sizing */
  --topbar-h:   44px;
  --headerbar-h: 64px;
  --footer-h:   68px;
}

input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { opacity: 0.3; }
input[type="date"]::-webkit-calendar-picker-indicator { filter: invert(0.5); cursor: pointer; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1a2538; border-radius: 3px; }
</style>

<style scoped>
/* ── Root layout ──────────────────────────────────────────────────────────── */
.billing-root {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-root);
  color: var(--text);
  font-family: var(--font-mono);
  overflow: hidden;
}

/* ── Top Bar ──────────────────────────────────────────────────────────────── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--topbar-h);
  padding: 0 18px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  gap: 16px;
}

.topbar-brand {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.brand-bolt {
  font-size: 16px;
  color: var(--accent);
  filter: drop-shadow(0 0 6px var(--accent));
}

.brand-text {
  font-family: var(--font-disp);
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 0.1em;
  color: var(--accent);
  text-transform: uppercase;
}

.brand-sep {
  color: var(--border2);
  font-size: 14px;
}

.brand-sub {
  font-size: 11px;
  color: var(--text3);
  letter-spacing: 0.06em;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.last-invoice-badge {
  font-size: 12px;
  color: var(--green);
  font-weight: 600;
  background: var(--green-dim);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: 20px;
  padding: 2px 10px;
}

.hotkey-chips {
  display: flex;
  gap: 8px;
}

.chip {
  font-size: 11px;
  color: var(--text3);
  display: flex;
  align-items: center;
  gap: 4px;
}

.chip kbd {
  background: var(--bg-surface3);
  border: 1px solid var(--border2);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text2);
}

/* ── Header Bar (form fields) ─────────────────────────────────────────────── */
.header-bar {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 10px 18px;
  background: var(--bg-surface);
  border-bottom: 2px solid var(--border);
  flex-shrink: 0;
  flex-wrap: wrap;
  min-height: var(--headerbar-h);
}

.hf-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
}

.hf-wide { flex: 2; min-width: 200px; }

.hf-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text3);
}

.req-star { color: var(--red); margin-left: 1px; }

.hf-input {
  background: var(--bg-surface2);
  border: 1px solid var(--border2);
  border-radius: 7px;
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 13px;
  padding: 7px 11px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  min-width: 120px;
}

.hf-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.hf-date { width: 154px; color-scheme: dark; }
.hf-select { cursor: pointer; width: 160px; }
.hf-readonly {
  cursor: default;
  color: var(--text3);
  background: var(--bg-root);
  border-color: var(--border);
  width: 140px;
}

.hf-error .hf-input { border-color: var(--red); }
.hf-err-msg {
  font-size: 10px;
  color: var(--red);
  position: absolute;
  bottom: -15px;
  left: 0;
  white-space: nowrap;
}

/* Customer autocomplete */
.autocomplete-wrap { position: relative; }

.dropdown-list {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--bg-surface2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  list-style: none;
  z-index: 200;
  overflow: hidden;
  max-height: 220px;
  overflow-y: auto;
  box-shadow: 0 12px 40px rgba(0,0,0,0.5);
}

.dropdown-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  cursor: pointer;
  gap: 12px;
  transition: background 0.1s;
}

.dropdown-list li:hover,
.dropdown-list li.dd-active {
  background: var(--bg-surface3);
}

.dd-name { font-size: 13px; color: var(--text); }
.dd-code { font-size: 11px; color: var(--text3); }

/* Payment toggle */
.pay-toggle { display: flex; gap: 5px; }

.pay-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-surface2);
  border: 1px solid var(--border2);
  border-radius: 7px;
  color: var(--text3);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  padding: 7px 13px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.pay-btn:hover { color: var(--text2); }

.pay-btn.active.pay-cash {
  background: var(--green-dim);
  border-color: rgba(16,185,129,0.35);
  color: var(--green);
}

.pay-btn.active.pay-credit {
  background: var(--yellow-dim);
  border-color: rgba(245,158,11,0.35);
  color: var(--yellow);
}

.pay-icon { font-size: 14px; }

/* ── Grid Section ─────────────────────────────────────────────────────────── */
.grid-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.grid-scroll {
  flex: 1;
  overflow: auto;
}

.billing-grid {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

/* Header */
.billing-grid thead tr {
  background: var(--bg-surface);
  position: sticky;
  top: 0;
  z-index: 10;
}

.billing-grid th {
  padding: 9px 10px;
  font-family: var(--font-disp);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text3);
  border-bottom: 2px solid var(--border2);
  text-align: left;
  white-space: nowrap;
  user-select: none;
}

.th-idx { width: 38px; text-align: center; }
.th-r { text-align: right; }

/* Body rows */
.billing-grid tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background 0.08s;
}

.billing-grid tbody tr:hover       { background: var(--bg-row-hover); }
.billing-grid tbody tr.row-active  { background: var(--bg-row-active); }
.billing-grid tbody tr.row-loading { opacity: 0.6; }

.billing-grid tbody tr.row-filled td.td-code .code-display {
  color: #4a9eff;
}

/* Body cells */
.billing-grid td {
  padding: 3px 6px;
  vertical-align: middle;
}

.td-idx {
  font-size: 11px;
  color: var(--text3);
  text-align: center;
  padding: 0;
}

.td-r { text-align: right; }

.cell-display {
  display: block;
  font-size: 13px;
  padding: 5px 6px;
  color: var(--text2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.code-display { color: var(--accent); font-weight: 600; }
.name-display { color: var(--text2); }

/* Stock status colours */
.stock-ok   { color: var(--green) !important; }
.stock-warn { color: var(--yellow) !important; }
.stock-zero { color: var(--red) !important; }

.td-amount { }
.amount-val {
  display: block;
  font-size: 13px;
  font-weight: 600;
  text-align: right;
  padding: 5px 8px 5px 6px;
  color: var(--green);
}

/* Grid inputs */
.grid-cell {
  width: 100%;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 13px;
  padding: 5px 7px;
  outline: none;
  transition: border-color 0.1s, background 0.1s;
}

.grid-cell:focus {
  background: var(--bg-surface2);
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-glow);
}

.barcode-cell { font-size: 12px; }
.qty-cell, .disc-cell { text-align: right; }

/* Delete button */
.td-del { padding: 0 4px; }
.del-btn {
  background: none;
  border: none;
  color: transparent;
  font-size: 11px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  transition: color 0.1s, background 0.1s;
  display: block;
}
tr:hover .del-btn   { color: var(--text3); }
.del-btn:hover      { color: var(--red) !important; background: var(--red-dim); }

/* Empty row */
.row-empty td {
  text-align: center;
  padding: 48px 20px;
  font-size: 13px;
  color: var(--text3);
}
.row-empty td kbd {
  background: var(--bg-surface3);
  border: 1px solid var(--border2);
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 12px;
  color: var(--text2);
}

/* Loading shimmer */
.loading-shimmer {
  color: var(--text3);
  font-style: italic;
  font-size: 12px;
  animation: shimmer-blink 1s step-end infinite;
}
@keyframes shimmer-blink { 50% { opacity: 0.3; } }

/* ── Grid footer (add row) ────────────────────────────────────────────────── */
.grid-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  border-top: 1px solid var(--border);
  background: var(--bg-surface);
  flex-shrink: 0;
}

.add-row-btn {
  display: flex;
  align-items: center;
  gap: 7px;
  background: var(--accent-dim);
  border: 1px dashed var(--border-focus);
  border-radius: 7px;
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 6px 14px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.add-row-btn:hover {
  background: var(--accent-glow);
  border-style: solid;
}
.add-row-btn kbd {
  background: rgba(59,130,246,0.15);
  border: 1px solid rgba(59,130,246,0.3);
  border-radius: 3px;
  padding: 1px 6px;
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--accent);
}

.items-err {
  font-size: 11px;
  color: var(--red);
}

/* ── Billing Footer ───────────────────────────────────────────────────────── */
.billing-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--footer-h);
  padding: 0 20px;
  background: var(--bg-surface);
  border-top: 2px solid var(--border2);
  flex-shrink: 0;
  gap: 20px;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.row-count {
  font-size: 12px;
  color: var(--text3);
  white-space: nowrap;
}

.btn-clear {
  background: none;
  border: 1px solid var(--border2);
  border-radius: 7px;
  color: var(--text3);
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-clear:hover { color: var(--red); border-color: rgba(239,68,68,0.3); background: var(--red-dim); }
.btn-clear:disabled { opacity: 0.4; cursor: not-allowed; }

/* Totals block */
.totals-block {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 240px;
}

.total-row {
  display: flex;
  justify-content: space-between;
  gap: 24px;
}

.total-lbl {
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.total-val {
  font-size: 13px;
  color: var(--text2);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.disc-val  { color: var(--yellow); }

.grand-total-row {
  border-top: 1px solid var(--border2);
  padding-top: 4px;
  margin-top: 2px;
}

.grand-lbl { color: var(--text); font-weight: 700; font-size: 12px; letter-spacing: 0.1em; }
.grand-val { color: var(--green); font-size: 18px; font-weight: 700; letter-spacing: 0.04em; }

/* Footer right */
.footer-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.payment-display {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}
.pd-label { color: var(--text3); }
.pd-val { font-weight: 600; font-size: 13px; }
.pd-cash { color: var(--green); }
.pd-credit { color: var(--yellow); }

.btn-save {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--accent);
  border: none;
  border-radius: 9px;
  color: #fff;
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  padding: 10px 22px;
  cursor: pointer;
  letter-spacing: 0.04em;
  transition: background 0.15s, transform 0.1s, box-shadow 0.15s;
  box-shadow: 0 0 20px rgba(59,130,246,0.25);
}

.btn-save:hover:not(:disabled) {
  background: #2563eb;
  box-shadow: 0 0 30px rgba(59,130,246,0.4);
  transform: translateY(-1px);
}

.btn-save:active:not(:disabled) { transform: translateY(0); }

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-save.saving { background: #1d4ed8; }

.btn-save kbd {
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: rgba(255,255,255,0.8);
}

.save-spinner { animation: spin 0.8s linear infinite; font-size: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Dropdown transition ──────────────────────────────────────────────────── */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active { transition: opacity 0.12s, transform 0.12s; }
.dropdown-fade-enter-from,
.dropdown-fade-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Toast stack ──────────────────────────────────────────────────────────── */
.toast-stack {
  position: fixed;
  bottom: 90px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 16px;
  border-radius: 9px;
  font-family: var(--font-mono);
  font-size: 13px;
  cursor: pointer;
  pointer-events: all;
  min-width: 240px;
  max-width: 400px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.4);
  border: 1px solid transparent;
}

.toast-success {
  background: #081c14;
  border-color: rgba(16,185,129,0.3);
  color: var(--green);
}

.toast-error {
  background: #1a0808;
  border-color: rgba(239,68,68,0.3);
  color: #ff6b6b;
}

.toast-info {
  background: var(--bg-surface2);
  border-color: var(--border2);
  color: var(--text2);
}

.toast-icon { font-size: 14px; flex-shrink: 0; }
.toast-msg  { flex: 1; line-height: 1.4; }

.toast-anim-enter-active { transition: all 0.2s cubic-bezier(0.34,1.56,0.64,1); }
.toast-anim-leave-active { transition: all 0.15s ease; }
.toast-anim-enter-from   { opacity: 0; transform: translateX(30px) scale(0.9); }
.toast-anim-leave-to     { opacity: 0; transform: translateX(30px); }
.toast-anim-move         { transition: transform 0.2s ease; }
</style>
