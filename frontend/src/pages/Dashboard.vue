<template>
  <div class="flex min-h-screen bg-slate-900">

    <!-- ===================== SIDEBAR ===================== -->
    <aside class="flex w-56 flex-col border-r border-slate-700 bg-slate-800">
      <!-- Logo -->
      <div class="border-b border-slate-700 px-4 py-4">
        <div class="text-base font-bold text-white">Wholesale<span class="font-light text-slate-400">Billing</span></div>
        <div class="mt-0.5 text-[10px] text-slate-400">Fast Billing System</div>
      </div>

      <!-- User -->
      <div class="border-b border-slate-700 px-4 py-3">
        <div class="flex items-center gap-2">
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-xs font-bold text-white">
            {{ userInitials }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-semibold text-slate-200">{{ session.fullName.value || 'User' }}</div>
            <div class="flex items-center gap-1.5">
              <span class="truncate text-[10px] text-slate-400">{{ session.user.value }}</span>
              <span class="shrink-0 rounded px-1 py-0.5 text-[9px] font-bold uppercase tracking-wider"
                :class="{
                  'bg-amber-500/20 text-amber-400': userRole === 'admin',
                  'bg-blue-500/20 text-blue-400': userRole === 'cashier',
                  'bg-green-500/20 text-green-400': userRole === 'biller',
                }"
              >{{ userRole }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-3">
        <div class="mb-2 px-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">Menu</div>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-left text-sm font-semibold text-white"
        >
          🏠 Dashboard
        </button>
        <button
          v-if="canAccessTile('Cashier-Management')"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/Cashier-Management')"
        >
          📓 <span class="font-bold text-white">Cashier</span>
        </button>
        <button
          v-if="canAccessTile('pricing-rules')"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/pricing-rules')"
        >
          🏷️ <span class="font-bold text-white">Pricing Rules</span>
        </button>
        <button
          v-if="canAccessTile('barcode-print')"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/barcode-print')"
        >
          🔖 <span class="font-bold text-white">Print Barcodes</span>
        </button>
        <button
          v-if="canAccessTile('incentive-ledger')"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/incentive-ledger')"
        >
          🏆 <span class="font-bold text-white">Incentive Ledger</span>
        </button>
        <button
          v-if="canAccessTile('loading-receipt')"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/loading-receipt')"
        >
          🚚 <span class="font-bold text-white">Loading Receipt</span>
        </button>
        <button
          v-if="canAccessTile('material-transfer')"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/material-transfer')"
        >
          🚚 <span class="font-bold text-white">Stock Transfer</span>
        </button>
        <button
          v-if="canAccessTile('stock-reconciliation')"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/stock-reconciliation')"
        >
          ⚖️ <span class="font-bold text-white">Stock Reconcile</span>
        </button>
        <button
          v-if="canAccessTile('parcel-address')"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/parcel-address')"
        >
          📦 <span class="font-bold text-white">Parcel Address</span>
        </button>
      </nav>

      <!-- Settings section -->
      <div class="border-t border-slate-700 px-3 py-3">
        <div class="mb-2 px-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">Settings</div>

        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="showSystemPerformance = true"
        >
          📊 System Performance
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="showGeneralSettings = true"
        >
          ⚙️ General
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-red-400 hover:bg-slate-700"
          @click="handleLogout"
        >
          🚪 Logout
        </button>
      </div>
    </aside>

    <!-- ===================== MAIN CONTENT ===================== -->
    <main class="flex-1">
      <!-- Top Bar -->
      <header class="sticky top-0 z-40 border-b border-slate-700 bg-slate-800 px-6 py-3">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-lg font-bold text-white">Dashboard</h1>
            <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wider">{{ todayDate }} | {{ todayDay }}</p>
          </div>
        </div>
      </header>

      <div class="flex flex-row items-start justify-between gap-8 px-10 py-10">
        <!-- Left: Tiles -->
        <div class="flex-1 max-w-5xl">
          <div class="grid grid-cols-3 gap-6">
            <div
              v-for="tile in tiles"
              :key="tile.id"
              class="group relative cursor-pointer rounded-xl p-6 transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:brightness-110"
              :class="tile.tileBg"
              @click="openModule(tile.id)"
            >
              <span v-if="tile.shortcut" class="absolute right-3 top-3 flex items-center gap-1.5 rounded-lg border border-white/30 bg-black/40 px-3 py-1.5 font-mono text-lg font-black text-white shadow-lg backdrop-blur-md group-hover:bg-white/30 transition-all">
                {{ tile.shortcut }}
              </span>
              <div class="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-white/20 text-xl">
                {{ tile.icon }}
              </div>
              <div class="text-sm font-semibold text-white">{{ tile.name }}</div>
              <div class="mt-1 text-xs text-white/70">{{ tile.desc }}</div>
            </div>
          </div>
        </div>

        <!-- Right: Clock -->
        <div class="flex-shrink-0 flex flex-col items-center gap-1 pt-2 bg-slate-800/20 p-6 rounded-3xl border border-white/5 backdrop-blur-sm shadow-xl">
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">{{ todayDate }}</div>
          <div class="text-lg font-black text-white uppercase tracking-wider mb-2 drop-shadow-sm">{{ todayDay }}</div>
          <AnalogueClock />
        </div>
      </div>

      <div class="mx-auto max-w-4xl px-6 pb-12">
        <div class="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500">
          <span class="flex items-center gap-1.5">
            Press <kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-slate-300">F1</kbd> – <kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-slate-300">F10</kbd>
            to quick open
          </span>
          <span class="text-slate-700">|</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-slate-300">Ctrl+L</kbd> Customer</span>
          <span class="text-slate-700">|</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-slate-300">Ctrl+I</kbd> Item Search</span>
          <span class="text-slate-700">|</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-slate-300">Ctrl+R</kbd> Stock Reconcile</span>
          <span class="text-slate-700">|</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-slate-300">ESC</kbd> Close Modals</span>
        </div>
      </div>
    </main>

    <!-- ===================== GENERAL SETTINGS DIALOG ===================== -->
    <GeneralSettings
      :show="showGeneralSettings"
      @close="showGeneralSettings = false"
    />

    <!-- SYSTEM PERFORMANCE -->
    <SystemPerformance
      :show="showSystemPerformance"
      @close="showSystemPerformance = false"
    />

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="custSearchModalRef"
      :show="showCustomerSearchModal"
      :initialType="searchType"
      :allowed-types="isBiller ? ['Customer', 'Supplier', 'Employee'] : undefined"
      @close="closeCustomerSearchModal"
      @select="pickCust"
    />

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="itemSearchModalRef"
      :show="showItemSearchModal"
      search-type="Sales"
      :price-list="filteredBillingSeries[0]?.price_list || defaultSeries || 'Standard Selling'"
      :warehouse="defaultWarehouse"
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
    <!-- SUCCESS POPUP -->
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
import GeneralSettings from '../components/GeneralSettings.vue'
import SystemPerformance from '../components/SystemPerformance.vue'
import AnalogueClock from '../components/AnalogueClock.vue'
import { fetchItemPrice, fetchItemStockForWarehouses, frappeGet } from '../api.js'
import { searchCustomers } from '../customersearch.js'
import { createCustomer, updateCustomer } from '../api/customer.js'
import { useItemCache } from '../services/itemCache.js'
import { useShortcuts, useSubwindowWatcher } from '../services/shortcutManager'
import { canAccessTile, canAccessRoute, getUserRole } from '../composables/usePermission'
import { dashboardShortcuts } from '../shortcuts/dashboardShortcuts'

const router = useRouter()

const { refreshItemCache } = useItemCache()
const { user: currentUser } = session

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
const todayDate = computed(() => {
  return new Date().toLocaleDateString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })
})

