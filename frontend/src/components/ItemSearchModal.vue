<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="modelValue"
        class="modal-overlay"
        @mousedown.self="close"
        @keydown.esc="close"
      >
        <div
          class="modal-box"
          role="dialog"
          aria-modal="true"
          aria-label="Search and select item"
        >
          <!-- ── Header ── -->
          <div class="modal-head">
            <div class="modal-head-left">
              <span class="modal-icon">⊞</span>
              <span class="modal-title">Item Search</span>
            </div>
            <button class="modal-close" @click="close" tabindex="-1">
              ✕
            </button>
          </div>

          <!-- ── Search input ── -->
          <div class="modal-search-row">
            <div class="search-field-wrap">
              <span class="search-prefix">⌕</span>
              <input
                ref="searchInputRef"
                v-model="query"
                class="search-field"
                type="text"
                placeholder="Type item code or name…"
                autocomplete="off"
                spellcheck="false"
                @input="onQueryChange"
                @keydown.esc.prevent="close"
                @keydown.enter.prevent="confirmFocused"
                @keydown.down.prevent="moveCursor(1)"
                @keydown.up.prevent="moveCursor(-1)"
              />
              <span v-if="loading" class="search-spinner" aria-label="Searching">⟳</span>
            </div>
            <span class="search-hint">{{ results.length }} result{{ results.length !== 1 ? "s" : "" }}</span>
          </div>

          <!-- ── Results table ── -->
          <div class="modal-results-wrap" ref="resultsWrapRef">
            <table v-if="results.length" class="results-table" role="grid">
              <thead>
                <tr>
                  <th>Item Code</th>
                  <th class="col-name">Item Name</th>
                  <th class="col-num">Price</th>
                  <th class="col-num">Stock</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(item, idx) in results"
                  :key="item.item_code"
                  :ref="el => setRowRef(el, idx)"
                  :class="{ highlighted: idx === cursor }"
                  @click="selectItem(item)"
                  @mouseenter="cursor = idx"
                  role="row"
                  :aria-selected="idx === cursor"
                  tabindex="-1"
                >
                  <td class="td-code">{{ item.item_code }}</td>
                  <td class="td-name">{{ item.item_name }}</td>
                  <td class="td-num">
                    <span v-if="item._loading" class="loading-dot">…</span>
                    <span v-else>{{ fmtPrice(item.price) }}</span>
                  </td>
                  <td
                    class="td-num"
                    :class="{ 'stock-low': !item._loading && item.stock <= 0 }"
                  >
                    <span v-if="item._loading" class="loading-dot">…</span>
                    <span v-else>{{ item.stock }}</span>
                  </td>
                </tr>
              </tbody>
            </table>

            <div v-else class="modal-empty">
              <template v-if="loading">
                <span class="empty-spinner">⟳</span>
                <span>Searching…</span>
              </template>
              <template v-else>
                <span class="empty-icon">∅</span>
                <span>No items found{{ query ? ' for ' : '' }}<strong v-if="query">"{{ query }}"</strong></span>
              </template>
            </div>
          </div>

          <!-- ── Footer shortcuts ── -->
          <div class="modal-footer">
            <span class="kbd-hint"><kbd>↑↓</kbd> Navigate</span>
            <span class="kbd-hint"><kbd>↵</kbd> Select</span>
            <span class="kbd-hint"><kbd>Esc</kbd> Close</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from "vue";
import { searchItems, fetchItemDetails } from "../api.js";

// ─── Props / emits ────────────────────────────────────────────────────────────

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  priceList:  { type: String, default: "Standard Selling" },
});

const emit = defineEmits(["update:modelValue", "selected"]);

// ─── State ────────────────────────────────────────────────────────────────────

const query         = ref("");
const results       = ref([]);
const cursor        = ref(0);
const loading       = ref(false);
const searchInputRef  = ref(null);
const resultsWrapRef  = ref(null);
const rowRefs         = new Map();

let _debounce = null;

// ─── Ref management ───────────────────────────────────────────────────────────

function setRowRef(el, idx) {
  if (el) rowRefs.set(idx, el);
  else rowRefs.delete(idx);
}

