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
          <button
            @click="handleFullSync"
            :disabled="isSyncing"
            class="flex items-center justify-center rounded bg-slate-700 p-1.5 text-slate-400 hover:bg-slate-600 hover:text-white transition-colors disabled:opacity-50"
            title="Sync Settings"
          >
            <svg class="h-4 w-4" :class="{'animate-spin text-blue-400': isSyncing}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-3 overflow-y-auto">
        <!-- Admin: Inherit User Settings -->
        <div v-if="isActualAdmin" class="mb-6 px-2">
          <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-slate-500">
            Inherit Settings
          </label>
          <div class="relative group">
            <select 
              v-model="selectedUser"
              @change="handleUserChange"
              class="w-full appearance-none rounded-lg bg-slate-700/50 border border-slate-600 px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all hover:bg-slate-700"
            >
              <option :value="session.user.value">Me ({{ session.fullName.value }})</option>
              <option v-for="u in allUsers" :key="u.value" :value="u.value">
                {{ u.label }}
              </option>
            </select>
            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
          <div v-if="selectedUser !== session.user.value" class="mt-1.5 flex items-center gap-1.5 px-1">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
            <span class="text-[10px] font-medium text-amber-400/90 italic">Previewing User Mode</span>
          </div>
        </div>

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
          v-if="canAccessTile('daily-report')"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/daily-report')"
        >
          📊 <span class="font-bold text-white">Daily Report</span>
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="showReconcileWindow = true"
        >
          🔗 <span class="font-bold text-white">Pay Reconcile</span>
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
          v-if="userRole === 'admin'"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700"
          @click="router.push('/ssplbillingsettings')"
        >
          ⚙️ SSPL Settings
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
      ref="generalSettingsRef"
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
    <!-- RECONCILE WINDOW -->
    <ReconcileWindow
      v-if="showReconcileWindow"
      @close="showReconcileWindow = false"
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
import ReconcileWindow from './ReconcileWindow.vue'
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

// ==================== PERMISSIONS & ROLES ====================
const permissionTrigger = ref(0)
const userRole = computed(() => {
  permissionTrigger.value
  return getUserRole()
})
const isBiller = computed(() => userRole.value === 'biller')
const isActualAdmin = computed(() => ['Administrator', 'admin'].includes(session.user.value))

// ==================== USER ====================
const userInitials = computed(() => {
  const name = String(session.fullName.value || session.user.value || 'U')
  return name.split(' ').map(w => w[0] || '').join('').toUpperCase().slice(0, 2) || 'U'
})

const selectedUser = ref(localStorage.getItem('wb-inherited-user') || session.user.value)
const allUsers = ref([])

async function handleUserChange() {
  if (selectedUser.value === session.user.value) {
    localStorage.removeItem('wb-inherited-user')
  } else {
    localStorage.setItem('wb-inherited-user', selectedUser.value)
  }
  await syncSettings()
  permissionTrigger.value++
}

async function handleLogout() {
  localStorage.removeItem('wb-inherited-user')
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
  { id: 'gst-dummy-ledger', name: 'GST Dummy Ledger', desc: 'Manage dummy GST entries', icon: '📖', shortcut: '', tileBg: 'bg-indigo-900' },
  { id: 'gst-ledger', name: 'GST Ledger', desc: 'View GST Quotation ledger', icon: '📜', shortcut: '', tileBg: 'bg-indigo-800' },
  { id: 'sales-order', name: 'Sales Order', desc: 'Create & manage sales orders', icon: '📝', shortcut: '', tileBg: 'bg-orange-600' },
  { id: 'reports', name: 'Reports', desc: 'Business reports and analytics', icon: '📊', shortcut: '', tileBg: 'bg-violet-600' },
]

const tiles = computed(() => {
  permissionTrigger.value
  return allTiles.filter(t => canAccessTile(t.id))
})

