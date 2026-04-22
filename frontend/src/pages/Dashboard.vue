<template>
  <div class="flex min-h-screen bg-[var(--color-bg)]">

    <!-- ===================== SIDEBAR ===================== -->
    <aside class="flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
      <!-- Logo -->
      <div class="border-b border-[var(--color-border)] px-4 py-4">
        <div class="text-lg font-bold text-[var(--color-text)]">Wholesale<span class="font-light text-[var(--color-text-muted)]">Billing</span></div>
        <div class="mt-0.5 text-xs text-[var(--color-text-muted)]">Fast Billing System</div>
      </div>

      <!-- User -->
      <div class="border-b border-[var(--color-border)] px-4 py-3">
        <div class="flex items-center gap-2">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-highlight)] text-sm font-bold text-[var(--color-text-on-highlight)]">
            {{ userInitials }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-base font-semibold text-[var(--color-text)]">{{ session.fullName.value || 'User' }}</div>
            <div class="flex items-center gap-1.5">
              <span class="truncate text-xs text-[var(--color-text-muted)]">{{ session.user.value }}</span>
              <span class="shrink-0 rounded px-1 py-0.5 text-[10px] font-bold uppercase tracking-wider"
                :class="{
                  'bg-[var(--color-warning)]/20 text-[var(--color-warning)]': userRole === 'admin',
                  'bg-[var(--color-info)]/20 text-[var(--color-info)]': userRole === 'cashier',
                  'bg-[var(--color-success)]/20 text-[var(--color-success)]': userRole === 'biller',
                }"
              >{{ userRole }}</span>
            </div>
          </div>
          <button
            @click="handleFullSync"
            :disabled="isSyncing"
            class="flex items-center justify-center rounded bg-[var(--color-surface-raised)] p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition-colors disabled:opacity-50"
            title="Sync Settings"
          >
            <svg class="h-4 w-4" :class="{'animate-spin text-[var(--color-info)]': isSyncing}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-3 overflow-y-auto">
        <!-- Admin: Inherit User Settings -->
        <div v-if="isActualAdmin" class="mb-6 px-2">
          <label class="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
            Inherit Settings
          </label>
          <div class="relative group">
            <select
              v-model="selectedUser"
              @change="handleUserChange"
              class="w-full appearance-none rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-highlight)] focus:outline-none focus:ring-1 focus:ring-[var(--color-highlight)] transition-all hover:bg-[var(--color-midlight)]"
            >
              <option :value="session.user.value">Me ({{ session.fullName.value }})</option>
              <option v-for="u in allUsers" :key="u.value" :value="u.value">
                {{ u.label }}
              </option>
            </select>
            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-[var(--color-text-muted)]">
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
          <div v-if="selectedUser !== session.user.value" class="mt-1.5 flex items-center gap-1.5 px-1">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-warning)] opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-warning)]"></span>
            </span>
            <span class="text-xs font-medium text-[var(--color-warning)]/90 italic">Previewing User Mode</span>
          </div>
        </div>

        <div class="mb-2 px-2 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Menu</div>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg bg-[var(--color-highlight)] px-3 py-2 text-left text-base font-semibold text-[var(--color-text-on-highlight)]"
        >
          🏠 Dashboard
        </button>
      </nav>

      <!-- Settings section -->
      <div class="border-t border-[var(--color-border)] px-3 py-3">
        <div class="mb-2 px-2 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Settings</div>

        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="handleToggleTheme"
        >
          <span v-if="theme === 'light'">☀️</span>
          <span v-else>🌙</span>
          <span>Toggle Theme</span>
        </button>

        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="showSystemPerformance = true"
        >
          📊 System Performance
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="showGeneralSettings = true"
        >
          ⚙️ General
        </button>
        <button
          v-if="userRole === 'admin'"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="router.push('/ssplbillingsettings')"
        >
          ⚙️ SSPL Settings
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-danger)] hover:bg-[var(--color-midlight)]"
          @click="handleLogout"
        >
          🚪 Logout
        </button>
      </div>
    </aside>

    <!-- ===================== MAIN CONTENT ===================== -->
    <main class="flex-1">
      <!-- Top Bar -->
      <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-lg font-bold text-[var(--color-text)]">Dashboard</h1>
            <p class="text-[10px] text-[var(--color-text-muted)] font-medium uppercase tracking-wider">{{ todayDate }} | {{ todayDay }}</p>
          </div>
        </div>
      </header>

      <div class="flex flex-row items-start justify-between gap-8 px-10 py-10">
        <!-- Left: Bucketed Tiles -->
        <div class="flex-shrink-0 space-y-4">
          <template v-for="bucket in BUCKETS" :key="bucket.id">
            <div v-if="tilesInBucket(bucket.id).length > 0">
              <!-- Bucket Label -->
              <div class="mb-1.5 flex items-center gap-2">
                <span class="text-[9px] font-black uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{{ bucket.label }}</span>
                <div class="h-px flex-1 bg-[var(--color-border)]"></div>
              </div>
              <!-- Tile Grid -->
              <div class="grid grid-cols-3 gap-2">
                <div
                  v-for="tile in tilesInBucket(bucket.id)"
                  :key="tile.id"
                  class="group relative cursor-pointer flex items-center gap-3 rounded-lg px-3 transition-all duration-200 hover:translate-x-1 hover:shadow-md hover:brightness-110 bg-[var(--color-midlight)]"
                  :style="{ width: '70mm', height: '15mm' }"
                  @click="openModule(tile.id)"
                >
                  <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-black/5 text-lg">
                    {{ tile.icon }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-2xl font-normal truncate text-[var(--color-text)]">{{ tile.name }}</div>
                    <div class="text-[9px] truncate text-[var(--color-text)] opacity-60">{{ tile.desc }}</div>
                  </div>
                  <span v-if="tile.shortcut" class="shrink-0 rounded bg-black/10 px-1.5 py-0.5 font-mono text-[10px] font-black text-[var(--color-text)] opacity-70">
                    {{ tile.shortcut }}
                  </span>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Right: Clock (unchanged) -->
        <div class="flex-shrink-0 flex flex-col items-center gap-1 pt-2 bg-[var(--color-surface)] p-6 rounded-3xl border border-[var(--color-border)] backdrop-blur-sm shadow-xl">
          <div class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-[0.2em]">{{ todayDate }}</div>
          <div class="text-lg font-black text-[var(--color-text)] uppercase tracking-wider mb-2 drop-shadow-sm">{{ todayDay }}</div>
          <AnalogueClock />
        </div>
      </div>

      <div class="mx-auto max-w-4xl px-6 pb-12">
        <div class="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-[var(--color-text-muted)]">
          <span class="flex items-center gap-1.5">
            Press <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] font-semibold text-[var(--color-text)]">F1</kbd> – <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] font-semibold text-[var(--color-text)]">F10</kbd>
            to quick open
          </span>
          <span class="text-[var(--color-lowlight)]">|</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] font-semibold text-[var(--color-text)]">Ctrl+L</kbd> Customer</span>
          <span class="text-[var(--color-lowlight)]">|</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] font-semibold text-[var(--color-text)]">Ctrl+I</kbd> Item Search</span>
          <span class="text-[var(--color-lowlight)]">|</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] font-semibold text-[var(--color-text)]">Ctrl+R</kbd> Stock Reconcile</span>
          <span class="text-[var(--color-lowlight)]">|</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] font-semibold text-[var(--color-text)]">ESC</kbd> Close Modals</span>
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

    <!-- OUTSTANDING BILLS MODAL -->
    <OutstandingBillsModal
      :show="showOutstandingBillsModal"
      :party="outstandingParty"
      :party-type="outstandingPartyType"
      :entered-amount="0"
      @close="showOutstandingBillsModal = false"
    />

    <!-- INVOICE TEMPLATE FULL SCREEN MODAL -->
    <div v-if="showInvoiceTemplate" class="fixed inset-0 z-[100] bg-[var(--color-bg)]">
      <Item_Invoice_Template
        title="Template Preview"
        doc-number="INV-TEMP-001"
        party-name="Sample Customer"
        party-details="123 Main Street, Sample City"
        party-address="123 Main Street, Sample City"
        party-mobile="9876543210"
        party-gstin="22AAAAA0000A1Z5"
        :party-balance="1250.50"
        party-last-inv-date="05-Apr-26"
        doc-date="06-Apr-2026"
        sidebar-date="06-04-2026"
        sidebar-search=""
        :sidebar-series="['ALL']"
        :available-series="['ALL', 'RETL', 'WHSL']"
        :draft-only="true"
        :sidebar-items="[
          { name: 'INV-TEMP-001', grand_total: '2250', customer_name: 'Sample Customer', docstatus: 0 },
          { name: 'INV-TEMP-002', grand_total: '1500', customer_name: 'John Doe', docstatus: 1 }
        ]"
        selected-sidebar-item-name="INV-TEMP-001"
        :items="[
          { item_code: 'ITEM001', item_name: 'Sample Item 1', qty: 10, rate: 100, amount: 1000 },
          { item_code: 'ITEM002', item_name: 'Sample Item 2', qty: 5, rate: 250, amount: 1250 }
        ]"
        subtotal="2250.00"
        total-tax="0.00"
        total-amount="2250.00"
        price-list="Standard Selling"
        tax-template="GST 18% (Inclusive)"
        :is-inclusive-tax="true"
        :ignore-discount-rule="false"
        :is-return="false"
        warehouse="Main Warehouse"
        cost-center="Main Cost Center"
        @back="showInvoiceTemplate = false"
        @save="showInvoiceTemplate = false"
        @print="showInvoiceTemplate = false"
      >
        <template #header-right>
          <span>Sample Header Extra Info</span>
        </template>
        <template #bottom-left>
          <div class="p-4 text-[var(--color-text-muted)]">Sample Insights Content</div>
        </template>
        <template #bottom-middle>
          <div class="p-4 text-[var(--color-text-muted)]">Sample Settings Content</div>
        </template>
      </Item_Invoice_Template>
    </div>

    <!-- STOCK TEMPLATE FULL SCREEN MODAL -->
    <div v-if="showStockTemplate" class="fixed inset-0 z-[100] bg-[var(--color-bg)]">
      <Stock_Template
        title="Stock Template Preview"
        doc-number="ST-TEMP-001"
        party-name="Main Warehouse -> Store"
        doc-date="06-Apr-2026"
        sidebar-date="06-04-2026"
        sidebar-search=""
        :sidebar-series="['ST']"
        :available-series="['ST', 'MAT']"
        :draft-only="true"
        :sidebar-items="[
          { name: 'ST-TEMP-001', total_qty: '150', posting_date: '2026-04-06', docstatus: 0 },
          { name: 'ST-TEMP-002', total_qty: '45', posting_date: '2026-04-05', docstatus: 1 }
        ]"
        selected-sidebar-item-name="ST-TEMP-001"
        :items="[
          { item_code: 'ITEM001', item_name: 'Sample Item 1', qty: 100, uom: 'Nos', rate: 10 },
          { item_code: 'ITEM002', item_name: 'Sample Item 2', qty: 50, uom: 'Kg', rate: 25 }
        ]"
        total-amount="2250.00"
        total-label="Total Value"
        item-count="2"
        warehouse="Main Warehouse"
        save-button-text="Save"
        :is-read-only="false"
        :is-draft="true"
        @back="showStockTemplate = false"
        @save="showStockTemplate = false"
        @cancel="showStockTemplate = false"
      />
    </div>

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
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import Stock_Template from '../components/Stock_Template.vue'
import OutstandingBillsModal from '../components/OutstandingBillsModal.vue'
import { fetchItemPrice, fetchItemStockForWarehouses, frappeGet } from '../api.js'
import { searchCustomers } from '../customersearch.js'
import { createCustomer, updateCustomer } from '../api/customer.js'
import { useItemCache } from '../services/itemCache.js'
import { useLedgerCache } from '../services/ledgerCache.js'
import { useShortcuts, useSubwindowWatcher } from '../services/shortcutManager'
import { canAccessTile, canAccessRoute, getUserRole } from '../composables/usePermission'
import { dashboardShortcuts } from '../shortcuts/dashboardShortcuts'
import { useTheme } from '../composables/useTheme'

