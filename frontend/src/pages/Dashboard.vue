<template>
  <div class="flex h-full overflow-hidden bg-[var(--color-bg)]">

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
            <div class="truncate text-base font-semibold text-[var(--color-text)]">
              {{ session.fullName.value || 'User' }}
              <span v-if="selectedUser !== session.user.value" class="text-xs font-normal text-[var(--color-text-muted)]"> ({{ selectedUser }})</span>
            </div>
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
              class="w-full rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-highlight)] focus:outline-none focus:ring-1 focus:ring-[var(--color-highlight)] transition-all hover:bg-[var(--color-midlight)]"
            >
              <option :value="session.user.value">Me ({{ session.fullName.value }})</option>
              <option v-for="u in allUsers" :key="u.value" :value="u.value">
                {{ u.label }}
              </option>
            </select>
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
          @click="currentTab = 'dashboard'"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base font-semibold transition-colors"
          :class="currentTab === 'dashboard' ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-midlight)]'"
        >
          🏠 Dashboard
        </button>
        <button
          v-if="userRole === 'admin'"
          @click="currentTab = 'locked-bills'"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base font-semibold transition-colors"
          :class="currentTab === 'locked-bills' ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-midlight)]'"
        >
          🔐 Locked Bills
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
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)] disabled:opacity-50 transition-colors"
          @click="handleClearRedisCache"
          :disabled="isClearingRedis"
        >
          <span :class="{'animate-spin inline-block': isClearingRedis}">🧹</span>
          <span>{{ isClearingRedis ? 'Clearing Cache...' : 'Clear Redis Cache' }}</span>
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
            <h1 class="text-lg font-bold text-[var(--color-text)]">{{ (currentTab === 'locked-bills' && userRole === 'admin') ? 'Locked Bills' : 'Dashboard' }}</h1>
            <p class="text-[10px] text-[var(--color-text-muted)] font-medium uppercase tracking-wider">{{ todayDate }} | {{ todayDay }}</p>
          </div>
          
          <div class="flex items-center gap-4">
            <span class="text-[var(--color-info)] font-bold uppercase tracking-widest text-xs">
              👤 {{ session.fullName.value || session.user.value }}
              <span v-if="selectedUser !== session.user.value" class="normal-case font-normal text-[var(--color-text-muted)] text-xs"> ({{ selectedUser }})</span>
            </span>
            <!-- Fullscreen button -->
            <button
              @click="toggleFullscreen"
              class="flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-midlight)] transition shadow-sm active:scale-95 focus:outline-none"
              title="Toggle Fullscreen"
            >
              <span>{{ isFullscreen ? '📴 Exit Fullscreen' : '📺 Fullscreen' }}</span>
            </button>
          </div>
        </div>
      </header>

      <div v-if="currentTab === 'dashboard'" class="flex flex-row items-start justify-between gap-8 px-10 py-10">
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

        <!-- Right Column: Clock & MQTT Widgets -->
        <div class="flex-shrink-0 flex flex-col gap-4 w-[280px]">
          <!-- Clock -->
          <div class="flex flex-col items-center gap-1 pt-2 bg-[var(--color-surface)] p-6 rounded-3xl border border-[var(--color-border)] backdrop-blur-sm shadow-xl">
            <div class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-[0.2em]">{{ todayDate }}</div>
            <div class="text-lg font-black text-[var(--color-text)] uppercase tracking-wider mb-2 drop-shadow-sm">{{ todayDay }}</div>
            <AnalogueClock />
          </div>

          <!-- MQTT Server Status -->
          <div class="bg-[var(--color-surface)] p-5 rounded-3xl border border-[var(--color-border)] shadow-xl flex flex-col gap-3">
            <div class="flex items-center justify-between border-b border-[var(--color-border)]/50 pb-2">
              <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-[0.15em]">MQTT Server</span>
              <span class="flex items-center gap-1.5 text-xs font-bold">
                <span
                  class="h-2.5 w-2.5 rounded-full"
                  :class="isConnected ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)] animate-pulse' : 'bg-rose-500'"
                ></span>
                <span :class="isConnected ? 'text-emerald-500' : 'text-rose-500'">
                  {{ isConnected ? 'Connected' : 'Disconnected' }}
                </span>
              </span>
            </div>

            <div class="text-xs space-y-1">
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Broker:</span>
                <span class="font-mono font-bold text-[var(--color-text)] truncate max-w-[160px] text-right" :title="serverInfo.server">{{ serverInfo.server || 'N/A' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Port:</span>
                <span class="font-mono font-bold text-[var(--color-text)]">{{ serverInfo.port || 'N/A' }}</span>
              </div>
            </div>

            <!-- Manual reconnect button -->
            <button
              v-if="!isConnected"
              @click="handleMqttRefresh"
              :disabled="isConnecting"
              class="w-full flex items-center justify-center gap-2 rounded-xl bg-amber-600 hover:bg-amber-700 disabled:opacity-50 px-4 py-2.5 text-xs font-bold text-white transition active:scale-95 border border-amber-500 shadow-md focus:outline-none"
            >
              <span>{{ isConnecting ? '⏳ Connecting...' : '🔄 Reconnect MQTT' }}</span>
            </button>
          </div>

          <!-- Live Sync Status -->
          <div
            class="bg-[var(--color-surface)] p-5 rounded-3xl border shadow-xl flex flex-col gap-3 transition-all duration-500"
            :class="syncFlash ? 'border-emerald-500 shadow-emerald-500/20' : 'border-[var(--color-border)]'"
          >
            <div class="flex items-center justify-between border-b border-[var(--color-border)]/50 pb-2">
              <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-[0.15em]">Live Sync</span>
              <span class="flex items-center gap-1.5 text-xs font-bold">
                <span
                  class="h-2.5 w-2.5 rounded-full"
                  :class="socketConnected ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)] animate-pulse' : 'bg-rose-500'"
                ></span>
                <span :class="socketConnected ? 'text-emerald-500' : 'text-rose-500'">
                  {{ socketConnected ? 'Connected' : 'Offline' }}
                </span>
              </span>
            </div>

            <div class="text-xs space-y-1.5">
              <div class="flex justify-between items-center">
                <span class="text-[var(--color-text-muted)]">Channel:</span>
                <span class="font-mono text-[var(--color-text)] font-bold">Item Cache</span>
              </div>
              <div class="flex justify-between items-start gap-2">
                <span class="text-[var(--color-text-muted)] shrink-0">Last Update:</span>
                <span class="font-mono text-right text-[var(--color-text)]">
                  {{ lastSyncTime || '—' }}
                </span>
              </div>
            </div>

            <!-- Flash banner on update -->
            <div
              v-if="syncFlash"
              class="flex items-center gap-2 rounded-xl bg-emerald-500/15 border border-emerald-500/30 px-3 py-2 text-xs font-bold text-emerald-500"
            >
              <span class="animate-bounce">↻</span>
              Items refreshed
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="currentTab === 'locked-bills' && userRole === 'admin'" class="px-10 py-8">
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-[var(--color-text)]">Locked Bills</h2>
            <p class="text-xs text-[var(--color-text-muted)]">Manage sales invoices currently being edited by users</p>
          </div>
          <button
            @click="fetchLockedBills"
            :disabled="isLoadingLocked"
            class="flex items-center gap-2 rounded-xl bg-[var(--color-highlight)] hover:bg-[var(--color-highlight)]/90 px-4 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] transition active:scale-95 shadow-md disabled:opacity-50"
          >
            <span :class="{'animate-spin inline-block': isLoadingLocked}">🔄</span>
            <span>Refresh</span>
          </button>
        </div>

        <!-- Table Card -->
        <div class="overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
          <div v-if="isLoadingLocked" class="flex flex-col items-center justify-center py-16 gap-3">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-highlight)] border-t-transparent"></div>
            <div class="text-sm text-[var(--color-text-muted)] font-medium">Fetching locked bills...</div>
          </div>
          
          <div v-else-if="lockedBills.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
            <div class="text-5xl mb-4">🔓</div>
            <h3 class="text-lg font-bold text-[var(--color-text)]">No Locked Bills</h3>
            <p class="mt-1 text-sm text-[var(--color-text-muted)] max-w-sm">There are no invoices currently locked for editing by any user.</p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full border-collapse text-left text-sm text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">Bill No</th>
                  <th class="px-6 py-4">Username</th>
                  <th class="px-6 py-4">Full Name</th>
                  <th class="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr
                  v-for="bill in lockedBills"
                  :key="bill.bill_no"
                  class="hover:bg-[var(--color-midlight)]/40 transition-colors"
                >
                  <td class="whitespace-nowrap px-6 py-4 font-mono font-bold text-[var(--color-highlight)] text-base">
                    {{ bill.bill_no }}
                  </td>
                  <td class="whitespace-nowrap px-6 py-4">
                    <span class="rounded bg-[var(--color-surface-raised)] px-2.5 py-1 text-xs font-mono text-[var(--color-text-muted)] border border-[var(--color-border)]">
                      {{ bill.username }}
                    </span>
                  </td>
                  <td class="whitespace-nowrap px-6 py-4 font-medium text-[var(--color-text)]">
                    {{ bill.fullname }}
                  </td>
                  <td class="whitespace-nowrap px-6 py-4 text-right">
                    <button
                      @click="handleForceUnlock(bill.bill_no)"
                      class="inline-flex items-center gap-1.5 rounded-xl border border-[var(--color-danger)]/30 bg-[var(--color-danger)]/10 px-3 py-1.5 text-xs font-bold text-[var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white transition active:scale-95 shadow-sm"
                    >
                      🔓 Force Unlock
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
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

