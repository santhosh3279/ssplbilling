<template>
  <div class="flex h-full overflow-hidden bg-[var(--color-bg)]">

    <!-- ===================== SIDEBAR ===================== -->
    <aside class="flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
      <!-- Logo -->
      <div class="border-b border-[var(--color-border)] px-4 py-4">
        <div class="text-lg font-bold text-[var(--color-text)]">Wholesale<span class="font-light text-[var(--color-text-muted)]">Billing</span></div>
        <div class="mt-0.5 text-xs text-[var(--color-text-muted)]">Fast Billing System</div>
        
        <!-- MQTT Status -->
        <div 
          v-if="mqttServerInfo && mqttServerInfo.server"
          @click="handleMqttClick"
          class="mt-3.5 flex items-center gap-2 rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-1.5 cursor-pointer hover:bg-[var(--color-midlight)] transition-all duration-200"
          :title="mqttConnecting ? 'Refreshing connection...' : 'Click to refresh connection'"
        >
          <span class="relative flex h-2.5 w-2.5 shrink-0">
            <span :class="[mqttConnected ? 'bg-emerald-500' : 'bg-rose-500']" class="relative inline-flex rounded-full h-2.5 w-2.5"></span>
            <span v-if="mqttConnected || mqttConnecting" :class="[mqttConnecting ? 'bg-blue-400' : 'bg-emerald-400']" class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"></span>
          </span>
          <span class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text)]">
            {{ mqttConnecting ? 'Refreshing...' : (mqttConnected ? 'QR Server Connected' : 'QR Server Disconnected') }}
          </span>
        </div>
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
          @click="handleOpenGstValidator"
        >
          🔍 GST Validation
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
    <main class="flex-1 overflow-y-auto">
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
        doctype="Sales Invoice"
        :sidebar-series="['ALL']"
        :available-series="['ALL', 'RETL', 'WHSL']"
        :draft-only="true"
        :sidebar-items="[
          { name: 'INV-TEMP-001', grand_total: '2250', customer_name: 'Sample Customer', docstatus: 0 },
          { name: 'INV-TEMP-002', grand_total: '1500', customer_name: 'John Doe', docstatus: 1 }
        ]"
        selected-sidebar-item-name="INV-TEMP-001"
        :items="[
          { item_code: 'ITEM001', item_name: 'Sample Item 1', qty: 100, uom: 'Nos', rate: 10, amount: 1000 },
          { item_code: 'ITEM002', item_name: 'Sample Item 2', qty: 50.5, uom: 'Kg', rate: 25, amount: 1262.5 }
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
import GeneralSettings from '../components/GeneralSettings.vue'
import SystemPerformance from '../components/SystemPerformance.vue'
import AnalogueClock from '../components/AnalogueClock.vue'
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import Stock_Template from '../components/Stock_Template.vue'
import { fetchItemPrice, fetchItemStockForWarehouses, frappeGet } from '../api.js'
import { searchCustomers } from '../customersearch.js'
import { createCustomer, updateCustomer } from '../api/customer.js'
import { useItemCache } from '../services/itemCache.js'
import { useLedgerCache } from '../services/ledgerCache.js'
import { useShortcuts, useSubwindowWatcher } from '../services/shortcutManager'
import { canAccessTile, canAccessRoute, getUserRole } from '../composables/usePermission'
import { dashboardShortcuts } from '../shortcuts/dashboardShortcuts'
import { useTheme } from '../composables/useTheme'
import { useMqtt } from '../composables/useMqtt'

const router = useRouter()

const { 
  isConnected: mqttConnected, 
  serverInfo: mqttServerInfo, 
  connectMqtt,
  refreshConnection: refreshMqtt,
  isConnecting: mqttConnecting
} = useMqtt()

async function handleMqttClick() {
  if (mqttConnecting.value) return
  await refreshMqtt()
}


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

function handleOpenGstValidator() {
  window.dispatchEvent(new CustomEvent('wb-open-gst-validator'))
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
const now = ref(new Date())
let timeInterval = null

const todayDate = computed(() => {
  return now.value.toLocaleDateString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })
})

const todayDay = computed(() => {
  return now.value.toLocaleDateString('en-IN', {
    timeZone: 'Asia/Kolkata',
    weekday: 'long'
  })
})


// ==================== TILES ====================

const BUCKETS = [
  { id: 'sale',     label: 'Sale' },
  { id: 'purchase', label: 'Purchase' },
  { id: 'stock',    label: 'Stock' },
  { id: 'accounts', label: 'Accounts' },
  { id: 'ledger',   label: 'Ledger View' },
  { id: 'sspl',     label: 'SSPL Special' },
  { id: 'report',   label: 'Report' },
]