const readyModules = ['sales', 'quotation', 'purchase', 'cashier', 'purchase-submit', 'ledger', 'purchase-order', 'sales-order', 'journal-contra', 'material-transfer', 'stock-reconciliation', 'reports', 'gst-dummy-ledger', 'gst-ledger']

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
  'gst-dummy-ledger': '/gst-dummy-ledger',
  'gst-ledger': '/gst-ledger',
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
  openCustomerSearch: () => {
    if (!isBiller.value) openCustomerSearch('All')
  },
  openItemSearch: () => openItemSearch(),
  handleEscape: () => {
    if (showReconcileWindow.value) { showReconcileWindow.value = false; return }
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
const GENERAL_SETTINGS_CACHE_KEY = 'wb-general-settings-v2'
const BILLING_SETTINGS_TTL = 30 * 60 * 1000 // 30 mins

// ==================== RECONCILE ====================
const showReconcileWindow = ref(false)

// ==================== SYSTEM PERFORMANCE ====================
const showSystemPerformance = ref(false)

// ==================== GENERAL SETTINGS ====================
const showGeneralSettings = ref(false)
const generalSettingsRef = ref(null)
const isSyncing = ref(false)

async function handleFullSync() {
  if (isSyncing.value) return
  isSyncing.value = true
  try {
    await syncSettings()
    if (generalSettingsRef.value?.loadSettings) {
      await generalSettingsRef.value.loadSettings()
    }
  } finally {
    isSyncing.value = false
  }
}

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
  await fetchSettings(selectedUser.value)
}

async function fetchSettings(user = null) {
  const targetUser = user || session.user.value
  // 1. Fetch allowed series for this user
  try {
    const d = await dashboardApi.getAllowedSeries(targetUser)
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
      cached.data?._current_user === targetUser
    if (cacheValid) {
      settings = cached.data
    } else {
      settings = await dashboardApi.getBillingSettings(targetUser)
      if (settings) {
        const settingsWithUser = { ...settings, _current_user: targetUser }
        localStorage.setItem(BILLING_SETTINGS_CACHE_KEY, JSON.stringify({ data: settingsWithUser, ts: Date.now() }))
        localStorage.setItem(GENERAL_SETTINGS_CACHE_KEY, JSON.stringify({ data: settingsWithUser, ts: Date.now() }))
      }
    }
    
    systemSettings.value = settings
    // Sync user's zoom to localStorage so Sales Entry can use it
    if (settings && settings.user_zoom) {
      localStorage.setItem('wb-zoom', settings.user_zoom)
    }
    if (settings && settings.wb_theme) {
      localStorage.setItem('wb-theme', settings.wb_theme)
    }
    if (settings && settings.cipher_map) {
      localStorage.setItem('wb-cipher', settings.cipher_map)
    }
    if (settings && settings.tax_paid_on_purchase) {
      localStorage.setItem('wb-tax-paid-on-purchase', settings.tax_paid_on_purchase)
    }

    // Sync roles to localStorage for permission inherited
    if (settings && settings.user_role) {
      const roles = settings.user_role
      localStorage.setItem('wb-role-admin', roles.admin ? '1' : '0')
      localStorage.setItem('wb-role-cashier', roles.cashier ? '1' : '0')
      localStorage.setItem('wb-role-biller', roles.biller ? '1' : '0')
      localStorage.setItem('wb-role-accounts', roles.accounts ? '1' : '0')
    }

    // Sync printer settings to localStorage
    if (settings && settings.user_defaults) {
      const defaults = settings.user_defaults
      if (defaults.default_printer) localStorage.setItem('wb-printer', defaults.default_printer)
      if (defaults.warehouse) {
        localStorage.setItem('wb-warehouse', defaults.warehouse)
        defaultWarehouse.value = defaults.warehouse
      }
      if (defaults.cost_center) localStorage.setItem('wb-cost-center', defaults.cost_center)
      if (defaults.income_account) localStorage.setItem('wb-income-account', defaults.income_account)
    }

    // Printer & Template mapping from settings
    if (settings && settings.printer_settings) {
       localStorage.setItem('wb-printer-templates', JSON.stringify(settings.printer_settings))
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

onMounted(async () => {
  window.addEventListener('wb-global-ledger-search', () => openCustomerSearch('All'))
  window.addEventListener('wb-global-item-search', openItemSearch)
  window.addEventListener('wb-navigate-home', () => router.push('/'))
  
  if (isActualAdmin.value) {
    try {
      allUsers.value = await dashboardApi.getAllUsers()
    } catch (e) {
      console.warn('[Dashboard] getAllUsers failed:', e)
    }
  }

  fetchSettings(selectedUser.value)
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