import { fetchItemPrice, fetchItemStockForWarehouses, frappeGet, frappePost } from '../api.js'
import { searchCustomers } from '../customersearch.js'
import { createCustomer, updateCustomer } from '../api/customer.js'
import { useItemCache } from '../services/itemCache.js'
import { useLedgerCache } from '../services/ledgerCache.js'
import { useShortcuts, useSubwindowWatcher } from '../services/shortcutManager'
import { canAccessTile, canAccessRoute, getUserRole } from '../composables/usePermission'
import { dashboardShortcuts } from '../shortcuts/dashboardShortcuts'
import { useTheme } from '../composables/useTheme'
import { useMqtt } from '../composables/useMqtt'
import { getFrappeSocket } from '../services/frappeSocket'

const router = useRouter()

const { isConnected, isConnecting, serverInfo, refreshConnection, checkStatus } = useMqtt()

async function handleMqttRefresh() {
  await refreshConnection()
}

// ==================== LIVE SYNC INDICATOR ====================
const socketConnected = ref(false)
const lastSyncTime = ref('')
const syncFlash = ref(false)
let _flashTimer = null

function _onSocketConnect() { socketConnected.value = true }
function _onSocketDisconnect() { socketConnected.value = false }
function _onItemCacheUpdated() {
  lastSyncTime.value = new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit' })
  syncFlash.value = true
  clearTimeout(_flashTimer)
  _flashTimer = setTimeout(() => { syncFlash.value = false }, 3000)
}

