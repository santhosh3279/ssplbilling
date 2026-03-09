<template>
  <div class="flex min-h-screen bg-gray-50">

    <!-- ===================== SIDEBAR ===================== -->
    <aside class="flex w-56 flex-col border-r border-gray-200 bg-white">
      <!-- Logo -->
      <div class="border-b border-gray-100 px-4 py-4">
        <div class="text-base font-bold text-gray-900">Wholesale<span class="font-light text-gray-400">Billing</span></div>
        <div class="mt-0.5 text-[10px] text-gray-400">Fast Billing System</div>
      </div>

      <!-- User -->
      <div class="border-b border-gray-100 px-4 py-3">
        <div class="flex items-center gap-2">
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-600">
            {{ userInitials }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-semibold text-gray-700">{{ session.fullName.value || 'User' }}</div>
            <div class="truncate text-[10px] text-gray-400">{{ session.user.value }}</div>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-3">
        <div class="mb-2 px-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">Menu</div>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-left text-sm font-semibold text-blue-700"
        >
          🏠 Dashboard
        </button>
      </nav>

      <!-- Settings section -->
      <div class="border-t border-gray-100 px-3 py-3">
        <div class="mb-2 px-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">Settings</div>

        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-gray-600 hover:bg-gray-50"
          @click="showGeneralSettings = true"
        >
          ⚙️ General
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-red-500 hover:bg-red-50"
          @click="handleLogout"
        >
          🚪 Logout
        </button>
      </div>
    </aside>

    <!-- ===================== MAIN CONTENT ===================== -->
    <main class="flex-1">
      <!-- Top Bar -->
      <header class="sticky top-0 z-40 border-b border-gray-200 bg-white px-6 py-3">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-lg font-bold text-gray-800">Dashboard</h1>
            <p class="text-xs text-gray-400">{{ today }}</p>
          </div>
        </div>
      </header>

      <!-- Tiles -->
      <div class="mx-auto max-w-4xl px-6 py-8">
        <div class="grid grid-cols-3 gap-4">
          <div
            v-for="tile in tiles"
            :key="tile.id"
            class="group relative cursor-pointer rounded-xl border border-gray-200 bg-white p-6 transition-all duration-200 hover:-translate-y-1 hover:border-blue-300 hover:shadow-lg"
            @click="openModule(tile.id)"
          >
            <span class="absolute right-3 top-3 rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-gray-400">
              {{ tile.shortcut }}
            </span>
            <div class="mb-3 flex h-10 w-10 items-center justify-center rounded-lg text-xl" :class="tile.iconBg">
              {{ tile.icon }}
            </div>
            <div class="text-sm font-semibold text-gray-800">{{ tile.name }}</div>
            <div class="mt-1 text-xs text-gray-400">{{ tile.desc }}</div>
          </div>
        </div>

        <div class="mt-8 flex items-center justify-center gap-6 text-xs text-gray-400">
          <span>Press <kbd class="rounded border border-gray-300 bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold">F1</kbd> – <kbd class="rounded border border-gray-300 bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold">F9</kbd> to quick open</span>
          <span class="text-gray-300">|</span>
          <span><kbd class="rounded border border-gray-300 bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold">Ctrl+L</kbd> Customer</span>
          <span class="text-gray-300">|</span>
          <span><kbd class="rounded border border-gray-300 bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold">Ctrl+I</kbd> Item Search</span>
        </div>
      </div>
    </main>

    <!-- ===================== GENERAL SETTINGS DIALOG ===================== -->
    <div v-if="showGeneralSettings" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showGeneralSettings = false">
      <div class="w-[680px] rounded-xl bg-white shadow-2xl">
        <div class="border-b border-gray-200 px-5 py-4">
          <div class="text-sm font-semibold text-gray-700">⚙️ General Settings</div>
        </div>
        <div class="flex max-h-[75vh] flex-col gap-4 overflow-y-auto px-5 py-4">
          <div class="flex flex-col gap-1">
            <label class="text-xs font-semibold text-gray-500">Bill Naming Series</label>
            <select
              v-model="defaultSeries"
              class="rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              <option v-for="s in availableSeries" :key="s" :value="s">{{ s }}</option>
            </select>
            <div v-if="userAllowedString" class="mt-1 flex flex-wrap gap-1">
              <span class="text-[9px] font-bold uppercase tracking-wider text-gray-400">User Permissions:</span>
              <span v-for="p in userAllowedString.split(',')" :key="p" class="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-600">
                {{ p.trim() }}
              </span>
            </div>
          </div>

          <div class="flex flex-col gap-1">
            <label class="text-xs font-semibold text-gray-500">Default Zoom (%)</label>
            <div class="flex items-center gap-3">
              <input
                type="number"
                v-model.number="defaultZoom"
                min="50"
                max="300"
                step="10"
                class="w-24 rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
              />
              <span class="text-xs text-gray-400">50 – 300{{ defaultZoom !== null ? ` (current: ${defaultZoom}%)` : '' }}</span>
            </div>
          </div>



          <!-- SSPL Billing Settings Details -->
          <div v-if="systemSettings" class="mt-4 border-t border-gray-100 pt-4">
            <div class="mb-3 text-[10px] font-bold uppercase tracking-wider text-gray-400">System Configuration (SSPL Billing Settings)</div>

            <!-- Discount Account, Cipher Map & Zoom -->
            <div class="mb-3 flex flex-col gap-1.5">
              <div class="flex justify-between text-xs">
                <span class="text-gray-500">Discount Account</span>
                <span class="font-medium text-gray-700">{{ systemSettings.discount_account || '--' }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-gray-500">Cipher Map</span>
                <span class="font-mono text-gray-700">{{ systemSettings.cipher_map || '--' }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-gray-500">Your Zoom</span>
                <span class="font-medium text-gray-700">{{ systemSettings.user_zoom || '--' }}%</span>
              </div>
            </div>

            <!-- Billing Series -->
            <div class="mb-3">
              <div class="mb-1 text-[10px] font-semibold text-gray-400">Billing Series</div>
              <div class="overflow-auto rounded-lg border border-gray-100">
                <table class="w-full text-[10px]">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Series</th>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Price List</th>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Warehouse</th>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Tax Template</th>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Cost Center</th>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Print Format</th>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Cash A/C</th>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Bank</th>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">UPI</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="bs in filteredBillingSeries" :key="bs.series" class="border-t border-gray-100">
                      <td class="whitespace-nowrap px-2 py-1.5 font-medium">{{ bs.series }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.price_list || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.warehouse || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.tax_template || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.cost_center || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.print_format || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.cash_account || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.bank || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.upi || '--' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- User Series -->
            <div v-if="systemSettings.user_series?.length">
              <div class="mb-1 text-[10px] font-semibold text-gray-400">User Series Permissions</div>
              <div class="overflow-auto rounded-lg border border-gray-100">
                <table class="w-full text-[10px]">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-2 py-1.5 text-left text-gray-400">User</th>
                      <th class="px-2 py-1.5 text-left text-gray-400">Allowed Series</th>
                      <th class="px-2 py-1.5 text-right text-gray-400">Zoom</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="us in systemSettings.user_series" :key="us.user" class="border-t border-gray-100">
                      <td class="px-2 py-1.5 font-medium">{{ us.user }}</td>
                      <td class="px-2 py-1.5 font-mono">{{ us.allowed_series || '--' }}</td>
                      <td class="px-2 py-1.5 text-right font-mono">{{ us.zoom_value || '--' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 border-t border-gray-200 px-5 py-3">
          <button class="rounded bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-700" @click="saveGeneralSettings">Save</button>
        </div>
      </div>
    </div>

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="custSearchModalRef"
      :show="showCustomerSearchModal"
      :initialType="searchType"
      @close="closeCustomerSearchModal"
      @select="pickCust"
    />

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="itemSearchModalRef"
      :show="showItemSearchModal"
      search-type="Sales"
      :price-list="filteredBillingSeries[0]?.price_list || defaultSeries || 'Standard Selling'"
      :warehouse="warehouseLabel"
      @close="showItemSearchModal = false"
      @select="pickItem"
    />

    <!-- CUSTOMER LEDGER SUB-WINDOW -->
    <CustomerLedger
      v-if="showLedgerWindow"
      :is-sub-window="true"
      :ledger-name="ledgerCustomerName"
      :ledger-type="ledgerType"
      :initial-from-date="ledgerFromDate"
      :initial-to-date="ledgerToDate"
      @close="closeLedgerAndReturnToSearch"
    />

    <!-- STOCK LEDGER SUB-WINDOW -->
    <StockLedger
      v-if="showStockLedgerWindow"
      :is-sub-window="true"
      :item-code="stockLedgerItemCode"
      :initial-from-date="stockLedgerFromDate"
      :initial-to-date="stockLedgerToDate"
      @close="closeStockLedgerAndReturnToSearch"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { session } from '../session'
import { dashboardApi } from '../services/dashboard'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import CustomerLedger from './CustomerLedger.vue'
import StockLedger from './StockLedger.vue'
import ItemSearch from '../components/ItemSearch.vue'
import { fetchItemPrice, fetchItemStockForWarehouses } from '../api.js'
import { searchCustomers } from '../customersearch.js'
import { createCustomer, updateCustomer } from '../api/customer.js'
import { useItemCache } from '../services/itemCache.js'

const router = useRouter()

const { refreshItemCache } = useItemCache()

// ==================== USER ====================
const userInitials = computed(() => {
  const name = String(session.fullName.value || session.user.value || 'U')
  return name.split(' ').map(w => w[0] || '').join('').toUpperCase().slice(0, 2) || 'U'
})

async function handleLogout() {
  await session.logout()
  router.push('/login')
}

// ==================== DATE ====================
const today = new Date().toLocaleDateString('en-IN', {
  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
})

// ==================== TILES ====================
const tiles = [
  { id: 'sales', name: 'Sales Entry', desc: 'Create sales invoices', icon: '🧾', shortcut: 'F1', iconBg: 'bg-blue-50' },
  { id: 'purchase', name: 'Purchase Entry', desc: 'Record purchases', icon: '📥', shortcut: 'F2', iconBg: 'bg-green-50' },
  { id: 'payment', name: 'Payment Entry', desc: 'Outgoing payments', icon: '💸', shortcut: 'F3', iconBg: 'bg-amber-50' },
  { id: 'receipt', name: 'Receipt Entry', desc: 'Incoming receipts', icon: '📄', shortcut: 'F4', iconBg: 'bg-green-50' },
  { id: 'cashier', name: 'Cashier Entry', desc: 'POS cash management', icon: '💰', shortcut: 'F5', iconBg: 'bg-amber-50' },
  { id: 'ledger', name: 'Customer Ledger', desc: 'View customer account history', icon: '📋', shortcut: 'F6', iconBg: 'bg-purple-50' },
  { id: 'pricelist', name: 'Price List Viewer', desc: 'View item prices', icon: '💲', shortcut: 'F7', iconBg: 'bg-green-50' },
  { id: 'journal', name: 'Journal Entry', desc: 'Manual journal entries', icon: '📒', shortcut: 'F8', iconBg: 'bg-red-50' },
  { id: 'contra', name: 'Contra Entry', desc: 'Bank to cash transfers', icon: '🔄', shortcut: 'F9', iconBg: 'bg-amber-50' },
]

const readyModules = ['sales', 'purchase', 'cashier', 'ledger', 'pricelist', 'journal', 'contra']

// payment/receipt/journal/contra are aliases into the PaymentReceiptEntry page
const routeAliases = { 
  payment: '/payment?mode=Pay', 
  receipt: '/payment?mode=Receive',
  journal: '/payment', 
  contra: '/payment' 
}

function openModule(id) {
  if (routeAliases[id]) {
    router.push(routeAliases[id])
  } else if (readyModules.includes(id)) {
    router.push('/' + id)
  } else {
    alert('Coming soon: ' + id)
  }
}

// ==================== F-KEY SHORTCUTS ====================
const routeMap = {
  F1: 'sales', F2: 'purchase', F3: 'payment',
  F4: 'receipt', F5: 'cashier', F6: 'ledger',
  F7: 'pricelist', F8: 'journal', F9: 'contra',
}

import { useShortcuts } from '../services/shortcutManager'

// ==================== KEYBOARD SHORTCUTS ====================
useShortcuts({
  'F1': () => openModule('sales'),
  'F2': () => openModule('purchase'),
  'F3': () => openModule('payment'),
  'F4': () => openModule('receipt'),
  'F5': () => openModule('cashier'),
  'F6': () => openModule('ledger'),
  'F7': () => openModule('pricelist'),
  'F8': () => openModule('journal'),
  'F9': () => openModule('contra'),
  'ESCAPE': () => {
    if (showGeneralSettings.value) { showGeneralSettings.value = false; return }
    if (showCustomerSearchModal.value) { closeCustomerSearchModal(); return }
    if (showItemSearchModal.value) { showItemSearchModal.value = false; return }
    if (showLedgerWindow.value) { showLedgerWindow.value = false; return }
    if (showStockLedgerWindow.value) { showStockLedgerWindow.value = false; return }
  }
})

const availableSeries = ref([])
const userAllowedString = ref('')
const systemSettings = ref(null)

const BILLING_SETTINGS_CACHE_KEY = 'wb-billing-settings-v2'
const BILLING_SETTINGS_TTL = 60 * 60 * 1000 // 1 hour

// ==================== GENERAL SETTINGS ====================
const showGeneralSettings = ref(false)
const defaultSeries = ref(localStorage.getItem('wb-series') || '')
const defaultZoom = ref(null) // populated from SSPL Billing Settings on load

async function saveGeneralSettings() {
  localStorage.setItem('wb-series', defaultSeries.value)
  if (defaultZoom.value === null) { showGeneralSettings.value = false; return }
  const zoom = Math.max(50, Math.min(300, defaultZoom.value))
  defaultZoom.value = zoom
  localStorage.setItem('wb-zoom', String(zoom))
  try {
    await dashboardApi.saveDefaultZoom(zoom)
    // Bust the settings cache so next load picks up the new zoom
    localStorage.removeItem(BILLING_SETTINGS_CACHE_KEY)
  } catch (e) {
    console.warn('[Dashboard] saveDefaultZoom failed:', e)
  }
  showGeneralSettings.value = false
}

// ==================== CUSTOMER SEARCH ====================
const showCustomerSearchModal = ref(false)
const searchType = ref('All')
const showLedgerWindow = ref(false)
const ledgerCustomerName = ref('')
const ledgerType = ref('Customer')
const ledgerFromDate = ref('')
const ledgerToDate = ref('')
const custSearchModalRef = ref(null)

async function openCustomerSearch(type = 'All') {
  searchType.value = type
  showCustomerSearchModal.value = true
  
  // Reset any open sub-forms or date filters when opening the search modal
  nextTick(() => {
    custSearchModalRef.value?.closeSubForm()
    custSearchModalRef.value?.focus()
  })
}

function closeCustomerSearchModal() {
  showCustomerSearchModal.value = false
}

function closeLedgerAndReturnToSearch() {
  showLedgerWindow.value = false
  openCustomerSearch(searchType.value)
}

function pickCust(item, dates) {
  showCustomerSearchModal.value = false
  ledgerCustomerName.value = item.name
  ledgerType.value = item.type || 'Customer'
  if (dates) {
    ledgerFromDate.value = dates.from
    ledgerToDate.value = dates.to
  } else {
    ledgerFromDate.value = ''
    ledgerToDate.value = ''
  }
  showLedgerWindow.value = true
}

// ==================== ITEM SEARCH ====================
const showItemSearchModal = ref(false)
const showStockLedgerWindow = ref(false)
const stockLedgerItemCode = ref('')
const stockLedgerFromDate = ref('')
const stockLedgerToDate = ref('')
const itemSearchModalRef = ref(null)

async function openItemSearch(clear = true) {
  showItemSearchModal.value = true
  // Reset any open sub-forms or date filters when opening the search modal
  nextTick(() => {
    itemSearchModalRef.value?.closeSubForm()
    itemSearchModalRef.value?.focus()
  })
}

function pickItem(item, dates) {
  showItemSearchModal.value = false
  stockLedgerItemCode.value = item.item_code
  if (dates) {
    stockLedgerFromDate.value = dates.from
    stockLedgerToDate.value = dates.to
  } else {
    stockLedgerFromDate.value = ''
    stockLedgerToDate.value = ''
  }
  showStockLedgerWindow.value = true
}

function closeStockLedgerAndReturnToSearch() {
  showStockLedgerWindow.value = false
  openItemSearch(false) // Return without clearing search
}

async function fetchSettings() {
  // 1. Fetch allowed series for this user
  try {
    const d = await dashboardApi.getAllowedSeries()
    availableSeries.value = d.allowed_series || []
    userAllowedString.value = d.user_allowed_string || ''
    if (availableSeries.value.length && !availableSeries.value.includes(defaultSeries.value)) {
      defaultSeries.value = availableSeries.value[0]
    }
  } catch (e) {
    console.warn('[Dashboard] getAllowedSeries failed:', e)
  }

  // 2. Fetch global settings
  try {
    // Check cache first
    let settings = null
    const cached = JSON.parse(localStorage.getItem(BILLING_SETTINGS_CACHE_KEY) || 'null')
    if (cached && (Date.now() - cached.ts) < BILLING_SETTINGS_TTL) {
      settings = cached.data
    } else {
      settings = await dashboardApi.getBillingSettings()
      if (settings) {
        localStorage.setItem(BILLING_SETTINGS_CACHE_KEY, JSON.stringify({ data: settings, ts: Date.now() }))
      }
    }
    
    systemSettings.value = settings
    // Sync user's zoom to localStorage so Sales Entry can use it
    if (settings && settings.user_zoom) {
      localStorage.setItem('wb-zoom', settings.user_zoom)
      defaultZoom.value = parseInt(settings.user_zoom)
    }
  } catch (e) {
    console.warn('[Dashboard] getBillingSettings failed:', e)
  }
}

const filteredBillingSeries = computed(() => {
  const all = systemSettings.value?.billing_series || []
  if (!availableSeries.value?.length) {
    return userAllowedString.value ? [] : all
  }
  return all.filter(bs => availableSeries.value.includes(bs.series))
})

const warehouseLabel = computed(() => {
  const warehouses = [...new Set(
    filteredBillingSeries.value.map(bs => bs.warehouse).filter(Boolean)
  )]
  if (warehouses.length === 0) return 'All Warehouses'
  if (warehouses.length === 1) return warehouses[0]
  return warehouses.join(', ')
})

onMounted(() => {
  window.addEventListener('wb-global-ledger-search', () => openCustomerSearch('All'))
  window.addEventListener('wb-global-item-search', openItemSearch)
  window.addEventListener('wb-navigate-home', () => router.push('/'))
  fetchSettings()
  refreshItemCache('Sales') // Preload items for fast entry
})
onUnmounted(() => {
  window.removeEventListener('wb-global-ledger-search', () => openCustomerSearch('All'))
  window.removeEventListener('wb-global-item-search', openItemSearch)
  window.removeEventListener('wb-navigate-home', () => router.push('/'))
})

</script>
