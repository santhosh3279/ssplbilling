<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="$emit('close')">
    <div class="w-[680px] rounded-xl bg-white shadow-2xl">
      <div class="border-b border-gray-200 px-5 py-4 flex items-center justify-between">
        <div class="text-sm font-semibold text-gray-700">⚙️ General Settings</div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">✕</button>
      </div>
      
      <div class="flex max-h-[75vh] flex-col gap-4 overflow-y-auto px-5 py-4">
        <!-- Default Zoom -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold text-gray-500">Default Zoom (%)</label>
          <div class="flex items-center gap-3">
            <input
              type="number"
              v-model.number="localZoom"
              min="50"
              max="300"
              step="10"
              class="w-24 rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
            <span class="text-xs text-gray-400">50 – 300 (current: {{ localZoom }}%)</span>
          </div>
        </div>

        <!-- SSPL Billing Settings Details -->
        <div class="mt-4 border-t border-gray-100 pt-4">
          <div class="mb-3 flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider text-gray-400">System Configuration</span>
            <button
              @click="handleSync"
              :disabled="syncing"
              class="text-[10px] font-bold text-blue-600 hover:underline disabled:opacity-50"
            >{{ syncing ? 'SYNCING...' : 'SYNC NOW' }}</button>
          </div>

          <div v-if="syncing && !rawSettings" class="py-4 text-center text-xs text-gray-400">Loading...</div>

          <template v-if="rawSettings">
            <!-- Discount Account & Cipher Map -->
            <div class="mb-3 flex flex-col gap-1.5">
              <div class="flex justify-between text-xs">
                <span class="text-gray-500">Discount Account</span>
                <span class="font-medium text-gray-700">{{ rawSettings.discount_account || '--' }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-gray-500">Cipher Map</span>
                <span class="font-mono text-gray-700">{{ rawSettings.cipher_map || '--' }}</span>
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
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Printer</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="bs in visibleBillingSeries" :key="bs.series" class="border-t border-gray-100">
                      <td class="whitespace-nowrap px-2 py-1.5 font-medium">{{ bs.series || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.price_list || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.warehouse || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.tax_template || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.cost_center || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.print_format || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ bs.printer || '--' }}</td>
                    </tr>
                    <tr v-if="!visibleBillingSeries.length">
                      <td colspan="7" class="px-2 py-2 text-center text-gray-400">No billing series configured</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Printer Settings -->
            <div class="mb-3">
              <div class="mb-1 text-[10px] font-semibold text-gray-400">Printer & Format Settings</div>
              <div class="overflow-auto rounded-lg border border-gray-100">
                <table class="w-full text-[10px]">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Printer</th>
                      <th class="whitespace-nowrap px-2 py-1.5 text-left text-gray-400">Print Template</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="ps in rawSettings.printer_settings" :key="ps.printer + ps.template" class="border-t border-gray-100">
                      <td class="whitespace-nowrap px-2 py-1.5 font-medium">{{ ps.printer || '--' }}</td>
                      <td class="whitespace-nowrap px-2 py-1.5">{{ ps.template || '--' }}</td>
                    </tr>
                    <tr v-if="!rawSettings.printer_settings?.length">
                      <td colspan="2" class="px-2 py-2 text-center text-gray-400">No printer settings configured</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- User Series -->
            <div v-if="visibleUserSeries.length">
              <div class="mb-1 text-[10px] font-semibold text-gray-400">User Series Permissions</div>
              <div class="overflow-auto rounded-lg border border-gray-100">
                <table class="w-full text-[10px]">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-2 py-1.5 text-left text-gray-400">User</th>
                      <th class="px-2 py-1.5 text-left text-gray-400">Allowed Series</th>
                      <th class="px-2 py-1.5 text-right text-gray-400">Zoom</th>
                      <th class="px-2 py-1.5 text-left text-gray-400">Cash A/C</th>
                      <th class="px-2 py-1.5 text-left text-gray-400">Bank A/C</th>
                      <th class="px-2 py-1.5 text-left text-gray-400">UPI A/C</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="us in visibleUserSeries" :key="us.name" class="border-t border-gray-100">
                      <td class="px-2 py-1.5 font-medium">{{ us.user || '--' }}</td>
                      <td class="px-2 py-1.5 font-mono">{{ us.allowed_series_seperated_by_comma || '--' }}</td>
                      <td class="px-2 py-1.5 text-right font-mono">{{ us.zoom_value || '--' }}</td>
                      <td class="px-2 py-1.5">{{ us.cash || '--' }}</td>
                      <td class="px-2 py-1.5">{{ us.bank_account || '--' }}</td>
                      <td class="px-2 py-1.5">{{ us.upi || '--' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="flex justify-end gap-2 border-t border-gray-200 px-5 py-3">
        <button 
          class="rounded bg-gray-100 px-4 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-200" 
          @click="$emit('close')"
        >
          Cancel
        </button>
        <button 
          class="rounded bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-700" 
          @click="handleSave"
        >
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { dashboardApi } from '../services/dashboard'
import { session } from '../session.js'

const BILLING_SETTINGS_CACHE_KEY = 'wb-billing-settings-v2'

const props = defineProps({
  show: Boolean,
  systemSettings: Object,
  billingSeries: Array,
  userSeries: Array,
  defaultZoom: [Number, String]
})

const emit = defineEmits(['close', 'save', 'sync'])

const localZoom = ref(props.defaultZoom)
const rawSettings = ref(null)
const syncing = ref(false)

watch(() => props.defaultZoom, (newVal) => {
  localZoom.value = newVal
})

watch(() => props.show, (val) => {
  if (val) loadSettings()
})

async function loadSettings() {
  syncing.value = true
  try {
    rawSettings.value = await dashboardApi.getBillingSettings()
  } catch (e) {
    console.error('[GeneralSettings] getBillingSettings failed:', e)
  } finally {
    syncing.value = false
  }
}

async function handleSync() {
  await loadSettings()
  if (rawSettings.value) {
    if (currentUserRow.value?.zoom_value) {
      localStorage.setItem('wb-zoom', String(currentUserRow.value.zoom_value))
      localZoom.value = parseInt(currentUserRow.value.zoom_value)
    }
    // Clear billing settings cache so Dashboard re-fetches fresh data
    localStorage.removeItem(BILLING_SETTINGS_CACHE_KEY)
  }
  emit('sync')
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
  if (!row) return []
  const allowed = (row.allowed_series_seperated_by_comma || '')
    .split(',').map(s => s.trim()).filter(Boolean)
  if (!allowed.length || allowed.includes('ALL')) return rawSettings.value.billing_series
  const allowedPrefixes = allowed.map(s => getAlpha(s).slice(0, 3))
  return rawSettings.value.billing_series.filter(bs =>
    allowedPrefixes.some(p => getAlpha(bs.series).slice(0, 3).startsWith(p))
  )
})

function handleSave() {
  emit('save', {
    zoom: localZoom.value
  })
}
</script>