const isFullscreen = ref(false)

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
      .then(() => {
        isFullscreen.value = true
      })
      .catch((err) => {
        console.error(`Error enabling fullscreen: ${err.message}`)
      })
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}




const { items: cachedItems, lastSync: itemsLastSync, refreshItemCache } = useItemCache()
const { ledgers: cachedLedgers, lastSync: ledgersLastSync, refreshLedgerCache } = useLedgerCache()
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

// ==================== KEYBOARD ====================
const isKeyboardVisible = ref(localStorage.getItem('wb-force-keyboard') === 'true')

function handleToggleKeyboard() {
  window.dispatchEvent(new CustomEvent('wb-global-keyboard-toggle'))
}

function syncKeyboardState() {
  isKeyboardVisible.value = localStorage.getItem('wb-force-keyboard') === 'true'
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
  window.location.reload()
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
  { id: 'expense',            bucket: 'accounts', name: 'Cash Box Entry',        desc: 'Manage company expenses',                  icon: '💸', shortcut: ''  },
  { id: 'single-entry',       bucket: 'accounts', name: 'Single Entry',          desc: 'Manage single payment entries',            icon: '🧾', shortcut: ''    },
  { id: 'payment',            bucket: 'accounts', name: 'Payment Receipt',       desc: 'Accounts payment & receipt entry',         icon: '💸', shortcut: 'Shift+F3'  },
  { id: 'unreconciled',       bucket: 'accounts', name: 'Unreconciled Entries',  desc: 'View and reconcile ledger entries',        icon: '🔗', shortcut: ''    },
  { id: 'payment-reconciliation', bucket: 'accounts', name: 'Payment Reconciliation', desc: 'Link payments to invoices', icon: '🤝', shortcut: '' },
  { id: 'journal-contra',     bucket: 'accounts', name: 'Journal Contra',        desc: 'General ledger entries',                   icon: '📒', shortcut: 'Shift+F8'  },
  { id: 'outstanding-bills',  bucket: 'accounts', name: 'Outstanding',           desc: 'View party outstanding bills',             icon: '📋', shortcut: ''    },
  // ── Ledger View ──
  { id: 'stock-ledger',       bucket: 'ledger',   name: 'Stock',                 desc: 'View stock movement by item',              icon: '📦', shortcut: ''    },
  { id: 'ledger',             bucket: 'ledger',   name: 'Customer Ledger',       desc: 'View customer account history',            icon: '📋', shortcut: 'Shift+F6'  },
  { id: 'gst-ledger',         bucket: 'ledger',   name: 'GST Ledger',            desc: 'View GST Quotation ledger',                icon: '📜', shortcut: ''    },
  { id: 'incentive-ledger',   bucket: 'ledger',   name: 'Incentive Ledger',      desc: 'View employee incentives',                 icon: '🏆', shortcut: ''    },
  { id: 'incentive-redeem',   bucket: 'accounts', name: 'Incentive Redeem',      desc: 'Redeem points for cash',                   icon: '🎁', shortcut: ''    },
  { id: 'incentive-entry',    bucket: 'accounts', name: 'Incentive Entry',       desc: 'Create invoice incentive entries',         icon: '🏆', shortcut: ''    },
  { id: 'general-ledger',    bucket: 'ledger',   name: 'General Ledger',        desc: 'GL ledger via ERPNext report engine',       icon: '📒', shortcut: ''    },
  // ── SSPL Special ──
  { id: 'loading-receipt',    bucket: 'sspl',     name: 'Loading Receipt',       desc: 'Generate loading receipts',                icon: '🚚', shortcut: ''    },
  { id: 'parcel-address',     bucket: 'sspl',     name: 'Parcel Address',        desc: 'Manage parcel addresses',                  icon: '📦', shortcut: ''    },
  { id: 'gst-dummy-ledger',   bucket: 'sspl',     name: 'WGB PAYMENTS',          desc: 'Manage WGB payment entries',               icon: '📖', shortcut: ''    },
  { id: 'pricing-rules',      bucket: 'sspl',     name: 'Discount Rules',        desc: 'Manage discount rules and tiers',          icon: '🏷️', shortcut: ''    },
  { id: 'naming-settings',    bucket: 'sspl',   name: 'Naming Settings',       desc: 'Configure document series',                icon: '🔢', shortcut: ''    },
  { id: 'barcode-print',      bucket: 'sspl',   name: 'Print Barcodes',        desc: 'Print item barcodes',                      icon: '🔖', shortcut: ''    },
  { id: 'catelogue',          bucket: 'sspl',   name: 'Catalogues',            desc: 'View published catalogues',                icon: '📖', shortcut: ''    },

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

const readyModules = ['sales', 'quotation', 'purchase-invoice', 'cashier', 'purchase-submit', 'ledger', 'purchase-order', 'sales-order', 'journal-contra', 'stock-reconciliation', 'reports', 'gst-dummy-ledger', 'gst-ledger', 'pricing-rules', 'barcode-print', 'incentive-ledger', 'incentive-redeem', 'incentive-entry', 'loading-receipt', 'daily-report', 'parcel-address', 'stock-ledger', 'general-ledger', 'single-entry', 'cancellation', 'naming-settings', 'expense', 'payment-reconciliation', 'repack', 'offer-display', 'catelogue', 'unreconciled']

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
  'incentive-entry': '/incentive-entry',
  'loading-receipt': '/loading-receipt',
  'daily-report': '/daily-report',
  'parcel-address': '/parcel-address',
  'store-transfer': '/store-transfer',
  'general-ledger': '/general-ledger',
  reports: '/reports',
  cancellation: '/cancellation',
  'naming-settings': '/naming-settings',
  catelogue: '/catelogue',
}