const router = useRouter()

const { refreshItemCache } = useItemCache()
const { refreshLedgerCache } = useLedgerCache()
const { user: currentUser } = session

// ==================== PERMISSIONS & ROLES ====================
const permissionTrigger = ref(0)
const userRole = computed(() => {
  permissionTrigger.value
  return getUserRole()
})
const isBiller = computed(() => userRole.value === 'biller')
const isActualAdmin = computed(() => ['Administrator', 'admin'].includes(session.user.value))

// ==================== THEME ====================
const { theme, toggleTheme, applyTheme } = useTheme()

function handleToggleTheme() {
  toggleTheme()
}

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

const BUCKETS = [
  { id: 'sale',     label: 'Sale' },
  { id: 'purchase', label: 'Purchase' },
  { id: 'accounts', label: 'Accounts' },
  { id: 'ledger',   label: 'Ledger View' },
  { id: 'sspl',     label: 'SSPL Special' },
  { id: 'report',   label: 'Report' },
]

const allTiles = [
  // ── Sale ──
  { id: 'sales',              bucket: 'sale',     name: 'Sales Invoice',         desc: 'Create sales invoices',                    icon: '🧾', shortcut: 'F1'  },
  { id: 'quotation',          bucket: 'sale',     name: 'Quotation',             desc: 'Create quotations',                        icon: '📄', shortcut: 'F10' },
  { id: 'cashier',            bucket: 'sale',     name: 'Cashier Desk',          desc: 'Modern payment desk',                      icon: '🏧', shortcut: 'F5'  },
  { id: 'sales-order',        bucket: 'sale',     name: 'Sales Order',           desc: 'Create & manage sales orders',             icon: '📝', shortcut: ''    },
  { id: 'Cashier-Management', bucket: 'sale',     name: 'Cashier Management',    desc: 'Daily reconciliation & denominations',     icon: '📓', shortcut: ''    },
  { id: 'cancellation',       bucket: 'sale',     name: 'Cancellation',          desc: 'Cancel & amend submitted bills',           icon: '🚫', shortcut: ''    },
  // ── Purchase ──
  { id: 'purchase-invoice',   bucket: 'purchase', name: 'Purchase Invoice',      desc: 'Fast purchase invoice entry',              icon: '🧾', shortcut: ''    },
  { id: 'purchase-order',     bucket: 'purchase', name: 'Purchase Order',        desc: 'Create & manage purchase orders',          icon: '📋', shortcut: 'F7'  },
  { id: 'purchase-submit',    bucket: 'purchase', name: 'Purchase Desk',         desc: 'Confirm & submit purchases',               icon: '📥', shortcut: 'F4'  },
  // ── Accounts ──
  { id: 'single-entry',       bucket: 'accounts', name: 'Bulk Payment',          desc: 'Fast bulk payment entries',                icon: '🧾', shortcut: ''    },
  { id: 'payment',            bucket: 'accounts', name: 'Payment Receipt',       desc: 'Accounts payment & receipt entry',         icon: '💸', shortcut: 'F3'  },
  { id: 'journal-contra',     bucket: 'accounts', name: 'Journal Contra',        desc: 'General ledger entries',                   icon: '📒', shortcut: 'F8'  },
  { id: 'outstanding-bills',  bucket: 'accounts', name: 'Outstanding',           desc: 'View party outstanding bills',             icon: '📋', shortcut: ''    },
  // ── Ledger View ──
  { id: 'stock-ledger',       bucket: 'ledger',   name: 'Stock',                 desc: 'View stock movement by item',              icon: '📦', shortcut: ''    },
  { id: 'ledger',             bucket: 'ledger',   name: 'Customer Ledger',       desc: 'View customer account history',            icon: '📋', shortcut: 'F6'  },
  { id: 'gst-ledger',         bucket: 'ledger',   name: 'GST Ledger',            desc: 'View GST Quotation ledger',                icon: '📜', shortcut: ''    },
  { id: 'incentive-ledger',   bucket: 'ledger',   name: 'Incentive Ledger',      desc: 'Employee incentives',                      icon: '🏆', shortcut: ''    },
  { id: 'general-ledger',    bucket: 'ledger',   name: 'General Ledger',        desc: 'GL ledger via ERPNext report engine',       icon: '📒', shortcut: ''    },
  // ── SSPL Special ──
  { id: 'loading-receipt',    bucket: 'sspl',     name: 'Loading Receipt',       desc: 'Generate loading receipts',                icon: '🚚', shortcut: ''    },
  { id: 'parcel-address',     bucket: 'sspl',     name: 'Parcel Address',        desc: 'Manage parcel addresses',                  icon: '📦', shortcut: ''    },
  { id: 'gst-dummy-ledger',   bucket: 'sspl',     name: 'WGB PAYMENTS',          desc: 'Manage WGB payment entries',               icon: '📖', shortcut: ''    },
  { id: 'pricing-rules',      bucket: 'sspl',     name: 'Pricing Rule',          desc: 'Sync & manage pricing rules',              icon: '🏷️', shortcut: ''    },
  { id: 'stock-reconciliation', bucket: 'sspl',   name: 'Stock Reconciliation',  desc: 'Adjust stock levels',                      icon: '⚖️', shortcut: ''    },
  { id: 'store-transfer',     bucket: 'sspl',   name: 'Store Transfer',        desc: 'Transfer stock between warehouses',        icon: '🔄', shortcut: 'F9'  },
  { id: 'barcode-print',      bucket: 'sspl',   name: 'Print Barcodes',        desc: 'Print item barcodes',                      icon: '🔖', shortcut: ''    },
  { id: 'invoice-template',   bucket: 'sspl',     name: 'Invoice Template',      desc: 'Reusable invoice UI template',             icon: '🎨', shortcut: ''    },
  { id: 'stock-template',     bucket: 'sspl',     name: 'Stock Template',        desc: 'Reusable stock UI template',               icon: '📦', shortcut: ''    },
  // ── Report ──
  { id: 'daily-report',       bucket: 'report',   name: 'Daily Report',          desc: 'Daily operations summary',                 icon: '📊', shortcut: ''    },
  { id: 'reports',            bucket: 'report',   name: 'Reports',               desc: 'Business reports and analytics',           icon: '📈', shortcut: ''    },
]

