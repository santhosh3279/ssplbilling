<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="$emit('close')">
    <div class="w-[720px] rounded-xl bg-white shadow-2xl">

      <!-- Header -->
      <div class="border-b border-gray-200 px-5 py-4 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="text-sm font-semibold text-gray-700">⚙️ General Settings</div>
          <button 
            @click="showLocalVariables"
            class="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-[10px] font-bold text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
          >
            DEBUG: View Local Variables
          </button>
        </div>
        <div class="flex items-center gap-3">
          <button
            @click="handleSync"
            :disabled="syncing"
            class="text-[10px] font-bold text-blue-600 hover:underline disabled:opacity-50"
          >{{ syncing ? 'SYNCING...' : 'SYNC NOW' }}</button>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">✕</button>
        </div>
      </div>

      <div class="flex max-h-[78vh] flex-col gap-4 overflow-y-auto px-5 py-4">

        <!-- Loading -->
        <div v-if="syncing && !rawSettings" class="py-8 text-center text-xs text-gray-400">Loading settings…</div>

        <template v-if="rawSettings">

          <!-- ── Your Settings ── -->
          <div class="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-blue-400">Your Settings</div>
            <div class="grid grid-cols-2 gap-x-8 gap-y-2 text-xs">
              <div class="flex items-center justify-between">
                <span class="text-gray-500">Default Zoom</span>
                <span class="font-mono font-semibold text-gray-800">{{ rawSettings.user_zoom || '--' }}%</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-500">Cash Account</span>
                <span class="font-medium text-gray-800">{{ rawSettings.user_defaults?.cash || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-500">Card Account</span>
                <span class="font-medium text-gray-800">{{ rawSettings.user_defaults?.card || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-500">Bank Account</span>
                <span class="font-medium text-gray-800">{{ rawSettings.user_defaults?.bank || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-500">UPI Account</span>
                <span class="font-medium text-gray-800">{{ rawSettings.user_defaults?.upi || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-500">Warehouse</span>
                <span class="font-medium text-gray-800">{{ rawSettings.user_defaults?.warehouse || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-500">Cost Center</span>
                <span class="font-medium text-gray-800">{{ rawSettings.user_defaults?.cost_center || '--' }}</span>
              </div>
            </div>
          </div>

          <!-- ── System Configuration ── -->
          <div>
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">System Configuration</div>
            <div class="flex flex-col gap-1.5 rounded-lg border border-gray-100 bg-gray-50 px-4 py-3 text-xs">
              <div class="flex items-center justify-between">
                <span class="text-gray-500">Discount Account</span>
                <span class="font-medium text-gray-700">{{ rawSettings.discount_account || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-500">Freight Account</span>
                <span class="font-medium text-gray-700">{{ rawSettings.freight_account || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-500">Cipher Map</span>
                <span class="font-mono text-gray-700">{{ rawSettings.cipher_map || '--' }}</span>
              </div>
            </div>
          </div>

          <!-- ── Billing Series ── -->
          <div>
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">Billing Series</div>
            <div class="overflow-auto rounded-lg border border-gray-100">
              <table class="w-full text-[10px]">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Series</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Print Format</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Price List</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Tax Template</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="bs in visibleBillingSeries" :key="bs.series" class="border-t border-gray-100 hover:bg-gray-50">
                    <td class="whitespace-nowrap px-2 py-1.5 font-semibold text-gray-800">{{ bs.series || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ bs.print_format || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ bs.price_list || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ bs.tax_template || '--' }}</td>
                  </tr>
                  <tr v-if="!visibleBillingSeries.length">
                    <td colspan="4" class="px-2 py-3 text-center text-gray-400">No billing series configured</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── Printer Settings ── -->
          <div v-if="rawSettings.printer_settings?.length">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">Printer Settings</div>
            <div class="overflow-auto rounded-lg border border-gray-100">
              <table class="w-full text-[10px]">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Printer</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Print Template</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="ps in rawSettings.printer_settings" :key="ps.printer + ps.template" class="border-t border-gray-100 hover:bg-gray-50">
                    <td class="whitespace-nowrap px-2 py-1.5 font-medium text-gray-800">{{ ps.printer || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ ps.template || '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── User Series Permissions ── -->
          <div v-if="visibleUserSeries.length">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">User Series Permissions</div>
            <div class="overflow-auto rounded-lg border border-gray-100">
              <table class="w-full text-[10px]">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">User</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Allowed Series</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-right font-semibold text-gray-400">Zoom</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Cash A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Card A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Bank A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">UPI A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Warehouse</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-gray-400">Cost Center</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="us in visibleUserSeries" :key="us.user" class="border-t border-gray-100 hover:bg-gray-50">
                    <td class="whitespace-nowrap px-2 py-1.5 font-medium text-gray-800">{{ us.user || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 font-mono text-gray-600">{{ us.allowed_series || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-right font-mono text-gray-600">{{ us.zoom_value || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ us.cash || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ us.card || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ us.bank || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ us.upi || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ us.warehouse || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-gray-600">{{ us.cost_center || '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </template>
      </div>

      <!-- Footer -->
      <div class="flex justify-end border-t border-gray-200 px-5 py-3">
        <button
          class="rounded bg-gray-100 px-4 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-200"
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

const props = defineProps({
  show: Boolean,
})

const emit = defineEmits(['close', 'sync'])

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

  // Account Defaults (Resolved using mop_map)
  // wb-*-mop  = Mode of Payment name (e.g. "Cash", "HDFC Card")
  // wb-*      = Resolved GL account  (e.g. "Cash - SSPL")
  const mopMap = settings.mop_map || {}

  if (settings.user_defaults?.cash) {
    const mop = settings.user_defaults.cash
    const acc = mopMap[mop] || mop
    localStorage.setItem('wb-cash-mop', mop)
    localStorage.setItem('wb-cash', acc)
  }
  if (settings.user_defaults?.card) {
    const mop = settings.user_defaults.card
    const acc = mopMap[mop] || mop
    localStorage.setItem('wb-card-mop', mop)
    localStorage.setItem('wb-card', acc)
  }
  if (settings.user_defaults?.bank) {
    const mop = settings.user_defaults.bank
    const acc = mopMap[mop] || mop
    localStorage.setItem('wb-bank-mop', mop)
    localStorage.setItem('wb-bank', acc)
  }
  if (settings.user_defaults?.upi) {
    const mop = settings.user_defaults.upi
    const acc = mopMap[mop] || mop
    localStorage.setItem('wb-upi-mop', mop)
    localStorage.setItem('wb-upi', acc)
  }

  if (settings.user_defaults?.warehouse) {
    localStorage.setItem('wb-warehouse', settings.user_defaults.warehouse)
  }
  if (settings.user_defaults?.cost_center) {
    localStorage.setItem('wb-cost-center', settings.user_defaults.cost_center)
  }
  // Set billing defaults from the first visible series row
  const firstSeries = (settings.billing_series || [])[0]
  if (firstSeries) {
    if (firstSeries.series)      localStorage.setItem('wb-series', firstSeries.series)
    if (firstSeries.price_list)  localStorage.setItem('wb-price-list', firstSeries.price_list)
    if (firstSeries.tax_rate)    localStorage.setItem('wb-tax-rate', String(firstSeries.tax_rate))
  }

  // Save allowed series prefixes for today's bills query (wb-allowed-series = JSON array of prefixes)
  // A naming series "SSPL-SI-.YYYY.-" has prefix "SSPL-SI-" (everything before the first dot)
  const allBillingSeries = settings.billing_series || []
  const currentUser = session.user.value
  const userRow = (settings.user_series || []).find(r => r.user === currentUser)
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
    .map(bs => bs.series.split('.')[0])   // "SSPL-SI-.YYYY.-" → "SSPL-SI-"
    .filter(Boolean)
  if (seriesPrefixes.length) {
    localStorage.setItem('wb-allowed-series', JSON.stringify(seriesPrefixes))
  }
}

async function handleSync() {
  await loadSettings()
  emit('sync')
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
