<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm outline-none"
  >
    <div class="flex h-[90vh] w-[80vw] flex-col rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden relative">
      <!-- Header -->
      <div class="border-b border-[var(--color-border)] px-6 py-4 flex items-center justify-between bg-[var(--color-surface-raised)]">
        <div>
          <div class="text-2xl font-bold text-[var(--color-text)]">Loading Items</div>
          <div class="text-sm text-[var(--color-text-muted)]">Manage items available for Loading Receipts</div>
        </div>
        <div class="flex items-center gap-4">
          <button
            @click="showCreateForm = true"
            class="rounded-lg bg-[var(--color-info)] px-4 py-2 text-sm font-bold text-white shadow-md hover:opacity-90 transition-all active:scale-95"
          >
            + Create New Item
          </button>
          <button @click="$emit('close')" class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)] ml-2">✕</button>
        </div>
      </div>

      <!-- Search Bar -->
      <div class="p-4 border-b border-[var(--color-border)]">
        <input
          v-model="query"
          type="text"
          placeholder="Search items by code or name..."
          class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          @input="onSearch"
        />
      </div>

      <!-- Item List -->
      <div class="flex-1 overflow-y-auto">
        <table class="w-full text-left border-collapse">
          <thead class="sticky top-0 bg-[var(--color-surface)] shadow-sm z-10">
            <tr>
              <th class="px-6 py-3 border-b border-[var(--color-border)] text-xs font-bold uppercase text-[var(--color-text-muted)]">Code</th>
              <th class="px-6 py-3 border-b border-[var(--color-border)] text-xs font-bold uppercase text-[var(--color-text-muted)]">Item Name</th>
              <th class="px-6 py-3 border-b border-[var(--color-border)] text-xs font-bold uppercase text-[var(--color-text-muted)] text-center">UOM</th>
              <th class="px-6 py-3 border-b border-[var(--color-border)] text-xs font-bold uppercase text-[var(--color-text-muted)] text-right">Default Rate</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in items"
              :key="item.item_code"
              class="hover:bg-[var(--color-surface-raised)]/30 transition-colors border-b border-[var(--color-border)]/50"
            >
              <td class="px-6 py-4 font-mono text-lg font-bold text-[var(--color-info)]">{{ item.item_code }}</td>
              <td class="px-6 py-4 text-lg text-[var(--color-text)]">{{ item.item_name }}</td>
              <td class="px-6 py-4 text-lg text-[var(--color-text-muted)] text-center">{{ item.uom || 'Nos' }}</td>
              <td class="px-6 py-4 font-mono text-lg font-bold text-right text-[var(--color-text)]">₹{{ (item.rate || 0).toFixed(2) }}</td>
            </tr>
            <tr v-if="!items.length && !loading">
              <td colspan="4" class="px-6 py-12 text-center text-[var(--color-text-muted)] italic text-lg">
                No loading items found.
              </td>
            </tr>
            <tr v-if="loading">
              <td colspan="4" class="px-6 py-12 text-center">
                <span class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-info)] border-t-transparent"></span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Create Form Overlay -->
      <div
        v-if="showCreateForm"
        class="absolute inset-0 z-[60] flex items-center justify-center bg-black/60"
      >
        <div class="w-[500px] rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden">
          <div class="bg-[var(--color-surface-raised)] px-6 py-4 border-b border-[var(--color-border)] flex justify-between items-center">
            <span class="text-xl font-bold text-[var(--color-text)]">Create Loading Item</span>
            <button @click="showCreateForm = false" class="text-2xl text-[var(--color-text-muted)]">✕</button>
          </div>
          <div class="p-6 space-y-4">
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Item Code *</label>
              <input
                v-model="form.item_code"
                ref="codeRef"
                type="text"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-xl font-bold outline-none focus:border-[var(--color-info)]"
                placeholder="LR-ITEM-001"
                @keydown.enter.prevent="nameRef?.focus()"
              />
            </div>
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Item Name *</label>
              <input
                v-model="form.item_name"
                ref="nameRef"
                type="text"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-xl outline-none focus:border-[var(--color-info)]"
                placeholder="Enter item name..."
                @keydown.enter.prevent="rateRef?.focus()"
              />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <label class="text-xs font-bold uppercase text-[var(--color-text-muted)]">UOM</label>
                <input
                  v-model="form.uom"
                  type="text"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-xl outline-none focus:border-[var(--color-info)]"
                  placeholder="Nos"
                />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Default Rate</label>
                <input
                  v-model.number="form.rate"
                  ref="rateRef"
                  type="number"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-xl font-mono outline-none focus:border-[var(--color-info)]"
                  placeholder="0.00"
                  @keydown.enter.prevent="saveItem"
                />
              </div>
            </div>
          </div>
          <div class="px-6 py-4 bg-[var(--color-surface)] border-t border-[var(--color-border)] flex gap-3">
            <button
              @click="showCreateForm = false"
              class="flex-1 rounded-lg py-2 font-bold uppercase text-[var(--color-text-muted)] bg-[var(--color-surface-raised)] border border-[var(--color-border)]"
            >
              Cancel
            </button>
            <button
              @click="saveItem"
              :disabled="saving || !form.item_code || !form.item_name"
              class="flex-1 rounded-lg py-2 font-bold uppercase text-white bg-[var(--color-info)] shadow-lg disabled:opacity-50"
            >
              {{ saving ? 'Saving...' : 'Save Item' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { frappePost, frappeGet } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close'])

// Link Esc to close (either the form or the whole modal)
useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: () => {
    if (showCreateForm.value) {
      showCreateForm.value = false
    } else {
      emit('close')
    }
  }
})

const items = ref([])
const loading = ref(false)
const query = ref('')
const showCreateForm = ref(false)
const saving = ref(false)

const form = ref({
  item_code: '',
  item_name: '',
  uom: 'Nos',
  rate: 0
})

const codeRef = ref(null)
const nameRef = ref(null)
const rateRef = ref(null)

async function fetchItems() {
  loading.value = true
  try {
    const res = await frappePost('ssplbilling.api.loading_receipt_api.search_loading_items', { query: query.value })
    items.value = res || []
  } catch (e) {
    console.error('Failed to fetch loading items:', e)
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchItems, 300)
}
let searchTimer = null

async function saveItem() {
  if (!form.value.item_code || !form.value.item_name) return
  saving.value = true
  try {
    await frappePost('frappe.client.insert', {
      doc: {
        doctype: 'Loading Item',
        ...form.value
      }
    })
    showCreateForm.value = false
    form.value = { item_code: '', item_name: '', uom: 'Nos', rate: 0 }
    fetchItems()
  } catch (e) {
    alert('Failed to save item: ' + e.message)
  } finally {
    saving.value = false
  }
}

watch(showCreateForm, (val) => {
  if (val) {
    nextTick(() => codeRef.value?.focus())
  }
})

onMounted(() => {
  fetchItems()
})
</script>
