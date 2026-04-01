<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="w-[820px] rounded-xl bg-slate-900 border border-slate-700 shadow-2xl">

      <!-- Header -->
      <div class="border-b border-slate-700 px-5 py-4 flex items-center justify-between bg-slate-800">
        <div class="flex items-center gap-4">
          <div class="text-sm font-semibold text-slate-200">⚙️ General Settings</div>
          <button
            @click="showLocalVariables"
            class="rounded-md border border-slate-600 bg-slate-700 px-2 py-1 text-[10px] font-bold text-slate-400 hover:bg-slate-600 hover:text-slate-200 transition-colors"
          >
            DEBUG: View Local Variables
          </button>
        </div>
        <div class="flex items-center gap-3">
          <button
            @click="handleSync"
            :disabled="syncing"
            class="text-[10px] font-bold text-blue-400 hover:underline disabled:opacity-50"
          >{{ syncing ? 'SYNCING...' : 'SYNC NOW' }}</button>
          <button @click="$emit('close')" class="text-slate-500 hover:text-slate-300">✕</button>
        </div>
      </div>

      <div class="flex max-h-[78vh] flex-col gap-4 overflow-y-auto px-5 py-4">

        <!-- Loading -->
        <div v-if="syncing && !rawSettings" class="py-8 text-center text-xs text-slate-500">Loading settings…</div>

        <template v-if="rawSettings">

          <!-- ── Your Settings ── -->
          <div class="rounded-lg border border-blue-800 bg-blue-900/20 px-4 py-3">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-blue-400">Your Settings</div>
            <div class="grid grid-cols-2 gap-x-8 gap-y-2 text-xs">
              <div class="flex items-center justify-between">
                <span class="text-slate-400">Default Zoom</span>
                <span class="font-mono font-semibold text-slate-200">{{ rawSettings.user_zoom || '--' }}%</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-400">Warehouse</span>
                <span class="font-medium text-slate-200">{{ rawSettings.user_defaults?.warehouse || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-400">Cost Center</span>
                <span class="font-medium text-slate-200">{{ rawSettings.user_defaults?.cost_center || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-400">Income Account</span>
                <span class="font-medium text-slate-200">{{ rawSettings.user_defaults?.income_account || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-400">Cash Account</span>
                <span class="font-medium text-slate-200">{{ rawSettings.user_defaults?.cash || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-400">Card Account</span>
                <span class="font-medium text-slate-200">{{ rawSettings.user_defaults?.card || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-400">Bank Account</span>
                <span class="font-medium text-slate-200">{{ rawSettings.user_defaults?.bank || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-400">UPI Account</span>
                <span class="font-medium text-slate-200">{{ rawSettings.user_defaults?.upi || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-400">Default Printer</span>
                <span class="font-medium text-slate-200">{{ rawSettings.user_defaults?.default_printer || '--' }}</span>
              </div>
            </div>
          </div>

          <!-- ── System Configuration ── -->
          <div>
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">System Configuration</div>
            <div class="overflow-auto rounded-lg border border-slate-700">
              <table class="w-full text-xs">
                <thead class="bg-slate-800">
                  <tr>
                    <th class="whitespace-nowrap px-3 py-1.5 text-left font-semibold text-slate-400">Field</th>
                    <th class="whitespace-nowrap px-3 py-1.5 text-left font-semibold text-slate-400">Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-slate-400">Discount Account</td>
                    <td class="px-3 py-1.5 font-medium text-slate-200">{{ rawSettings.discount_account || '--' }}</td>
                  </tr>
                  <tr class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-slate-400">Freight Account</td>
                    <td class="px-3 py-1.5 font-medium text-slate-200">{{ rawSettings.freight_account || '--' }}</td>
                  </tr>
                  <tr class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-slate-400">Tax Paid on Purchase</td>
                    <td class="px-3 py-1.5 font-medium text-slate-200">{{ rawSettings.tax_paid_on_purchase || '--' }}</td>
                  </tr>
                  <tr class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-slate-400">Packing Charge</td>
                    <td class="px-3 py-1.5 font-medium text-slate-200">{{ rawSettings.packing_charge || '--' }}</td>
                  </tr>
                  <tr class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-slate-400">Loading</td>
                    <td class="px-3 py-1.5 font-medium text-slate-200">{{ rawSettings.loading || '--' }}</td>
                  </tr>
                  <tr class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-slate-400">Other Charges</td>
                    <td class="px-3 py-1.5 font-medium text-slate-200">{{ rawSettings.other_charges || '--' }}</td>
                  </tr>
                  <tr class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-slate-400">Cipher Map</td>
                    <td class="px-3 py-1.5 font-mono text-slate-200">{{ rawSettings.cipher_map || '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── Billing Series ── -->
          <div>
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">Billing Series</div>
            <div class="overflow-auto rounded-lg border border-slate-700">
              <table class="w-full text-[10px]">
                <thead class="bg-slate-800">
                  <tr>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Series</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Print Format</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Price List</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Tax Template</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="bs in visibleBillingSeries" :key="bs.series" class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-2 py-1.5 font-semibold text-slate-200">{{ bs.series || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ bs.print_format || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ bs.price_list || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ bs.tax_template || '--' }}</td>
                  </tr>
                  <tr v-if="!visibleBillingSeries.length">
                    <td colspan="4" class="px-2 py-3 text-center text-slate-500">No billing series configured</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── Visible Accounts ── -->
          <div v-if="rawSettings.visible_accounts?.length">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">Visible Accounts</div>
            <div class="overflow-auto rounded-lg border border-slate-700">
              <table class="w-full text-xs">
                <thead class="bg-slate-800">
                  <tr>
                    <th class="whitespace-nowrap px-3 py-1.5 text-left font-semibold text-slate-400">Account</th>
                    <th class="whitespace-nowrap px-3 py-1.5 text-left font-semibold text-slate-400">Display Label</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="va in rawSettings.visible_accounts" :key="va.account" class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-3 py-1.5 font-medium text-slate-200">{{ va.account || '--' }}</td>
                    <td class="px-3 py-1.5 text-slate-400">{{ va.label || '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── Printer Settings ── -->
          <div v-if="visiblePrinterSettings.length">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">Printer Settings</div>
            <div class="overflow-auto rounded-lg border border-slate-700">
              <table class="w-full text-[10px]">
                <thead class="bg-slate-800">
                  <tr>
                    <th v-if="isAdmin" class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">User</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Printer</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Print Template</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="ps in visiblePrinterSettings" :key="ps.user + ps.printer + ps.template" class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td v-if="isAdmin" class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ ps.user || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 font-medium text-slate-200">{{ ps.printer || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ ps.template || '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── User Series Permissions ── -->
          <div v-if="visibleUserSeries.length">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">User Series Permissions</div>
            <div class="overflow-auto rounded-lg border border-slate-700">
              <table class="w-full text-[10px]">
                <thead class="bg-slate-800">
                  <tr>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">User</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Allowed Series</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-right font-semibold text-slate-400">Zoom</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Warehouse</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Cost Center</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Income A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Cash A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Card A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Bank A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">UPI A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-center font-semibold text-slate-400">Admin</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-center font-semibold text-slate-400">Cashier</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-center font-semibold text-slate-400">Biller</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-slate-400">Default Printer</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-center font-semibold text-slate-400">Accounts</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="us in visibleUserSeries" :key="us.user" class="border-t border-slate-700 hover:bg-slate-800/40">
                    <td class="whitespace-nowrap px-2 py-1.5 font-medium text-slate-200">{{ us.user || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 font-mono text-slate-400">{{ us.allowed_series || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-right font-mono text-slate-400">{{ us.zoom_value || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ us.warehouse || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ us.cost_center || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ us.income_account || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ us.cash || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ us.card || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ us.bank || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ us.upi || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-center text-slate-400">{{ us.admin ? '✓' : '' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-center text-slate-400">{{ us.cashier ? '✓' : '' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-center text-slate-400">{{ us.biller ? '✓' : '' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-slate-400">{{ us.default_printer || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-center text-slate-400">{{ us.accounts ? '✓' : '' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </template>
      </div>

      <!-- Footer -->
      <div class="flex justify-end border-t border-slate-700 px-5 py-3 bg-slate-800">
        <button
          class="rounded bg-slate-700 px-4 py-1.5 text-sm font-semibold text-slate-300 hover:bg-slate-600"
          @click="$emit('close')"
        >Close</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { dashboardApi } from '../services/dashboard'
import { session } from '../session.js'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean,
})

const emit = defineEmits(['close'])

useSubwindowWatcher(computed(() => props.show), { ESCAPE: () => emit('close') })

const rawSettings = ref(null)
const syncing = ref(false)

onMounted(() => {
  loadSettings()
})

watch(() => props.show, (val) => {
  if (val) loadSettings()
})

async function loadSettings() {
  syncing.value = true
  try {
    rawSettings.value = await dashboardApi.getBillingSettings()
    applyToLocalStorage(rawSettings.value)
  } catch (e) {
    console.error('[GeneralSettings] getBillingSettings failed:', e)
  } finally {
    syncing.value = false
  }
}

function applyToLocalStorage(settings) {
  if (!settings) return
  if (settings.user_zoom) {
    localStorage.setItem('wb-zoom', String(settings.user_zoom))
  }
  if (settings.discount_account) {
    localStorage.setItem('wb-discount-account', settings.discount_account)
  }
  if (settings.freight_account) {
    localStorage.setItem('wb_freight', settings.freight_account)
  }
  if (settings.packing_charge) {
    localStorage.setItem('wb-packing', settings.packing_charge)
  }
  if (settings.loading) {
    localStorage.setItem('wb-loading', settings.loading)
  }
  if (settings.other_charges) {
    localStorage.setItem('wb-other-charges', settings.other_charges)
  }

  // Visible accounts — global list of GL accounts exposed in the ledger search modal
  const visibleAccountNames = (settings.visible_accounts || [])
    .map(va => va.account)
    .filter(Boolean)
  if (visibleAccountNames.length) {
    localStorage.setItem('wb-visible-accounts', JSON.stringify(visibleAccountNames))
  } else {
    localStorage.removeItem('wb-visible-accounts')
  }

  // User defaults from user_series row
  ;['wb-cash-mop', 'wb-card-mop', 'wb-bank-mop', 'wb-upi-mop'].forEach(k => localStorage.removeItem(k))
  if (settings.user_defaults?.cash)           localStorage.setItem('wb-cash',           settings.user_defaults.cash)
  if (settings.user_defaults?.card)           localStorage.setItem('wb-card',           settings.user_defaults.card)
  if (settings.user_defaults?.bank)           localStorage.setItem('wb-bank',           settings.user_defaults.bank)
  if (settings.user_defaults?.upi)            localStorage.setItem('wb-upi',            settings.user_defaults.upi)
  if (settings.user_defaults?.warehouse)      localStorage.setItem('wb-warehouse',      settings.user_defaults.warehouse)
  if (settings.user_defaults?.cost_center)    localStorage.setItem('wb-cost-center',    settings.user_defaults.cost_center)
  if (settings.user_defaults?.income_account) localStorage.setItem('wb-income-account', settings.user_defaults.income_account)
  if (settings.user_defaults?.default_printer) localStorage.setItem('wb-default-printer', settings.user_defaults.default_printer)

  // Set billing defaults from the first visible series row
  const firstSeries = (settings.billing_series || [])[0]
  if (firstSeries) {
    if (firstSeries.series)     localStorage.setItem('wb-series',     firstSeries.series)
    if (firstSeries.price_list) localStorage.setItem('wb-price-list', firstSeries.price_list)
  }

  // Save allowed series prefixes
  const allBillingSeries = settings.billing_series || []
  const currentUser = session.user.value
  const userRow = (settings.user_series || []).find(r => r.user === currentUser)

  // Role flags from user_series row
  if (userRow) {
    localStorage.setItem('wb-role-admin',    userRow.admin    ? '1' : '0')
    localStorage.setItem('wb-role-cashier',  userRow.cashier  ? '1' : '0')
    localStorage.setItem('wb-role-biller',   userRow.biller   ? '1' : '0')
    localStorage.setItem('wb-role-accounts', userRow.accounts ? '1' : '0')
  }

  let allowedSeries = allBillingSeries
  if (userRow?.allowed_series && userRow.allowed_series.trim().toUpperCase() !== 'ALL') {
    const allowedList = userRow.allowed_series.split(',').map(s => s.trim()).filter(Boolean)
    const getAlpha = s => (s || '').replace(/[^A-Za-z]/g, '')
    const allowedPrefixes = allowedList.map(s => getAlpha(s).slice(0, 3))
    allowedSeries = allBillingSeries.filter(bs =>
      allowedPrefixes.some(p => getAlpha(bs.series).slice(0, 3).startsWith(p))
    )
  }

  const seriesPrefixes = allowedSeries
    .map(bs => bs.series.split('.')[0])
    .filter(Boolean)
  if (seriesPrefixes.length) {
    localStorage.setItem('wb-allowed-series', JSON.stringify(seriesPrefixes))
  }
}

async function handleSync() {
  await loadSettings()
}

function showLocalVariables() {
  const vars = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key.startsWith('wb-') || key.startsWith('wb_')) {
      vars.push(`${key}: ${localStorage.getItem(key)}`)
    }
  }
  vars.sort()
  alert(vars.length > 0 ? vars.join('\n') : 'No local variables found starting with wb-')
}

const currentUser = computed(() => session.user.value)
const isAdmin = computed(() => ['Administrator', 'admin'].includes(currentUser.value))

const currentUserRow = computed(() => {
  if (!rawSettings.value) return null
  return (rawSettings.value.user_series || []).find(r => r.user === currentUser.value) || null
})

const visibleUserSeries = computed(() => {
  if (!rawSettings.value?.user_series) return []
  if (isAdmin.value) return rawSettings.value.user_series
  return currentUserRow.value ? [currentUserRow.value] : []
})

function getAlpha(s) {
  return (s || '').replace(/[^A-Za-z]/g, '')
}

const visiblePrinterSettings = computed(() => {
  if (!rawSettings.value?.printer_settings) return []
  if (isAdmin.value) return rawSettings.value.printer_settings
  return rawSettings.value.printer_settings.filter(ps => ps.user === currentUser.value)
})

const visibleBillingSeries = computed(() => {
  if (!rawSettings.value?.billing_series) return []
  if (isAdmin.value) return rawSettings.value.billing_series
  const row = currentUserRow.value
  if (!row) return rawSettings.value.billing_series
  const allowed = (row.allowed_series || '')
    .split(',').map(s => s.trim()).filter(Boolean)
  if (!allowed.length || allowed.includes('ALL')) return rawSettings.value.billing_series
  const allowedPrefixes = allowed.map(s => getAlpha(s).slice(0, 3))
  return rawSettings.value.billing_series.filter(bs =>
    allowedPrefixes.some(p => getAlpha(bs.series).slice(0, 3).startsWith(p))
  )
})
</script>
