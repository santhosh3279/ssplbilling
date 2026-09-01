<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] overflow-hidden" style="color-scheme: dark;">
    <header class="shrink-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center gap-4">
        <button 
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors" 
          @click="router.push('/')"
        >
          &larr; Dashboard
        </button>
        <div>
          <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">SSPL Billing Settings</h1>
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">System Configuration</p>
        </div>
      </div>
      <div>
        <button 
          @click="saveSettings" 
          :disabled="isSaving"
          class="rounded-lg bg-[var(--color-info)] px-6 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-md transition-all hover:bg-[var(--color-info)] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isSaving ? 'Saving...' : 'Save Settings' }}
        </button>
      </div>
    </header>

    
    <main class="flex-1 overflow-y-auto scrollbar-none p-6 text-[var(--color-text)]">
      <div v-if="isLoading" class="flex h-full items-center justify-center text-[var(--color-text-muted)]">
        <span class="text-xl animate-pulse">Loading settings...</span>
      </div>
      <div v-else-if="settings" class="mx-auto max-w-7xl space-y-8 pb-20">
        
        <!-- Section: Price Encryption -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 class="text-xl font-bold text-[var(--color-text)] border-b border-[var(--color-border)] pb-3 mb-4">Price Encryption</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Cipher Map (10 characters, digits 0-9)</label>
              <input 
                v-model="settings.cipher_map" 
                type="text" 
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
              <p class="mt-1 text-xs text-[var(--color-text-muted)]">
                One character per digit 0-9, in order (e.g. KLMNOPQRST). Leave blank for no encryption.
              </p>
            </div>
            <DropdownField v-model="settings.discount_account" :options="lists.accounts" label="Discount Account" />
            <DropdownField v-model="settings.short_or_excess_account" :options="lists.accounts" label="Short or Excess Account" />
            <DropdownField v-model="settings.freight" :options="lists.accounts" label="Freight Account" />
            <DropdownField v-model="settings.tax_paid_on_purchase" :options="lists.accounts" label="Tax Paid on Purchase" />
            <DropdownField v-model="settings.packing_charge" :options="lists.accounts" label="Packing Charge" />
            <DropdownField v-model="settings.loading" :options="lists.accounts" label="Loading" />
            <DropdownField v-model="settings.other_charges" :options="lists.accounts" label="Other Charges" />
            <DropdownField v-model="settings.round_off" :options="lists.accounts" label="Round Off" />
          </div>
        </section>

        <!-- Section: Billing Series -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-3 mb-4">
            <h2 class="text-xl font-bold text-[var(--color-text)]">Billing Series</h2>
            <button @click="addRow('billing_series')" class="text-sm bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface-raised)] px-3 py-1 rounded text-[var(--color-text)]">+ Add Row</button>
          </div>
          <table class="w-full text-sm text-left">
            <thead class="text-xs text-[var(--color-text-muted)] uppercase bg-[var(--color-bg)]">
              <tr>
                <th class="px-3 py-2 rounded-tl-lg">Series</th>
                <th class="px-3 py-2">Print Format</th>
                <th class="px-3 py-2">Price List</th>
                <th class="px-3 py-2">Tax Template</th>
                <th class="px-3 py-2 text-center">Tax Incl.</th>
                <th class="px-3 py-2 rounded-tr-lg"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in settings.billing_series" :key="idx" class="border-b border-[var(--color-border)]">
                <td class="px-2 py-2"><DropdownField v-model="row.series" :options="lists.series" /></td>
                <td class="px-2 py-2"><DropdownField v-model="row.print_format" :options="lists.printFormats" /></td>
                <td class="px-2 py-2"><DropdownField v-model="row.price_list" :options="lists.priceLists" /></td>
                <td class="px-2 py-2"><DropdownField v-model="row.tax_template" :options="lists.taxTemplates" /></td>
                <td class="px-2 py-2 text-center">
                  <input type="checkbox" v-model="row.tax_type_incl" :true-value="1" :false-value="0" class="cursor-pointer accent-[var(--color-info)]" />
                </td>
                <td class="px-2 py-2 text-right"><button @click="removeRow('billing_series', idx)" class="text-[var(--color-danger)] hover:text-[var(--color-danger)] font-bold px-2">&times;</button></td>
              </tr>
              <tr v-if="!settings.billing_series || settings.billing_series.length === 0">
                <td colspan="5" class="text-center py-4 text-[var(--color-text-muted)] italic">No series configured</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Section: User Series -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-3 mb-4">
            <h2 class="text-xl font-bold text-[var(--color-text)]">User Series & Roles</h2>
            <button @click="addRow('user_series')" class="text-sm bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface-raised)] px-3 py-1 rounded text-[var(--color-text)]">+ Add Row</button>
          </div>
          <table class="w-full text-sm text-left">
            <thead class="text-[10px] text-[var(--color-text-muted)] uppercase bg-[var(--color-bg)]">
              <tr>
                <th class="px-2 py-2">User</th>
                <th class="px-2 py-2">Allowed Series</th>
                <th class="px-2 py-2">Zoom</th>
                <th class="px-2 py-2">Cash</th>
                <th class="px-2 py-2">UPI</th>
                <th class="px-2 py-2">Card</th>
                <th class="px-2 py-2">Bank</th>
                <th class="px-2 py-2">Warehouse</th>
                <th class="px-2 py-2">Cost Center</th>
                <th class="px-2 py-2">Income</th>
                <th class="px-2 py-2">Company</th>
                <th class="px-2 py-2 text-center" title="Admin">A</th>
                <th class="px-2 py-2 text-center" title="Cashier">C</th>
                <th class="px-2 py-2 text-center" title="Biller">B</th>
                <th class="px-2 py-2 text-center" title="Accounts">Acc</th>
                <th class="px-2 py-2">Printer</th>
                <th class="px-2 py-2">Theme</th>
                <th class="px-2 py-2"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in settings.user_series" :key="idx" class="border-b border-[var(--color-border)]">
                <td class="px-1 py-2"><DropdownField v-model="row.user" :options="lists.users" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.allowed_series_seperated_by_comma" placeholder="ALL or prefixes" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.zoom_value" type="number" placeholder="100" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.cash" :options="lists.accounts" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.upi" :options="lists.accounts" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.card" :options="lists.accounts" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.bank" :options="lists.accounts" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.warehouse" :options="lists.warehouses" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.cost_center" :options="lists.costCenters" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.income_account" :options="lists.accounts" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.company" :options="lists.companies" compact /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.admin" :true-value="1" :false-value="0" class="cursor-pointer accent-[var(--color-info)]" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.cashier" :true-value="1" :false-value="0" class="cursor-pointer accent-[var(--color-info)]" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.biller" :true-value="1" :false-value="0" class="cursor-pointer accent-[var(--color-info)]" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.accounts" :true-value="1" :false-value="0" class="cursor-pointer accent-[var(--color-info)]" /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.default_printer" :options="lists.printers" compact /></td>
                <td class="px-1 py-2"><DropdownField v-model="row.theme" :options="lists.themes" compact /></td>
                <td class="px-1 py-2 text-right"><button @click="removeRow('user_series', idx)" class="text-[var(--color-danger)] hover:text-[var(--color-danger)] font-bold px-2">&times;</button></td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Section: Printer Settings -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-3 mb-4">
            <h2 class="text-xl font-bold text-[var(--color-text)]">Printer Settings</h2>
            <button @click="addRow('table_vycb')" class="text-sm bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface-raised)] px-3 py-1 rounded text-[var(--color-text)]">+ Add Row</button>
          </div>
          <table class="w-full text-sm text-left">
            <thead class="text-xs text-[var(--color-text-muted)] uppercase bg-[var(--color-bg)]">
              <tr>
                <th class="px-3 py-2 rounded-tl-lg">User</th>
                <th class="px-3 py-2">Printer</th>
                <th class="px-3 py-2">Template</th>
                <th class="px-3 py-2 rounded-tr-lg"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in settings.table_vycb" :key="idx" class="border-b border-[var(--color-border)]">
                <td class="px-2 py-2"><DropdownField v-model="row.user" :options="lists.users" /></td>
                <td class="px-2 py-2"><DropdownField v-model="row.printer" :options="lists.printers" /></td>
                <td class="px-2 py-2"><DropdownField v-model="row.template" :options="lists.printFormats" /></td>
                <td class="px-2 py-2 text-right"><button @click="removeRow('table_vycb', idx)" class="text-[var(--color-danger)] hover:text-[var(--color-danger)] font-bold px-2">&times;</button></td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Section: Visible Accounts -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-3 mb-4">
            <h2 class="text-xl font-bold text-[var(--color-text)]">Visible Accounts</h2>
            <button @click="addRow('visible_accounts')" class="text-sm bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface-raised)] px-3 py-1 rounded text-[var(--color-text)]">+ Add Row</button>
          </div>
          <table class="w-full text-sm text-left">
            <thead class="text-xs text-[var(--color-text-muted)] uppercase bg-[var(--color-bg)]">
              <tr>
                <th class="px-3 py-2 rounded-tl-lg">Account</th>
                <th class="px-3 py-2">Label</th>
                <th class="px-3 py-2 rounded-tr-lg"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in settings.visible_accounts" :key="idx" class="border-b border-[var(--color-border)]">
                <td class="px-2 py-2"><DropdownField v-model="row.account" :options="lists.accounts" /></td>
                <td class="px-2 py-2"><input v-model="row.label" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-2 py-2 text-right"><button @click="removeRow('visible_accounts', idx)" class="text-[var(--color-danger)] hover:text-[var(--color-danger)] font-bold px-2">&times;</button></td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Section: WhatsApp Tab Extension -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-3 mb-4">
            <h2 class="text-xl font-bold text-[var(--color-text)]">WhatsApp Tab Extension</h2>
            <span
              class="rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider"
              :class="extensionInstalled
                ? 'bg-[var(--color-success)]/20 text-[var(--color-success)]'
                : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]'"
            >
              {{ extensionInstalled ? 'Installed on this machine' : 'Not installed here' }}
            </span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-3">
              <p class="text-sm text-[var(--color-text-muted)]">
                Sends a shared bill to the WhatsApp Web tab that is already open: switches to the
                party's chat and attaches the bill PDF, leaving only send to press. WhatsApp blocks a
                web page from doing any of this itself
                (<span class="font-mono text-xs">Cross-Origin-Opener-Policy</span>), so only a browser
                extension can. Billing works without it — bills then open a fresh tab to drag into.
              </p>
              <a
                :href="extensionZipUrl"
                download
                class="inline-flex items-center gap-3 rounded-lg bg-[#25D366] px-5 py-2.5 text-sm font-bold text-black shadow-md transition-all hover:brightness-110 active:scale-95"
              >
                <span class="text-lg">⬇</span>
                Download Extension (.zip)
              </a>
            </div>

            <ol class="list-decimal space-y-2 pl-5 text-sm text-[var(--color-text-muted)]">
              <li>Download and unzip to a permanent folder — Chrome loads it from that path on every start, so it must not be moved or deleted.</li>
              <li>Open <span class="font-mono text-xs text-[var(--color-text)]">chrome://extensions</span> and turn on <b>Developer mode</b>.</li>
              <li>Click <b>Load unpacked</b> and pick the unzipped <span class="font-mono text-xs text-[var(--color-text)]">whatsapp-tab</span> folder.</li>
              <li>Hard-reload this page (<span class="font-mono text-xs text-[var(--color-text)]">Ctrl+Shift+R</span>) — Chrome does not inject into tabs that were already open. The badge above turns green.</li>
            </ol>
          </div>
        </section>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { isValidCipherMap } from '../encryption.js'