const tiles = computed(() => {
  permissionTrigger.value
  return allTiles.filter(t => canAccessTile(t.id))
})

function tilesInBucket(bucketId) {
  return tiles.value.filter(t => t.bucket === bucketId)
}

const readyModules = ['sales', 'quotation', 'purchase-invoice', 'cashier', 'purchase-submit', 'ledger', 'purchase-order', 'sales-order', 'journal-contra', 'stock-reconciliation', 'reports', 'gst-dummy-ledger', 'gst-ledger', 'pricing-rules', 'barcode-print', 'incentive-ledger', 'loading-receipt', 'daily-report', 'parcel-address', 'stock-ledger', 'general-ledger', 'single-entry', 'cancellation']

// payment/receipt/journal/contra are aliases into the PaymentReceiptEntry page
const routeAliases = {
  sales: '/sales',
  quotation: '/quotation',
  'purchase-invoice': '/purchase-invoice',
  payment: '/payment',
  'purchase-order': '/purchase-order',
  'sales-order': '/sales-order',
  'journal-contra': '/journal-contra',
  'stock-reconciliation': '/stock-reconciliation',
  'gst-dummy-ledger': '/gst-dummy-ledger',
  'gst-ledger': '/gst-ledger',
  'Cashier-Management': '/Cashier-Management',
  'pricing-rules': '/pricing-rules',
  'barcode-print': '/barcode-print',
  'incentive-ledger': '/incentive-ledger',
  'loading-receipt': '/loading-receipt',
  'daily-report': '/daily-report',
  'parcel-address': '/parcel-address',
  'store-transfer': '/store-transfer',
  'general-ledger': '/general-ledger',
  reports: '/reports',
  cancellation: '/cancellation',
}