// ─── Watch open/close ─────────────────────────────────────────────────────────

watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      query.value = "";
      results.value = [];
      cursor.value = 0;
      await nextTick();
      searchInputRef.value?.focus();
      runSearch();
    } else {
      clearTimeout(_debounce);
    }
  }
);

// ─── Search logic ─────────────────────────────────────────────────────────────

function onQueryChange() {
  clearTimeout(_debounce);
  _debounce = setTimeout(runSearch, 250);
}

async function runSearch() {
  loading.value = true;
  try {
    let items;
    if (!query.value.trim()) {
      // Empty query: fetch all active sales items
      const qs = new URLSearchParams({
        doctype: "Item",
        fields: JSON.stringify(["item_code", "item_name"]),
        filters: JSON.stringify([["disabled", "=", 0], ["is_sales_item", "=", 1]]),
        limit_page_length: 200,
        order_by: "item_name asc",
      });
      const res = await fetch(`/api/method/frappe.client.get_list?${qs}`, {
        headers: { "X-Frappe-CSRF-Token": window.csrf_token ?? "fetch" },
      });
      const json = await res.json();
      items = json.message ?? [];
    } else {
      items = await searchItems(query.value);
    }

    // Seed results without prices first for instant display
    results.value = items.slice(0, 100).map((i) => ({
      ...i,
      price: null,
      stock: null,
      _loading: true,
    }));
    cursor.value = 0;

    // Enrich price + stock in background (batched)
    enrichResults(results.value.slice());
  } catch (e) {
    console.error("[ItemSearchModal] search error:", e);
  } finally {
    loading.value = false;
  }
}

async function enrichResults(snapshot) {
  // Fetch in parallel with concurrency limit of 8
  const BATCH = 8;
  for (let i = 0; i < snapshot.length; i += BATCH) {
    const batch = snapshot.slice(i, i + BATCH);
    await Promise.all(
      batch.map(async (item) => {
        const live = results.value.find((r) => r.item_code === item.item_code);
        if (!live) return;
        try {
          const { price, stock } = await fetchItemDetails(
            item.item_code,
            props.priceList
          );
          live.price = price;
          live.stock = stock;
        } catch {
          live.price = 0;
          live.stock = 0;
        } finally {
          live._loading = false;
        }
      })
    );
  }
}

// ─── Keyboard navigation ──────────────────────────────────────────────────────

function moveCursor(dir) {
  if (!results.value.length) return;
  cursor.value = Math.max(
    0,
    Math.min(results.value.length - 1, cursor.value + dir)
  );
  nextTick(() => {
    rowRefs.get(cursor.value)?.scrollIntoView({ block: "nearest" });
  });
}

function confirmFocused() {
  const item = results.value[cursor.value];
  if (item) selectItem(item);
}

// ─── Selection ────────────────────────────────────────────────────────────────

function selectItem(item) {
  emit("selected", {
    item_code: item.item_code,
    item_name: item.item_name,
    price: item.price ?? 0,
    stock: item.stock ?? 0,
  });
  close();
}

function close() {
  emit("update:modelValue", false);
}

// ─── Formatting ───────────────────────────────────────────────────────────────

function fmtPrice(val) {
  if (val === null) return "—";
  return Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
</script>

<style scoped>
/* ── Overlay ─────────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(4, 6, 12, 0.72);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* ── Box ─────────────────────────────────────────────────────────────────── */
.modal-box {
  background: #0a0d16;
  border: 1px solid #1a2035;
  border-radius: 14px;
  width: min(780px, 100%);
  max-height: min(640px, 90vh);
  display: flex;
  flex-direction: column;
  box-shadow:
    0 0 0 1px rgba(56,139,255,0.08),
    0 32px 80px rgba(0,0,0,0.7),
    0 8px 20px rgba(0,0,0,0.4);
  overflow: hidden;
}

/* ── Header ──────────────────────────────────────────────────────────────── */
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px 12px;
  border-bottom: 1px solid #12182a;
  flex-shrink: 0;
}