const todayDay = computed(() => {
  return new Date().toLocaleDateString('en-IN', {
    timeZone: 'Asia/Kolkata',
    weekday: 'long'
  })
})


// ==================== TILES ====================
const userRole = getUserRole()
const isBiller = userRole === 'biller'

const allTiles = [
  { id: 'sales', name: 'Sales Entry', desc: 'Create sales invoices', icon: '🧾', shortcut: 'F1', tileBg: 'bg-blue-600' },
  { id: 'quotation', name: 'Quotation Entry', desc: 'Create quotations', icon: '📄', shortcut: 'F10', tileBg: 'bg-slate-600' },
  { id: 'purchase', name: 'Purchase Entry', desc: 'Record purchases', icon: '📥', shortcut: 'F2', tileBg: 'bg-emerald-600' },
  { id: 'payment', name: 'Payment & Receipt Entry', desc: 'Manage payments and receipts', icon: '💸', shortcut: 'F3', tileBg: 'bg-amber-500' },
  { id: 'purchase-submit', name: 'Purchase Desk', desc: 'Confirm & submit purchases', icon: '📥', shortcut: 'F4', tileBg: 'bg-teal-600' },
  { id: 'cashier', name: 'Cashier Desk', desc: 'Modern payment desk', icon: '🏧', shortcut: 'F5', tileBg: 'bg-indigo-600' },
  { id: 'Cashier-Management', name: 'Cashier Management', desc: 'Daily reconciliation & denominations', icon: '📓', shortcut: '', tileBg: 'bg-emerald-700' },
  { id: 'ledger', name: 'Customer Ledger', desc: 'View customer account history', icon: '📋', shortcut: 'F6', tileBg: 'bg-purple-600' },
  { id: 'purchase-order', name: 'Purchase Order', desc: 'Create & manage purchase orders', icon: '📋', shortcut: 'F7', tileBg: 'bg-sky-600' },
  { id: 'journal-contra', name: 'Journal & Contra', desc: 'General ledger entries', icon: '📒', shortcut: 'F8', tileBg: 'bg-rose-600' },
  { id: 'material-transfer', name: 'Material Transfer', desc: 'Transfer items between warehouses', icon: '🚚', shortcut: 'F9', tileBg: 'bg-cyan-700' },
  { id: 'stock-reconciliation', name: 'Stock Reconciliation', desc: 'Adjust stock levels', icon: '⚖️', shortcut: '', tileBg: 'bg-slate-700' },
  { id: 'sales-order', name: 'Sales Order', desc: 'Create & manage sales orders', icon: '📝', shortcut: '', tileBg: 'bg-orange-600' },
  { id: 'reports', name: 'Reports', desc: 'Business reports and analytics', icon: '📊', shortcut: '', tileBg: 'bg-violet-600' },
]