function openModule(id) {
  if (id === 'invoice-template') {
    showInvoiceTemplate.value = true
    return
  }
  if (id === 'stock-template') {
    showStockTemplate.value = true
    return
  }
  if (id === 'stock-ledger') {
    openItemSearch()
    return
  }
  if (id === 'outstanding-bills') {
    searchPurpose.value = 'outstanding'
    openCustomerSearch('All')
    return
  }
  if (id === 'ledger') {
    searchPurpose.value = 'ledger'
    openCustomerSearch('All')
    return
  }
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
  F1: 'sales', F2: 'purchase-invoice', F3: 'payment',
  F4: 'purchase-submit', F5: 'cashier', F6: 'ledger',
  F7: 'purchase-order', F8: 'journal-contra', F9: 'store-transfer',
  F10: 'quotation',
}

// ==================== KEYBOARD SHORTCUTS ====================
useShortcuts(dashboardShortcuts({
  openModule,
  openCustomerSearch: () => {
    if (!isBiller.value) {
      searchPurpose.value = 'ledger'
      openCustomerSearch('All')
    }
  },
  openItemSearch: () => openItemSearch(),
  handleEscape: () => {
    if (showGeneralSettings.value) { showGeneralSettings.value = false; return }
    if (showCustomerSearchModal.value) { closeCustomerSearchModal(); return }
    if (showItemSearchModal.value) { showItemSearchModal.value = false; return }
    if (showLedgerWindow.value) { showLedgerWindow.value = false; return }
    if (showStockLedgerWindow.value) { showStockLedgerWindow.value = false; return }
    if (showInvoiceTemplate.value) { showInvoiceTemplate.value = false; return }
    if (showStockTemplate.value) { showStockTemplate.value = false; return }
    if (showOutstandingBillsModal.value) { showOutstandingBillsModal.value = false; return }
  }
}))