.modal-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-icon {
  font-size: 14px;
  color: #3b82f6;
}

.modal-title {
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #3b82f6;
}

.modal-close {
  background: none;
  border: none;
  color: #2d3f5a;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: color 0.15s, background 0.15s;
  line-height: 1;
}
.modal-close:hover {
  color: #e2e8f0;
  background: #131c2e;
}

/* ── Search Row ──────────────────────────────────────────────────────────── */
.modal-search-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  border-bottom: 1px solid #12182a;
  flex-shrink: 0;
}

.search-field-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #0e1322;
  border: 1px solid #1e2b42;
  border-radius: 8px;
  padding: 8px 12px;
  transition: border-color 0.15s;
}
.search-field-wrap:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.12);
}

.search-prefix {
  color: #2d4060;
  font-size: 18px;
  flex-shrink: 0;
}

.search-field {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #e2e8f0;
  font-family: "JetBrains Mono", monospace;
  font-size: 14px;
}
.search-field::placeholder { color: #1e2d45; }

.search-spinner {
  color: #3b82f6;
  font-size: 16px;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.search-hint {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: #1e2d45;
  white-space: nowrap;
}

/* ── Results ─────────────────────────────────────────────────────────────── */
.modal-results-wrap {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.modal-results-wrap::-webkit-scrollbar { width: 4px; }
.modal-results-wrap::-webkit-scrollbar-track { background: transparent; }
.modal-results-wrap::-webkit-scrollbar-thumb { background: #1a2538; border-radius: 2px; }

.results-table {
  width: 100%;
  border-collapse: collapse;
  font-family: "JetBrains Mono", monospace;
}

.results-table thead tr {
  background: #070a12;
  position: sticky;
  top: 0;
  z-index: 2;
}

.results-table th {
  padding: 9px 14px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #1e3050;
  border-bottom: 1px solid #0e1525;
  text-align: left;
  white-space: nowrap;
}

.results-table td {
  padding: 9px 14px;
  font-size: 13px;
  color: #7a92b0;
  border-bottom: 1px solid #0c1322;
  cursor: pointer;
  transition: background 0.08s, color 0.08s;
  white-space: nowrap;
}

.results-table tr.highlighted td,
.results-table tbody tr:hover td {
  background: #0e1a2e;
  color: #c8d6e8;
}

.td-code { color: #4a9eff; font-weight: 600; }
.td-name { white-space: normal; min-width: 160px; }
.col-num, .td-num { text-align: right; }
.stock-low { color: #ef4444 !important; }

.loading-dot {
  color: #1e3050;
  font-size: 12px;
  animation: blink 1s step-end infinite;
}

/* ── Empty state ─────────────────────────────────────────────────────────── */
.modal-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 60px 20px;
  font-family: "JetBrains Mono", monospace;
  font-size: 13px;
  color: #1e3050;
}

.empty-icon {
  font-size: 28px;
  opacity: 0.4;
}

.empty-spinner {
  font-size: 24px;
  animation: spin 1s linear infinite;
  color: #3b82f6;
}

.modal-empty strong { color: #2d4a6a; }

/* ── Footer ──────────────────────────────────────────────────────────────── */
.modal-footer {
  display: flex;
  gap: 18px;
  padding: 10px 18px;
  border-top: 1px solid #0c1525;
  flex-shrink: 0;
}

.kbd-hint {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: #1a2840;
  display: flex;
  align-items: center;
  gap: 5px;
}

.kbd-hint kbd {
  background: #0e1828;
  border: 1px solid #1a2840;
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 10px;
  color: #2d4a6a;
  font-family: "JetBrains Mono", monospace;
}

/* ── Transitions ─────────────────────────────────────────────────────────── */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.18s ease;
}
.modal-fade-enter-active .modal-box,
.modal-fade-leave-active .modal-box {
  transition: transform 0.18s cubic-bezier(0.4, 0, 0.2, 1);
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-from .modal-box {
  transform: scale(0.96) translateY(8px);
}
.modal-fade-leave-to .modal-box {
  transform: scale(0.96) translateY(8px);
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes blink { 50% { opacity: 0; } }
</style>