const allTiles = [
  // ── Sale ──
  { id: 'sales',              bucket: 'sale',     name: 'Sales Invoice',         desc: 'Create sales invoices',                    icon: '🧾', shortcut: ''  },
  { id: 'quotation',          bucket: 'sale',     name: 'Quotation',             desc: 'Create quotations',                        icon: '📄', shortcut: 'Shift+F10' },
  { id: 'cashier',            bucket: 'sale',     name: 'Cashier Desk',          desc: 'Modern payment desk',                      icon: '🏧', shortcut: 'Shift+F5'  },
  { id: 'sales-order',        bucket: 'sale',     name: 'Sales Order',           desc: 'Create & manage sales orders',             icon: '📝', shortcut: ''    },
  { id: 'Cashier-Management', bucket: 'sale',     name: 'Cashier Management',    desc: 'Daily reconciliation & denominations',     icon: '📓', shortcut: ''    },
  { id: 'cancellation',       bucket: 'sale',     name: 'Cancellation',          desc: 'Cancel & amend submitted bills',           icon: '🚫', shortcut: ''    },
  // ── Purchase ──
  { id: 'purchase-invoice',   bucket: 'purchase', name: 'Purchase Invoice',      desc: 'Fast purchase invoice entry',              icon: '🧾', shortcut: ''    },
  { id: 'purchase-order',     bucket: 'purchase', name: 'Purchase Order',        desc: 'Create & manage purchase orders',          icon: '📋', shortcut: 'Shift+F7'  },
  { id: 'purchase-submit',    bucket: 'purchase', name: 'Purchase Desk',         desc: 'Confirm & submit purchases',               icon: '📥', shortcut: 'Shift+F4'  },
  // ── Stock ──
  { id: 'stock-reconciliation', bucket: 'stock',  name: 'Stock Reconciliation',  desc: 'Adjust stock levels',                      icon: '⚖️', shortcut: ''    },
  { id: 'store-transfer',     bucket: 'stock',  name: 'Store Transfer',        desc: 'Transfer stock between warehouses',        icon: '🔄', shortcut: 'Shift+F9'  },
  { id: 'repack',             bucket: 'stock',  name: 'Repack Entry',          desc: 'Repack raw items into finished goods',     icon: '📦', shortcut: ''    },
  // ── Accounts ──
  { id: 'single-entry',       bucket: 'accounts', name: 'Bulk Payment',          desc: 'Fast bulk payment entries',                icon: '🧾', shortcut: ''    },
  { id: 'payment',            bucket: 'accounts', name: 'Payment Receipt',       desc: 'Accounts payment & receipt entry',         icon: '💸', shortcut: 'Shift+F3'  },
  { id: 'payment-reconciliation', bucket: 'accounts', name: 'Payment Reconciliation', desc: 'Link payments to invoices', icon: '🤝', shortcut: '' },
  { id: 'expense',            bucket: 'accounts', name: 'Expense Entry',         desc: 'Manage company expenses',                  icon: '💸', shortcut: ''  },
  { id: 'journal-contra',     bucket: 'accounts', name: 'Journal Contra',        desc: 'General ledger entries',                   icon: '📒', shortcut: 'Shift+F8'  },
  { id: 'outstanding-bills',  bucket: 'accounts', name: 'Outstanding',           desc: 'View party outstanding bills',             icon: '📋', shortcut: ''    },
  // ── Ledger View ──
  { id: 'stock-ledger',       bucket: 'ledger',   name: 'Stock',                 desc: 'View stock movement by item',              icon: '📦', shortcut: ''    },
  { id: 'ledger',             bucket: 'ledger',   name: 'Customer Ledger',       desc: 'View customer account history',            icon: '📋', shortcut: 'Shift+F6'  },
  { id: 'gst-ledger',         bucket: 'ledger',   name: 'GST Ledger',            desc: 'View GST Quotation ledger',                icon: '📜', shortcut: ''    },
  { id: 'incentive-ledger',   bucket: 'ledger',   name: 'Incentive Ledger',      desc: 'View employee incentives',                 icon: '🏆', shortcut: ''    },
  { id: 'incentive-redeem',   bucket: 'accounts', name: 'Incentive Redeem',      desc: 'Redeem points for cash',                   icon: '🎁', shortcut: ''    },
  { id: 'general-ledger',    bucket: 'ledger',   name: 'General Ledger',        desc: 'GL ledger via ERPNext report engine',       icon: '📒', shortcut: ''    },
  // ── SSPL Special ──
  { id: 'loading-receipt',    bucket: 'sspl',     name: 'Loading Receipt',       desc: 'Generate loading receipts',                icon: '🚚', shortcut: ''    },
  { id: 'parcel-address',     bucket: 'sspl',     name: 'Parcel Address',        desc: 'Manage parcel addresses',                  icon: '📦', shortcut: ''    },
  { id: 'gst-dummy-ledger',   bucket: 'sspl',     name: 'WGB PAYMENTS',          desc: 'Manage WGB payment entries',               icon: '📖', shortcut: ''    },
  { id: 'pricing-rules',      bucket: 'sspl',     name: 'Discount Rules',        desc: 'Manage discount rules and tiers',          icon: '🏷️', shortcut: ''    },
  { id: 'party-link',         bucket: 'sspl',   name: 'Party Link',            desc: 'Link customers and suppliers',             icon: '🔗', shortcut: ''    },
  { id: 'naming-settings',    bucket: 'sspl',   name: 'Naming Settings',       desc: 'Configure document series',                icon: '🔢', shortcut: ''    },
  { id: 'barcode-print',      bucket: 'sspl',   name: 'Print Barcodes',        desc: 'Print item barcodes',                      icon: '🔖', shortcut: ''    },
  { id: 'catelogue',          bucket: 'sspl',   name: 'Catalogues',            desc: 'View published catalogues',                icon: '📖', shortcut: ''    },
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

const readyModules = ['sales', 'quotation', 'purchase-invoice', 'cashier', 'purchase-submit', 'ledger', 'purchase-order', 'sales-order', 'journal-contra', 'stock-reconciliation', 'reports', 'gst-dummy-ledger', 'gst-ledger', 'pricing-rules', 'barcode-print', 'incentive-ledger', 'loading-receipt', 'daily-report', 'parcel-address', 'stock-ledger', 'general-ledger', 'single-entry', 'cancellation', 'party-link', 'naming-settings', 'expense', 'payment-reconciliation', 'repack', 'offer-display', 'catelogue']

// payment/receipt/journal/contra are aliases into the PaymentReceiptEntry page
const routeAliases = {
  sales: '/sales',
  quotation: '/quotation',
  repack: '/repack',
  'offer-display': '/offer-display',
  'purchase-invoice': '/purchase-invoice',
  payment: '/payment',
  expense: '/expense',
  'purchase-order': '/purchase-order',
  'sales-order': '/sales-order',
  'journal-contra': '/journal-contra',
  'stock-reconciliation': '/stock-reconciliation',
  'gst-dummy-ledger': '/gst-dummy-ledger',
  'gst-ledger': '/gst-ledger',
  'Cashier-Management': '/Cashier-Management',
  'pricing-rules': '/discount-rules',
  'barcode-print': '/barcode-print',
  'incentive-ledger': '/incentive-ledger',
  'incentive-redeem': '/incentive-redeem',
  'loading-receipt': '/loading-receipt',
  'daily-report': '/daily-report',
  'parcel-address': '/parcel-address',
  'store-transfer': '/store-transfer',
  'general-ledger': '/general-ledger',
  reports: '/reports',
  cancellation: '/cancellation',
  'party-link': '/party-link',
  'naming-settings': '/naming-settings',
  catelogue: '/catelogue',
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
  if (id === 'payment-reconciliation') {
    window.open('/app/payment-reconciliation', '_blank')
    return
  }
  if (id === 'stock-ledger') {
    window.dispatchEvent(new CustomEvent('wb-global-item-search'))
    return
  }
  if (id === 'outstanding-bills') {
    window.dispatchEvent(new CustomEvent('wb-global-ledger-search', { detail: { purpose: 'outstanding' } }))
    return
  }
  if (id === 'ledger') {
    window.dispatchEvent(new CustomEvent('wb-global-ledger-search', { detail: { purpose: 'ledger' } }))
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
  'SHIFT+F2': 'purchase-invoice', 'SHIFT+F3': 'payment',
  'SHIFT+F4': 'purchase-submit', 'SHIFT+F5': 'cashier', 'SHIFT+F6': 'ledger',
  'SHIFT+F7': 'purchase-order', 'SHIFT+F8': 'journal-contra', 'SHIFT+F9': 'store-transfer',
  'SHIFT+F10': 'quotation',
}

// ==================== KEYBOARD SHORTCUTS ====================
useShortcuts(dashboardShortcuts({
  openModule,
  handleEscape: () => {
    if (showGeneralSettings.value) { showGeneralSettings.value = false; return }
    if (showInvoiceTemplate.value) { showInvoiceTemplate.value = false; return }
    if (showStockTemplate.value) { showStockTemplate.value = false; return }
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

async function syncSettings() {
  localStorage.removeItem(SETTINGS_CACHE_KEY)
  await fetchSettings(selectedUser.value)
}

async function fetchSettings(user = null, force = false) {
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
    const cacheValid = !force && cached &&
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

    // Set billing defaults from the first visible series row
    const firstSeries = (settings.billing_series || [])[0]
    if (firstSeries) {
      localStorage.setItem('wb-tax-type-incl', firstSeries.tax_type_incl ? '1' : '0')
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
          const val = typeof s === 'string' ? s : (s?.prefix || '')
          const prefix = val.split('.')[0]
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
  window.addEventListener('wb-navigate-home', () => router.push('/'))
  
  if (isActualAdmin.value) {
    try {
      allUsers.value = await dashboardApi.getAllUsers()
    } catch (e) {
      console.warn('[Dashboard] getAllUsers failed:', e)
    }
  }

  fetchSettings(selectedUser.value, true)
  refreshItemCache('Sales') // Preload items for fast entry
  refreshLedgerCache()      // Preload ledgers for fast search
  connectMqtt()

  timeInterval = setInterval(() => {
    now.value = new Date()
  }, 1000)
})
onUnmounted(() => {
  window.removeEventListener('wb-navigate-home', () => router.push('/'))
  if (timeInterval) {
    clearInterval(timeInterval)
  }
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