const availableSeries = ref([])
const userAllowedString = ref('')
const systemSettings = ref(null)

const SETTINGS_CACHE_KEY = 'wb-settings-v2'
const BILLING_SETTINGS_TTL = 30 * 60 * 1000 // 30 mins

const showInvoiceTemplate = ref(false)
const showStockTemplate = ref(false)

// ==================== SYSTEM PERFORMANCE ====================
const showSystemPerformance = ref(false)

// ==================== GENERAL SETTINGS ====================
const showGeneralSettings = ref(false)
const generalSettingsRef = ref(null)
const isSyncing = ref(false)

// ==================== SEARCH CONTEXT ====================
const searchPurpose = ref('ledger') // 'ledger' or 'outstanding'

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
const showOutstandingBillsModal = ref(false)
const outstandingParty = ref('')
const outstandingPartyType = ref('')
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

async function pickCust(item, dates) {
  showCustomerSearchModal.value = false
  if (searchPurpose.value === 'outstanding') {
    try {
      const res = await frappeGet('ssplbilling.api.outstanding_api.get_party_outstanding', {
        party_type: item.type || 'Customer',
        party: item.name,
      })
      
      const hasInvoices = (res.invoices || []).length > 0
      const hasPayments = (res.payment_entries || []).length > 0
      const hasJournals = (res.journal_entries || []).length > 0
      
      if (hasInvoices || hasPayments || hasJournals) {
        outstandingParty.value = item.name
        outstandingPartyType.value = item.type || 'Customer'
        showOutstandingBillsModal.value = true
      } else {
        console.log('No outstanding items found for party:', item.name)
        // Optionally show a toast or message
      }
    } catch (e) {
      console.error('Failed to fetch outstanding items:', e)
    }
    return
  }
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
  localStorage.removeItem(SETTINGS_CACHE_KEY)
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
    const cached = JSON.parse(localStorage.getItem(SETTINGS_CACHE_KEY) || 'null')
    const cacheValid = cached &&
      (Date.now() - cached.ts) < BILLING_SETTINGS_TTL &&
      cached.data?._current_user === targetUser
    if (cacheValid) {
      settings = cached.data
    } else {
      settings = await dashboardApi.getBillingSettings(targetUser)
      if (settings) {
        const settingsWithUser = { ...settings, _current_user: targetUser }
        localStorage.setItem(SETTINGS_CACHE_KEY, JSON.stringify({ data: settingsWithUser, ts: Date.now() }))
      }
    }
    
    systemSettings.value = settings
    // Sync user's zoom to localStorage so Sales Invoice can use it
    if (settings && settings.user_zoom) {
      localStorage.setItem('wb-zoom', settings.user_zoom)
    }
    if (settings && settings.wb_theme) {
      const t = settings.wb_theme.toLowerCase() === 'dark' ? 'dark' : 'light'
      localStorage.setItem('wb-theme', t)
      // Do not call applyTheme() here to avoid overwriting Session_Theme once logged in
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

  // 4. Fetch and store all naming series for the requested DocTypes
  try {
    const seriesMap = await dashboardApi.getAllNamingSeries()
    if (seriesMap) {
      // Store individual lists and a flattened list of all unique prefixes
      const allPrefixes = new Set()
      Object.keys(seriesMap).forEach(dt => {
        const seriesList = seriesMap[dt] || []
        const key = `wb-series-${dt.toLowerCase().replace(/ /g, '-')}`
        localStorage.setItem(key, JSON.stringify(seriesList))
        
        seriesList.forEach(s => {
          const prefix = (s || '').split('.')[0]
          if (prefix) allPrefixes.add(prefix)
        })
      })
      // Flattened array of all unique prefixes as requested
      localStorage.setItem('wb-all-naming-series', JSON.stringify([...allPrefixes]))
    }
  } catch (e) {
    console.warn('[Dashboard] getAllNamingSeries failed:', e)
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

function cleanupOldKeys() {
  const keysToRemove = [
    'wb-general-settings-v1',
    'wb-general-settings-v2',
    'wb-billing-settings-v2'
  ]
  keysToRemove.forEach(k => localStorage.removeItem(k))
}

onMounted(async () => {
  cleanupOldKeys()
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
  refreshLedgerCache()      // Preload ledgers for fast search
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