import DropdownField from '../components/DropdownField.vue'
import { hasWhatsAppBridge } from '../services/whatsappBridge'

const router = useRouter()
const isLoading = ref(true)
const isSaving = ref(false)

const settings = ref(null)

// Zipped from the app's own source on request, so the download always matches the
// installed version of ssplbilling.
const extensionZipUrl = '/api/method/ssplbilling.api.print_preview_api.download_whatsapp_extension'
// The extension's content script stamps the page it runs on, so this reports on the
// machine the operator is sitting at — not on the server.
const extensionInstalled = ref(false)

const lists = ref({
  accounts: [],
  users: [],
  printers: [],
  printFormats: [],
  priceLists: [],
  taxTemplates: [],
  warehouses: [],
  costCenters: [],
  companies: [],
  series: [],
  themes: ['Light', 'Dark']
})



onMounted(async () => {
  extensionInstalled.value = hasWhatsAppBridge()
  await Promise.all([fetchSettings(), fetchLists()])
})

async function fetchLists() {
  try {
    const [acc, usr, pf, pl, tax, wh, cc, comp, serSI, serQT, prn] = await Promise.all([
      frappeGet('frappe.client.get_list', { doctype: 'Account', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'User', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Print Template', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Price List', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Sales Taxes and Charges Template', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Warehouse', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Cost Center', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Company', fields: ['name'], limit_page_length: 0 }),
      frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', { doctype: 'Sales Invoice' }).catch(() => ({allowed_series: []})),
      frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', { doctype: 'Quotation' }).catch(() => ({allowed_series: []})),
      frappeGet('frappe.client.get_list', { doctype: 'Printer', fields: ['name'], limit_page_length: 0 }).catch(() => [])
    ])
    
    lists.value.accounts = acc.map(a => a.name)
    lists.value.users = usr.map(u => u.name)
    lists.value.printFormats = pf.map(p => p.name)
    lists.value.priceLists = pl.map(p => p.name)
    lists.value.taxTemplates = tax.map(t => t.name)
    lists.value.warehouses = wh.map(w => w.name)
    lists.value.costCenters = cc.map(c => c.name)
    lists.value.companies = comp.map(c => c.name)
    lists.value.printers = prn.map(p => p.name)
    
    const s1 = serSI.allowed_series || []
    const s2 = serQT.allowed_series || []
    lists.value.series = [...new Set([...s1, ...s2])]
  } catch(e) {
    console.error('Error fetching lists', e)
  }
}