function openModule(id) {

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

  }
}))

const availableSeries = ref([])
const userAllowedString = ref('')
const systemSettings = ref(null)

const SETTINGS_CACHE_KEY = 'wb-settings-v2'
const BILLING_SETTINGS_TTL = 30 * 60 * 1000 // 30 mins
const ALLOWED_SERIES_CACHE_KEY = 'wb-allowed-series-v1'
const NAMING_SERIES_TS_KEY = 'wb-naming-series-ts-v1'
const OPENING_CASH_DATE_KEY = 'wb-opening-box-cash-date'
const GENERIC_CACHE_TTL = 30 * 60 * 1000 // 30 mins — series / naming series
const ITEM_CACHE_TTL = 5 * 60 * 1000 // 5 mins — items / ledgers freshness window



// ==================== SYSTEM PERFORMANCE ====================
const showSystemPerformance = ref(false)

// ==================== GENERAL SETTINGS ====================
const showGeneralSettings = ref(false)
const generalSettingsRef = ref(null)
const isSyncing = ref(false)

// ==================== LOCKED BILLS MANAGEMENT ====================
const currentTab = ref('dashboard')
const lockedBills = ref([])
const isLoadingLocked = ref(false)

async function fetchLockedBills() {
  isLoadingLocked.value = true
  try {
    const res = await frappeGet('ssplbilling.api.salesinvoice_api.get_locked_bills')
    lockedBills.value = res || []
  } catch (err) {
    console.error('Failed to fetch locked bills:', err)
  } finally {
    isLoadingLocked.value = false
  }
}

