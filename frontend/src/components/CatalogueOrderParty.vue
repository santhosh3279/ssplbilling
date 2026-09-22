<template>
  <section v-if="session.isSystemUser.value" class="m-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-[var(--color-text)] space-y-4 shadow-sm">
    <div class="flex items-center justify-between pb-2 border-b border-[var(--color-border)]/60">
      <div>
        <h2 class="font-bold text-sm uppercase tracking-wider text-[var(--color-text)]">Sales Order Customer & Price List</h2>
        <p class="text-xs text-[var(--color-text-muted)]">Search and select a customer and selling price list to view catalogue rates and place orders.</p>
      </div>
      <button
        v-if="orderContext.customer"
        type="button"
        @click="cancelModify"
        class="text-xs font-bold text-[var(--color-text-muted)] hover:text-[var(--color-text)] px-2.5 py-1 rounded-lg hover:bg-[var(--color-bg)] border border-[var(--color-border)] transition"
        title="Close"
      >
        ✕ Close
      </button>
    </div>

    <form class="flex flex-wrap items-end gap-4" @submit.prevent="apply">
      <!-- Customer Search -->
      <div class="relative flex-1 min-w-[240px]">
        <label for="catalogue-customer-search" class="block text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] mb-1">
          Customer Search
        </label>
        <div class="relative flex items-center">
          <input
            id="catalogue-customer-search"
            ref="searchInputRef"
            v-model="query"
            type="search"
            autocomplete="off"
            placeholder="Search customer name or code..."
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 pr-16 text-sm text-[var(--color-text)] outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            @focus="onFocus"
            @blur="onBlur"
            @input="onInput"
            @keydown="onKeydown"
          />
          <div class="absolute right-1.5 flex items-center gap-1">
            <button
              v-if="query || customer"
              type="button"
              @mousedown.prevent="clearCustomer"
              class="rounded p-1 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)] transition"
              title="Clear customer search"
            >
              ✕
            </button>
            <button
              type="button"
              @mousedown.prevent="showCustomerModal = true"
              class="rounded p-1 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 transition"
              title="Open full customer search modal"
            >
              🔍
            </button>
          </div>
        </div>

        <!-- Autocomplete dropdown -->
        <div
          v-if="showDropdown && (customers.length || loading || (query && !customer))"
          class="absolute z-50 left-0 right-0 mt-1 max-h-64 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl py-1 text-sm"
        >
          <div v-if="loading" class="px-3 py-2 text-xs text-[var(--color-text-muted)] italic">
            Searching customers…
          </div>
          <div
            v-for="(c, idx) in customers"
            :key="c.name"
            @mousedown.prevent="selectCustomer(c)"
            class="cursor-pointer px-3 py-2 transition-colors flex items-center justify-between"
            :class="idx === highlightedIndex ? 'bg-indigo-600 text-white' : 'hover:bg-[var(--color-surface-raised)] text-[var(--color-text)]'"
          >
            <div class="min-w-0 pr-2">
              <div class="font-bold truncate" :class="idx === highlightedIndex ? 'text-white' : 'text-[var(--color-text)]'">
                {{ c.customer_name }}
              </div>
              <div class="text-xs opacity-75 font-mono truncate" :class="idx === highlightedIndex ? 'text-indigo-100' : 'text-[var(--color-text-muted)]'">
                {{ c.name }}
              </div>
            </div>
            <div v-if="c.default_price_list" class="shrink-0 text-xs opacity-80 text-right" :class="idx === highlightedIndex ? 'text-indigo-100' : 'text-[var(--color-text-muted)]'">
              {{ c.default_price_list }}
            </div>
          </div>
          <div v-if="!loading && !customers.length && query && !customer" class="px-3 py-2 text-xs text-[var(--color-text-muted)] italic">
            No customers found matching "{{ query }}"
          </div>
        </div>
      </div>

      <!-- Price List -->
      <label class="flex-1 min-w-[200px] text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
        Price List
        <select
          v-model="priceList"
          required
          class="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Select price list</option>
          <option v-if="priceList && !priceLists.some(row => row.name === priceList)" :value="priceList">{{ priceList }}</option>
          <option v-for="row in priceLists" :key="row.name" :value="row.name">{{ row.name }}</option>
        </select>
      </label>

      <!-- Buttons -->
      <div class="flex items-center gap-2">
        <button
          type="submit"
          :disabled="saving || loading || !customer"
          class="rounded-lg bg-indigo-600 hover:bg-indigo-700 px-5 py-2 font-bold text-white text-sm disabled:opacity-50 transition shadow-sm cursor-pointer"
        >
          {{ saving ? 'Applying…' : 'Apply' }}
        </button>
        <button
          v-if="orderContext.customer"
          type="button"
          @click="cancelModify"
          class="rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-bg)] px-4 py-2 text-sm font-semibold text-[var(--color-text)] transition cursor-pointer"
        >
          Cancel
        </button>
      </div>
    </form>

    <p v-if="loading && !showDropdown" role="status" class="text-xs text-[var(--color-text-muted)]">Loading customers and price lists…</p>
    <p v-if="error" role="alert" class="text-xs text-red-500 font-medium">{{ error }}</p>

    <!-- Full Customer Search Modal -->
    <CustomerSearchModal
      v-if="showCustomerModal"
      :show="showCustomerModal"
      initial-type="Customer"
      :allowed-types="['Customer']"
      :skip-date-filter="true"
      @close="showCustomerModal = false"
      @select="onCustomerModalSelect"
    />
  </section>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { frappeGet, frappePost } from '../api.js'
