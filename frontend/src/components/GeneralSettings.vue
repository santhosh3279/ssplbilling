<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="w-[820px] rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl">

      <!-- Header -->
      <div class="border-b border-[var(--color-border)] px-5 py-4 flex items-center justify-between bg-[var(--color-surface)]">
        <div class="flex items-center gap-4">
          <div class="text-sm font-semibold text-[var(--color-text)]">⚙️ General Settings</div>
          <button
            @click="showLocalVariables"
            class="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1 text-[10px] font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
          >
            DEBUG: View Local Variables
          </button>
        </div>
        <div class="flex items-center gap-3">
          <button @click="$emit('close')" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]">✕</button>
        </div>
      </div>

      <div class="flex max-h-[78vh] flex-col gap-4 overflow-y-auto px-5 py-4">

        <!-- Loading -->
        <div v-if="syncing && !rawSettings" class="py-8 text-center text-xs text-[var(--color-text-muted)]">Loading settings…</div>

        <template v-if="rawSettings">

          <!-- ── Your Settings ── -->
          <div class="rounded-lg border border-[var(--color-info)] bg-[var(--color-info)]/20 px-4 py-3">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-info)]">Your Settings</div>
            <div class="grid grid-cols-2 gap-x-8 gap-y-2 text-xs">
              <div class="flex items-center justify-between">
                <span class="text-[var(--color-text-muted)]">Default Zoom</span>
                <span class="font-mono font-semibold text-[var(--color-text)]">{{ rawSettings.user_zoom || '--' }}%</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[var(--color-text-muted)]">Warehouse</span>
                <span class="font-medium text-[var(--color-text)]">{{ rawSettings.user_defaults?.warehouse || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[var(--color-text-muted)]">Cost Center</span>
                <span class="font-medium text-[var(--color-text)]">{{ rawSettings.user_defaults?.cost_center || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[var(--color-text-muted)]">Income Account</span>
                <span class="font-medium text-[var(--color-text)]">{{ rawSettings.user_defaults?.income_account || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[var(--color-text-muted)]">Cash Account</span>
                <span class="font-medium text-[var(--color-text)]">{{ rawSettings.user_defaults?.cash || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[var(--color-text-muted)]">Card Account</span>
                <span class="font-medium text-[var(--color-text)]">{{ rawSettings.user_defaults?.card || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[var(--color-text-muted)]">Bank Account</span>
                <span class="font-medium text-[var(--color-text)]">{{ rawSettings.user_defaults?.bank || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[var(--color-text-muted)]">UPI Account</span>
                <span class="font-medium text-[var(--color-text)]">{{ rawSettings.user_defaults?.upi || '--' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[var(--color-text-muted)]">Default Printer</span>
                <span class="font-medium text-[var(--color-text)]">{{ rawSettings.user_defaults?.default_printer || '--' }}</span>
              </div>
            </div>
          </div>

          <!-- ── System Configuration ── -->
          <div>
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">System Configuration</div>
            <div class="overflow-auto rounded-lg border border-[var(--color-border)]">
              <table class="w-full text-xs">
                <thead class="bg-[var(--color-surface)]">
                  <tr>
                    <th class="whitespace-nowrap px-3 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Field</th>
                    <th class="whitespace-nowrap px-3 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-[var(--color-text-muted)]">Discount Account</td>
                    <td class="px-3 py-1.5 font-medium text-[var(--color-text)]">{{ rawSettings.discount_account || '--' }}</td>
                  </tr>
                  <tr class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-[var(--color-text-muted)]">Freight Account</td>
                    <td class="px-3 py-1.5 font-medium text-[var(--color-text)]">{{ rawSettings.freight_account || '--' }}</td>
                  </tr>
                  <tr class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-[var(--color-text-muted)]">Tax Paid on Purchase</td>
                    <td class="px-3 py-1.5 font-medium text-[var(--color-text)]">{{ rawSettings.tax_paid_on_purchase || '--' }}</td>
                  </tr>
                  <tr class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-[var(--color-text-muted)]">Packing Charge</td>
                    <td class="px-3 py-1.5 font-medium text-[var(--color-text)]">{{ rawSettings.packing_charge || '--' }}</td>
                  </tr>
                  <tr class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-[var(--color-text-muted)]">Loading</td>
                    <td class="px-3 py-1.5 font-medium text-[var(--color-text)]">{{ rawSettings.loading || '--' }}</td>
                  </tr>
                  <tr class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-[var(--color-text-muted)]">Other Charges</td>
                    <td class="px-3 py-1.5 font-medium text-[var(--color-text)]">{{ rawSettings.other_charges || '--' }}</td>
                  </tr>
                  <tr class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-[var(--color-text-muted)]">Round Off</td>
                    <td class="px-3 py-1.5 font-medium text-[var(--color-text)]">{{ rawSettings.round_off || '--' }}</td>
                  </tr>
                  <tr class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-3 py-1.5 text-[var(--color-text-muted)]">Cipher Map</td>
                    <td class="px-3 py-1.5 font-mono text-[var(--color-text)]">{{ rawSettings.cipher_map || '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── Billing Series ── -->
          <div>
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Billing Series</div>
            <div class="overflow-auto rounded-lg border border-[var(--color-border)]">
              <table class="w-full text-[10px]">
                <thead class="bg-[var(--color-surface)]">
                  <tr>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Series</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Print Format</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Price List</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Tax Template</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="bs in visibleBillingSeries" :key="bs.series" class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-2 py-1.5 font-semibold text-[var(--color-text)]">{{ bs.series || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ bs.print_format || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ bs.price_list || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ bs.tax_template || '--' }}</td>
                  </tr>
                  <tr v-if="!visibleBillingSeries.length">
                    <td colspan="4" class="px-2 py-3 text-center text-[var(--color-text-muted)]">No billing series configured</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── Visible Accounts ── -->
          <div v-if="rawSettings.visible_accounts?.length">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Visible Accounts</div>
            <div class="overflow-auto rounded-lg border border-[var(--color-border)]">
              <table class="w-full text-xs">
                <thead class="bg-[var(--color-surface)]">
                  <tr>
                    <th class="whitespace-nowrap px-3 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Account</th>
                    <th class="whitespace-nowrap px-3 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Display Label</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="va in rawSettings.visible_accounts" :key="va.account" class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-3 py-1.5 font-medium text-[var(--color-text)]">{{ va.account || '--' }}</td>
                    <td class="px-3 py-1.5 text-[var(--color-text-muted)]">{{ va.label || '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── Printer Settings ── -->
          <div v-if="visiblePrinterSettings.length">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Printer Settings</div>
            <div class="overflow-auto rounded-lg border border-[var(--color-border)]">
              <table class="w-full text-[10px]">
                <thead class="bg-[var(--color-surface)]">
                  <tr>
                    <th v-if="isAdmin" class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">User</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Printer</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Print Template</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="ps in visiblePrinterSettings" :key="ps.user + ps.printer + ps.template" class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td v-if="isAdmin" class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ ps.user || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 font-medium text-[var(--color-text)]">{{ ps.printer || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ ps.template || '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── User Series Permissions ── -->
          <div v-if="visibleUserSeries.length">
            <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">User Series Permissions</div>
            <div class="overflow-auto rounded-lg border border-[var(--color-border)]">
              <table class="w-full text-[10px]">
                <thead class="bg-[var(--color-surface)]">
                  <tr>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">User</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Allowed Series</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-right font-semibold text-[var(--color-text-muted)]">Zoom</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Warehouse</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Cost Center</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Income A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Cash A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Card A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Bank A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">UPI A/C</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-center font-semibold text-[var(--color-text-muted)]">Admin</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-center font-semibold text-[var(--color-text-muted)]">Cashier</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-center font-semibold text-[var(--color-text-muted)]">Biller</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-left font-semibold text-[var(--color-text-muted)]">Default Printer</th>
                    <th class="whitespace-nowrap px-2 py-1.5 text-center font-semibold text-[var(--color-text-muted)]">Accounts</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="us in visibleUserSeries" :key="us.user" class="border-t border-[var(--color-border)] hover:bg-[var(--color-surface)]/40">
                    <td class="whitespace-nowrap px-2 py-1.5 font-medium text-[var(--color-text)]">{{ us.user || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 font-mono text-[var(--color-text-muted)]">{{ us.allowed_series || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-right font-mono text-[var(--color-text-muted)]">{{ us.zoom_value || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ us.warehouse || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ us.cost_center || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ us.income_account || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ us.cash || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ us.card || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ us.bank || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ us.upi || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-center text-[var(--color-text-muted)]">{{ us.admin ? '✓' : '' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-center text-[var(--color-text-muted)]">{{ us.cashier ? '✓' : '' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-center text-[var(--color-text-muted)]">{{ us.biller ? '✓' : '' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-[var(--color-text-muted)]">{{ us.default_printer || '--' }}</td>
                    <td class="whitespace-nowrap px-2 py-1.5 text-center text-[var(--color-text-muted)]">{{ us.accounts ? '✓' : '' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </template>
      </div>

      <!-- Footer -->
      <div class="flex justify-end border-t border-[var(--color-border)] px-5 py-3 bg-[var(--color-surface)]">
        <button
          class="rounded bg-[var(--color-surface-raised)] px-4 py-1.5 text-sm font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]"
          @click="$emit('close')"
        >Close</button>
      </div>

    </div>

    <!-- Debug Variables Modal -->
    <div v-if="showDebugModal" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showDebugModal = false">
      <div class="w-[600px] rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl flex flex-col max-h-[80vh]">
        <div class="border-b border-[var(--color-border)] px-5 py-4 flex items-center justify-between bg-[var(--color-surface)] rounded-t-xl">
          <div class="text-sm font-semibold text-[var(--color-text)]">🛠️ Debug Local Variables</div>
          <button @click="showDebugModal = false" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]">✕</button>
        </div>
        <div class="overflow-y-auto p-5">
          <table class="w-full text-left text-xs text-[var(--color-text)] border-collapse">
            <thead>
              <tr class="border-b border-[var(--color-border)] text-[var(--color-text-muted)]">
                <th class="py-2 px-3 font-semibold">Key</th>
                <th class="py-2 px-3 font-semibold">Value</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="v in localVariables" :key="v.key" class="border-b border-[var(--color-border)]/50 hover:bg-[var(--color-surface)]/30">
                <td class="py-2 px-3 font-mono text-[var(--color-info)]">{{ v.key }}</td>
                <td class="py-2 px-3 font-mono break-all max-w-[300px]" :title="v.value">{{ v.value }}</td>
              </tr>
              <tr v-if="localVariables.length === 0">
                <td colspan="2" class="py-4 text-center text-[var(--color-text-muted)]">No local variables found starting with wb-</td>
              </tr>
            </tbody>
          </table>

          <!-- Cached Tables Summary -->
          <div class="mt-8 mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-info)]">📦 Cached Tables Summary</div>
          <table class="w-full text-left text-xs text-[var(--color-text)] border-collapse">
            <thead>
              <tr class="border-b border-[var(--color-border)] text-[var(--color-text-muted)]">
                <th class="py-2 px-3 font-semibold">Table / Cache</th>
                <th class="py-2 px-3 font-semibold text-right">Record Count</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in cachedTables" :key="t.name" class="border-b border-[var(--color-border)]/50 hover:bg-[var(--color-surface)]/30">
                <td class="py-2 px-3 font-medium">{{ t.name }}</td>
                <td class="py-2 px-3 text-right font-mono font-bold text-[var(--color-highlight)]">{{ t.count.toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="border-t border-[var(--color-border)] px-5 py-3 bg-[var(--color-surface)] rounded-b-xl flex justify-end">
          <button @click="showDebugModal = false" class="rounded bg-[var(--color-surface-raised)] px-4 py-1.5 text-sm font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { dashboardApi } from '../services/dashboard'
import { session } from '../session.js'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { getUserRole } from '../composables/usePermission'
import { useItemCache } from '../services/itemCache'
import { useLedgerCache } from '../services/ledgerCache'

const props = defineProps({
  show: Boolean,
})

const emit = defineEmits(['close'])

useSubwindowWatcher(computed(() => props.show), { ESCAPE: () => emit('close') })

const { items: cachedItems, discountRules: cachedDiscountRules } = useItemCache()
const { ledgers: cachedLedgers } = useLedgerCache()

const rawSettings = ref(null)
const syncing = ref(false)
const showDebugModal = ref(false)
const localVariables = ref([])
const cachedTables = ref([])
const permissionTrigger = ref(0)

defineExpose({ loadSettings, syncing })

onMounted(() => {
  loadSettings()
})

watch(() => props.show, (val) => {
  if (val) loadSettings()
})

async function loadSettings() {
  syncing.value = true
  try {
    const targetUser = localStorage.getItem('wb-inherited-user') || session.user.value
    const [settings, metadata] = await Promise.all([
      dashboardApi.getBillingSettings(targetUser),
      dashboardApi.getSyncMetadata().catch(() => ({}))
    ])
    rawSettings.value = settings
    applyToLocalStorage(settings, targetUser)
    
    if (metadata) {
      if (metadata.sales_tax_templates) {
        localStorage.setItem('wb-sales-tax-template', JSON.stringify(metadata.sales_tax_templates))
      }
      if (metadata.purchase_tax_templates) {
        localStorage.setItem('wb-purchase-tax-template', JSON.stringify(metadata.purchase_tax_templates))
      }
      if (metadata.price_lists) {
        localStorage.setItem('wb-pricelist', JSON.stringify(metadata.price_lists))
      }
      if (metadata.cost_centers) {
        localStorage.setItem('wb-cost-centers', JSON.stringify(metadata.cost_centers))
      }
      if (metadata.warehouses) {
        localStorage.setItem('wb-warehouses', JSON.stringify(metadata.warehouses))
      }
    }

    permissionTrigger.value++
  } catch (e) {
    console.error('[GeneralSettings] loadSettings failed:', e)
  } finally {
    syncing.value = false
  }
}

function applyToLocalStorage(settings, targetUserArg) {
  if (!settings) return
  const targetUser = targetUserArg || localStorage.getItem('wb-inherited-user') || session.user.value
  
  if (settings.company_state) {
    localStorage.setItem('wb-company-state', settings.company_state)
  }
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
  if (settings.round_off) {
    localStorage.setItem('wb-round-off', settings.round_off)
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
  const userRow = (settings.user_series || []).find(r => r.user === targetUser)

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
    if (key.startsWith('wb-') || key.startsWith('wb_') || key.includes('cache')) {
      vars.push({ key, value: localStorage.getItem(key) })
    }
  }
  vars.sort((a, b) => a.key.localeCompare(b.key))
  localVariables.value = vars

  // Populate Cached Tables Summary
  cachedTables.value = [
    { name: 'Items (Memory)', count: cachedItems.value.length },
    { name: 'Ledgers (Local)', count: cachedLedgers.value.length },
    { name: 'Discount Rules (Local)', count: cachedDiscountRules.value.length },
    { name: 'UOM Map (Local)', count: Object.keys(JSON.parse(localStorage.getItem('sspl-item-uoms') || '{}')).length }
  ]

  showDebugModal.value = true
}

const currentUser = computed(() => session.user.value)
const isActualAdmin = computed(() => ['Administrator', 'admin'].includes(currentUser.value))

const userRole = computed(() => {
  permissionTrigger.value
  return getUserRole()
})

const isAdmin = computed(() => userRole.value === 'admin')

const currentUserRow = computed(() => {
  permissionTrigger.value
  if (!rawSettings.value) return null
  const targetUser = localStorage.getItem('wb-inherited-user') || currentUser.value
  return (rawSettings.value.user_series || []).find(r => r.user === targetUser) || null
})

const visibleUserSeries = computed(() => {
  permissionTrigger.value
  if (!rawSettings.value?.user_series) return []
  if (isAdmin.value) return rawSettings.value.user_series
  return currentUserRow.value ? [currentUserRow.value] : []
})

function getAlpha(s) {
  return (s || '').replace(/[^A-Za-z]/g, '')
}

const visiblePrinterSettings = computed(() => {
  permissionTrigger.value
  if (!rawSettings.value?.printer_settings) return []
  if (isAdmin.value) return rawSettings.value.printer_settings
  const targetUser = localStorage.getItem('wb-inherited-user') || currentUser.value
  return rawSettings.value.printer_settings.filter(ps => ps.user === targetUser)
})

const visibleBillingSeries = computed(() => {
  permissionTrigger.value
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