async function handleForceUnlock(billNo) {
  if (!confirm(`Are you sure you want to force unlock bill ${billNo}?`)) return
  try {
    await frappePost('ssplbilling.api.salesinvoice_api.release_bill_edit', { bill_no: billNo })
    await fetchLockedBills()
  } catch (err) {
    console.error('Failed to release lock:', err)
    alert('Failed to release lock.')
  }
}

watch(currentTab, (newTab) => {
  if (newTab === 'locked-bills') {
    fetchLockedBills()
  }
})


// ==================== REDIS CACHE MANAGEMENT ====================
const isClearingRedis = ref(false)

async function handleClearRedisCache() {
  if (isClearingRedis.value) return
  isClearingRedis.value = true
  try {
    const res = await dashboardApi.clearDraftInvoiceCache()
    if (res?.status === 'success') {
      alert(`Success: Redis stock cache cleared & rebuilt successfully (${res.count} items cached).`)
      await refreshItemCache('Sales', null, defaultWarehouse.value || null)
    } else {
      alert('Failed to clear Redis cache: ' + (res?.message || 'Unknown error'))
    }
  } catch (e) {
    console.error('[Dashboard] clearDraftInvoiceCache failed:', e)
    alert('Failed to clear Redis cache: ' + e.message)
  } finally {
    isClearingRedis.value = false
  }
}

async function handleFullSync() {
  if (isSyncing.value) return
  isSyncing.value = true
  try {
    await syncSettings()
    if (generalSettingsRef.value?.loadSettings) {
      await generalSettingsRef.value.loadSettings()
    }
    window.location.reload()
  } finally {
    isSyncing.value = false
  }
}

const defaultSeries = ref(localStorage.getItem('wb-series') || '')
const defaultWarehouse = ref(localStorage.getItem('wb-warehouse') || '')

async function syncSettings() {
  localStorage.removeItem(SETTINGS_CACHE_KEY)
  // force=true bypasses the series / opening-cash / naming-series caches too.
  await fetchSettings(selectedUser.value, true)
}