import { session } from '../session.js'
import { orderContext, setOrderContext } from '../services/catalogueOrderContext.js'
import CustomerSearchModal from './CustomerSearchModal.vue'

const emit = defineEmits(['applied', 'close'])

const query = ref('')
const customer = ref(orderContext.value.customer || '')
const priceList = ref(orderContext.value.price_list || '')
const customers = ref([])
const priceLists = ref([])
const showDropdown = ref(false)
const highlightedIndex = ref(-1)
const showCustomerModal = ref(false)
const searchInputRef = ref(null)

const loading = ref(false)
const saving = ref(false)
const error = ref('')

let timer = null
let request = 0

function syncFromContext() {
  customer.value = orderContext.value.customer || ''
  priceList.value = orderContext.value.price_list || ''
  if (orderContext.value.customer) {
    query.value = orderContext.value.customer_name
      ? `${orderContext.value.customer_name} (${orderContext.value.customer})`
      : orderContext.value.customer
  } else {
    query.value = ''
  }
}

watch(orderContext, () => {
  syncFromContext()
}, { immediate: true })

async function fetchOptions(searchQuery = '') {
  clearTimeout(timer)
  const id = ++request
  loading.value = true
  try {
    const result = await frappeGet('ssplbilling.api.catalogue_order_api.get_order_options', { query: searchQuery })
    if (id !== request) return
    customers.value = result.customers || []
    priceLists.value = result.price_lists || []
    error.value = ''
  } catch (err) {
    if (id === request) error.value = err.message || 'Could not load customers.'
  } finally {
    if (id === request) loading.value = false
  }
}

function triggerDebouncedSearch(searchQuery) {
  clearTimeout(timer)
  loading.value = true
  timer = setTimeout(() => {
    fetchOptions(searchQuery)
  }, 250)
}

function onInput() {
  customer.value = ''
  showDropdown.value = true
  highlightedIndex.value = -1
  triggerDebouncedSearch(query.value)
}

function onFocus() {
  showDropdown.value = true
  if (!customers.value.length) {
    fetchOptions(customer.value ? '' : query.value)
  }
}

function onBlur() {
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}

function selectCustomer(c) {
  customer.value = c.name
  query.value = `${c.customer_name} (${c.name})`
  showDropdown.value = false
  highlightedIndex.value = -1
  error.value = ''
  if (c.default_price_list) {
    priceList.value = c.default_price_list
  }
}

function clearCustomer() {
  customer.value = ''
  query.value = ''
  showDropdown.value = true
  highlightedIndex.value = -1
  error.value = ''
  fetchOptions('')
  nextTick(() => searchInputRef.value?.focus())
}

function onKeydown(e) {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (!showDropdown.value) {
      showDropdown.value = true
      return
    }
    if (customers.value.length) {
      highlightedIndex.value = (highlightedIndex.value + 1) % customers.value.length
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (!showDropdown.value) {
      showDropdown.value = true
      return
    }
    if (customers.value.length) {
      highlightedIndex.value = (highlightedIndex.value - 1 + customers.value.length) % customers.value.length
    }
  } else if (e.key === 'Enter') {
    if (showDropdown.value) {
      if (highlightedIndex.value >= 0 && customers.value[highlightedIndex.value]) {
        e.preventDefault()
        selectCustomer(customers.value[highlightedIndex.value])
        return
      } else if (customers.value.length === 1) {
        e.preventDefault()
        selectCustomer(customers.value[0])
        return
      }
    }
    if (!customer.value) {
      e.preventDefault()
      error.value = 'Please select a customer from the search results.'
    }
  } else if (e.key === 'Escape') {
    showDropdown.value = false
  }
}

function onCustomerModalSelect(party) {
  customer.value = party.name
  const label = party.label || party.customer_name || party.name
  query.value = `${label} (${party.name})`
  showDropdown.value = false
  showCustomerModal.value = false
  error.value = ''

  if (party.default_price_list) {
    priceList.value = party.default_price_list
  } else {
    const found = customers.value.find(c => c.name === party.name)
    if (found?.default_price_list) {
      priceList.value = found.default_price_list
    } else {
      frappeGet('ssplbilling.api.catalogue_order_api.get_order_options', { query: party.name }).then(res => {
        const match = res?.customers?.find(c => c.name === party.name)
        if (match?.default_price_list) {
          priceList.value = match.default_price_list
        }
      }).catch(() => {})
    }
  }
}

function cancelModify() {
  syncFromContext()
  showDropdown.value = false
  emit('close')
}

async function apply() {
  if (saving.value) return
  if (!customer.value) {
    error.value = 'Please select a customer.'
    return
  }
  if (!priceList.value) {
    error.value = 'Please select a price list.'
    return
  }
  saving.value = true
  error.value = ''
  try {
    const result = await frappePost(
      'ssplbilling.api.catalogue_order_api.get_system_order_context',
      { customer: customer.value, price_list: priceList.value },
      { silent: true }
    )
    setOrderContext(result)
    emit('applied', result)
  } catch (err) {
    error.value = err.message || 'Could not select this customer and price list.'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (session.isSystemUser.value) {
    fetchOptions('')
  }
})

onBeforeUnmount(() => {
  ++request
  clearTimeout(timer)
})
</script>