async function fetchSettings() {
  isLoading.value = true
  try {
    const res = await frappeGet('frappe.client.get', { doctype: 'SSPL Billing Settings', name: 'SSPL Billing Settings' })
    settings.value = res
    if (!settings.value.billing_series) settings.value.billing_series = []
    if (!settings.value.user_series) settings.value.user_series = []
    if (!settings.value.table_vycb) settings.value.table_vycb = []
    if (!settings.value.visible_accounts) settings.value.visible_accounts = []
  } catch (error) {
    alert('Failed to load SSPL Billing Settings: ' + error.message)
  } finally {
    isLoading.value = false
  }
}

async function saveSettings() {
  const rawCipher = (settings.value?.cipher_map || '').trim()
  if (!isValidCipherMap(rawCipher)) {
    alert(
      'Cipher Map is invalid. Enter exactly 10 characters, one per digit 0-9, ' +
      'e.g. KLMNOPQRST, or leave it blank to turn price encryption off.'
    )
    return
  }

  isSaving.value = true
  try {
    await frappePost('frappe.client.save', { doc: settings.value })
    // Apply the cipher now instead of waiting for the next Dashboard visit.
    if (rawCipher) {
      localStorage.setItem('wb-cipher', rawCipher)
    } else {
      localStorage.removeItem('wb-cipher')
    }
    alert('Settings saved successfully!')
    await fetchSettings()
  } catch (error) {
    console.error('Save failed:', error)
  } finally {
    isSaving.value = false
  }
}

const CHILD_DOCTYPE = {
  billing_series: 'SSPL Billing Series',
  user_series: 'USER SERIES',
  table_vycb: 'Printer and Format',
  visible_accounts: 'SSPL Visible Account',
}

function addRow(tableName) {
  if (!settings.value[tableName]) settings.value[tableName] = []
  settings.value[tableName].push({ doctype: CHILD_DOCTYPE[tableName] })
}

function removeRow(tableName, idx) {
  settings.value[tableName].splice(idx, 1)
}
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