async function fetchSettings(user = null, force = false) {
  const targetUser = user || session.user.value
  // 1. Fetch allowed series for this user — cached per user with TTL.
  //    Always rehydrate reactive state (even on cache hit) so a page reload
  //    doesn't leave the series dropdown empty.
  try {
    let d = null
    const cached = JSON.parse(localStorage.getItem(ALLOWED_SERIES_CACHE_KEY) || 'null')
    const cacheValid = !force && cached && cached.user === targetUser &&
      (Date.now() - cached.ts) < GENERIC_CACHE_TTL
    if (cacheValid) {
      d = cached.data
    } else {
      d = await dashboardApi.getAllowedSeries(targetUser)
      localStorage.setItem(ALLOWED_SERIES_CACHE_KEY, JSON.stringify({ data: d, user: targetUser, ts: Date.now() }))
    }
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

  // 3. Sync today's opening box cash — refetch only once per calendar day
  //    (date-keyed, NOT TTL: a stale value here would show yesterday's opening).
  try {
    const today = new Date().toLocaleDateString('en-CA')
    const haveToday = localStorage.getItem(OPENING_CASH_DATE_KEY) === today &&
      localStorage.getItem('wb-opening-box-cash') != null
    if (force || !haveToday) {
      const openingRes = await frappeGet('ssplbilling.api.cahierlog_api.get_opening_total', { date: today })
      if (openingRes) {
        const boxCash = String(openingRes.total || 0)
        localStorage.setItem('opening_cash', boxCash)
        localStorage.setItem('wb-opening-box-cash', boxCash)
        localStorage.setItem(OPENING_CASH_DATE_KEY, today)
      }
    }
  } catch (e) {
    console.warn('[Dashboard] opening box cash sync failed:', e)
  }

  // 4. Fetch and store all naming series for the requested DocTypes.
  //    Rarely changes → refetch on TTL only; consumers read the wb-series-* LS keys.
  try {
    const ts = Number(localStorage.getItem(NAMING_SERIES_TS_KEY) || 0)
    if (!force && (Date.now() - ts) < GENERIC_CACHE_TTL && localStorage.getItem('wb-all-naming-series')) {
      // Cached naming series still fresh — skip the network call.
    } else {
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
      localStorage.setItem(NAMING_SERIES_TS_KEY, String(Date.now()))
    }
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
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  window.addEventListener('wb-global-keyboard-toggle', syncKeyboardState)
  window.addEventListener('wb-item-cache-updated', _onItemCacheUpdated)

  const socket = getFrappeSocket()
  if (socket) {
    socketConnected.value = socket.connected
    socket.on('connect', _onSocketConnect)
    socket.on('disconnect', _onSocketDisconnect)
  }
  
  if (isActualAdmin.value) {
    try {
      allUsers.value = await dashboardApi.getAllUsers()
    } catch (e) {
      console.warn('[Dashboard] getAllUsers failed:', e)
    }
  }

  // Settings/series/opening-cash/naming-series: fetch only on cache miss/expiry (see fetchSettings)
  fetchSettings(selectedUser.value)
  // Items: skip if already cached this session and still fresh (WebSocket keeps stock live).
  // Seed warehouse-scoped (user's default warehouse) so per-warehouse stock is correct from
  // load and the first Ctrl+I in Sales Entry — same warehouse — needs no re-scope refetch.
  if (!cachedItems.value.length || (Date.now() - itemsLastSync.value) > ITEM_CACHE_TTL) {
    refreshItemCache('Sales', null, defaultWarehouse.value || null) // Preload items for fast entry
  }
  // Ledgers: hydrated from localStorage at module init; refresh only if empty or stale
  if (!cachedLedgers.value.length || (Date.now() - ledgersLastSync.value) > ITEM_CACHE_TTL) {
    refreshLedgerCache()      // Preload ledgers for fast search
  }
  // MQTT is live connection health — don't persist it; poll at most once per browser session
  if (!sessionStorage.getItem('wb-mqtt-checked')) {
    checkStatus()             // Retrieve MQTT server status once on load
    sessionStorage.setItem('wb-mqtt-checked', '1')
  }

  timeInterval = setInterval(() => {
    now.value = new Date()
  }, 1000)
})
onUnmounted(() => {
  window.removeEventListener('wb-navigate-home', () => router.push('/'))
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  window.removeEventListener('wb-global-keyboard-toggle', syncKeyboardState)
  window.removeEventListener('wb-item-cache-updated', _onItemCacheUpdated)
  clearTimeout(_flashTimer)

  const socket = getFrappeSocket()
  if (socket) {
    socket.off('connect', _onSocketConnect)
    socket.off('disconnect', _onSocketDisconnect)
  }
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