const tiles = allTiles.filter(t => canAccessTile(t.id))

const readyModules = ['sales', 'quotation', 'purchase', 'cashier', 'purchase-submit', 'ledger', 'purchase-order', 'sales-order', 'journal-contra', 'material-transfer', 'stock-reconciliation', 'reports']

// payment/receipt/journal/contra are aliases into the PaymentReceiptEntry page
const routeAliases = {
  sales: '/sales',
  quotation: '/quotation',
  purchase: '/purchase',
  payment: '/payment',
  'purchase-order': '/purchase-order',
  'sales-order': '/sales-order',
  'journal-contra': '/journal-contra',
  'material-transfer': '/material-transfer',
  'stock-reconciliation': '/stock-reconciliation',
  'Cashier-Management': '/Cashier-Management',
  reports: '/reports',
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
  F4: 'purchase-submit', F5: 'cashier', F6: 'ledger',
  F7: 'purchase-order', F8: 'journal-contra', F9: 'material-transfer',
  F10: 'quotation',
}

// ==================== KEYBOARD SHORTCUTS ====================
useShortcuts(dashboardShortcuts({
  openModule,
  openCustomerSearch: isBiller ? null : () => openCustomerSearch('All'),
  openItemSearch: () => openItemSearch(),
  handleEscape: () => {
    if (showGeneralSettings.value) { showGeneralSettings.value = false; return }
    if (showCustomerSearchModal.value) { closeCustomerSearchModal(); return }
    if (showItemSearchModal.value) { showItemSearchModal.value = false; return }
    if (showLedgerWindow.value) { showLedgerWindow.value = false; return }
    if (showStockLedgerWindow.value) { showStockLedgerWindow.value = false; return }
  }
}))

const availableSeries = ref([])
const userAllowedString = ref('')
const systemSettings = ref(null)

const BILLING_SETTINGS_CACHE_KEY = 'wb-billing-settings-v2'
const GENERAL_SETTINGS_CACHE_KEY = 'wb-general-settings-v1'
const BILLING_SETTINGS_TTL = 30 * 60 * 1000 // 30 mins

// ==================== SYSTEM PERFORMANCE ====================
const showSystemPerformance = ref(false)

// ==================== GENERAL SETTINGS ====================
const showGeneralSettings = ref(false)

const defaultSeries = ref(localStorage.getItem('wb-series') || '')
const defaultWarehouse = ref(localStorage.getItem('wb-warehouse') || '')

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

async function syncSettings() {
  localStorage.removeItem(BILLING_SETTINGS_CACHE_KEY)
  localStorage.removeItem(GENERAL_SETTINGS_CACHE_KEY)
  await fetchSettings()
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
    const cacheValid = cached &&
      (Date.now() - cached.ts) < BILLING_SETTINGS_TTL &&
      cached.data?._current_user === session.user.value
    if (cacheValid) {
      settings = cached.data
    } else {
      settings = await dashboardApi.getBillingSettings()
      if (settings) {
        const settingsWithUser = { ...settings, _current_user: session.user.value }
        localStorage.setItem(BILLING_SETTINGS_CACHE_KEY, JSON.stringify({ data: settingsWithUser, ts: Date.now() }))
        localStorage.setItem(GENERAL_SETTINGS_CACHE_KEY, JSON.stringify({ data: settingsWithUser, ts: Date.now() }))
      }
    }
    
    systemSettings.value = settings
    // Sync user's zoom to localStorage so Sales Entry can use it
    if (settings && settings.user_zoom) {
      localStorage.setItem('wb-zoom', settings.user_zoom)
    }
    if (settings && settings.cipher_map) {
      localStorage.setItem('wb-cipher', settings.cipher_map)
    }
  } catch (e) {
    console.warn('[Dashboard] getBillingSettings failed:', e)
  }

  // 3. Sync today's opening box cash
  try {
    const today = new Date().toLocaleDateString('en-CA')
    const openingRes = await frappeGet('ssplbilling.api.cahierlog_api.get_opening_total', { date: today })
    if (openingRes) {
      const boxCash = String(openingRes.total || 0)
      localStorage.setItem('opening_cash', boxCash)
      localStorage.setItem('wb-opening-box-cash', boxCash)
    }
  } catch (e) {
    console.warn('[Dashboard] opening box cash sync failed:', e)
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

const filteredUserSeries = computed(() => {
  const all = systemSettings.value?.user_series || []
  const user = currentUser.value
  if (user === 'Administrator' || user === 'admin') return all
  return all.filter(us => us.user === user)
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

<style scoped>
.pop-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.pop-leave-active {
  transition: all 0.2s ease-in;
}
.pop-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}
.pop-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
