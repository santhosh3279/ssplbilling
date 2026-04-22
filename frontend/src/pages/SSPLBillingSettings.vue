<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] overflow-hidden" style="color-scheme: dark;">
    <header class="shrink-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center gap-4">
        <button 
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text-on-highlight)] transition-colors" 
          @click="router.push('/')"
        >
          &larr; Dashboard
        </button>
        <div>
          <h1 class="text-lg font-bold text-[var(--color-text-on-highlight)] uppercase tracking-wider">SSPL Billing Settings</h1>
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
      <datalist id="dl-accounts"><option v-for="o in lists.accounts" :key="o" :value="o"></option></datalist>
      <datalist id="dl-users"><option v-for="o in lists.users" :key="o" :value="o"></option></datalist>
      <datalist id="dl-printers"><option v-for="o in lists.printers" :key="o" :value="o"></option></datalist>
      <datalist id="dl-print-formats"><option v-for="o in lists.printFormats" :key="o" :value="o"></option></datalist>
      <datalist id="dl-price-lists"><option v-for="o in lists.priceLists" :key="o" :value="o"></option></datalist>
      <datalist id="dl-tax-templates"><option v-for="o in lists.taxTemplates" :key="o" :value="o"></option></datalist>
      <datalist id="dl-warehouses"><option v-for="o in lists.warehouses" :key="o" :value="o"></option></datalist>
      <datalist id="dl-cost-centers"><option v-for="o in lists.costCenters" :key="o" :value="o"></option></datalist>
      <datalist id="dl-series"><option v-for="o in lists.series" :key="o" :value="o"></option></datalist>

      <div v-if="isLoading" class="flex h-full items-center justify-center text-[var(--color-text-muted)]">
        <span class="text-xl animate-pulse">Loading settings...</span>
      </div>
      <div v-else-if="settings" class="mx-auto max-w-7xl space-y-8 pb-20">
        
        <!-- Section: Price Encryption -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 class="text-xl font-bold text-[var(--color-text)] border-b border-[var(--color-border)] pb-3 mb-4">Price Encryption</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Cipher Map (JSON array, digits 0-9)</label>
              <input 
                v-model="settings.cipher_map" 
                type="text" 
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Discount Account</label>
              <input 
                v-model="settings.discount_account" list="dl-accounts" 
                type="text" 
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Freight Account</label>
              <input 
                v-model="settings.freight" list="dl-accounts" 
                type="text" 
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Tax Paid on Purchase</label>
              <input 
                v-model="settings.tax_paid_on_purchase" list="dl-accounts" 
                type="text" 
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Packing Charge</label>
              <input 
                v-model="settings.packing_charge" list="dl-accounts" 
                type="text" 
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Loading</label>
              <input 
                v-model="settings.loading" list="dl-accounts" 
                type="text" 
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Other Charges</label>
              <input 
                v-model="settings.other_charges" list="dl-accounts" 
                type="text" 
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
            </div>
          </div>
        </section>

        <!-- Section: Billing Series -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-3 mb-4">
            <h2 class="text-xl font-bold text-[var(--color-text)]">Billing Series</h2>
            <button @click="addRow('billing_series')" class="text-sm bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface-raised)] px-3 py-1 rounded text-[var(--color-text-on-highlight)]">+ Add Row</button>
          </div>
          <table class="w-full text-sm text-left">
            <thead class="text-xs text-[var(--color-text-muted)] uppercase bg-[var(--color-bg)]">
              <tr>
                <th class="px-3 py-2 rounded-tl-lg">Series</th>
                <th class="px-3 py-2">Print Format</th>
                <th class="px-3 py-2">Price List</th>
                <th class="px-3 py-2">Tax Template</th>
                <th class="px-3 py-2 rounded-tr-lg"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in settings.billing_series" :key="idx" class="border-b border-[var(--color-border)]">
                <td class="px-2 py-2"><input v-model="row.series" list="dl-series" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.print_format" list="dl-print-formats" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.price_list" list="dl-price-lists" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.tax_template" list="dl-tax-templates" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
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
            <button @click="addRow('user_series')" class="text-sm bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface-raised)] px-3 py-1 rounded text-[var(--color-text-on-highlight)]">+ Add Row</button>
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
                <td class="px-1 py-2"><input v-model="row.user" list="dl-users" class="w-full min-w-[100px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.allowed_series_seperated_by_comma" placeholder="ALL or prefixes" class="w-full min-w-[100px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.zoom_value" type="number" placeholder="100" class="w-full min-w-[60px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.cash" list="dl-accounts" class="w-full min-w-[80px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.upi" list="dl-accounts" class="w-full min-w-[80px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.card" list="dl-accounts" class="w-full min-w-[80px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.bank" list="dl-accounts" class="w-full min-w-[80px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.warehouse" list="dl-warehouses" class="w-full min-w-[80px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.cost_center" list="dl-cost-centers" class="w-full min-w-[80px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.income_account" list="dl-accounts" class="w-full min-w-[80px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.admin" :true-value="1" :false-value="0" class="cursor-pointer accent-[var(--color-info)]" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.cashier" :true-value="1" :false-value="0" class="cursor-pointer accent-[var(--color-info)]" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.biller" :true-value="1" :false-value="0" class="cursor-pointer accent-[var(--color-info)]" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.accounts" :true-value="1" :false-value="0" class="cursor-pointer accent-[var(--color-info)]" /></td>
                <td class="px-1 py-2"><input v-model="row.default_printer" list="dl-printers" class="w-full min-w-[80px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-1 py-2">
                  <select v-model="row.theme" class="w-full min-w-[70px] bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs focus:border-[var(--color-info)] outline-none text-[var(--color-text)]">
                    <option value="">—</option>
                    <option value="Light">Light</option>
                    <option value="Dark">Dark</option>
                  </select>
                </td>
                <td class="px-1 py-2 text-right"><button @click="removeRow('user_series', idx)" class="text-[var(--color-danger)] hover:text-[var(--color-danger)] font-bold px-2">&times;</button></td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Section: Printer Settings -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-3 mb-4">
            <h2 class="text-xl font-bold text-[var(--color-text)]">Printer Settings</h2>
            <button @click="addRow('table_vycb')" class="text-sm bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface-raised)] px-3 py-1 rounded text-[var(--color-text-on-highlight)]">+ Add Row</button>
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
                <td class="px-2 py-2"><input v-model="row.user" list="dl-users" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.printer" list="dl-printers" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.template" list="dl-print-formats" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-2 py-2 text-right"><button @click="removeRow('table_vycb', idx)" class="text-[var(--color-danger)] hover:text-[var(--color-danger)] font-bold px-2">&times;</button></td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Section: Visible Accounts -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-3 mb-4">
            <h2 class="text-xl font-bold text-[var(--color-text)]">Visible Accounts</h2>
            <button @click="addRow('visible_accounts')" class="text-sm bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface-raised)] px-3 py-1 rounded text-[var(--color-text-on-highlight)]">+ Add Row</button>
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
                <td class="px-2 py-2"><input v-model="row.account" list="dl-accounts" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.label" class="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 focus:border-[var(--color-info)] outline-none" /></td>
                <td class="px-2 py-2 text-right"><button @click="removeRow('visible_accounts', idx)" class="text-[var(--color-danger)] hover:text-[var(--color-danger)] font-bold px-2">&times;</button></td>
              </tr>
            </tbody>
          </table>
        </section>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

const router = useRouter()
const isLoading = ref(true)
const isSaving = ref(false)

const settings = ref(null)

const lists = ref({
  accounts: [],
  users: [],
  printers: [],
  printFormats: [],
  priceLists: [],
  taxTemplates: [],
  warehouses: [],
  costCenters: [],
  series: []
})



onMounted(async () => {
  await Promise.all([fetchSettings(), fetchLists()])
})

async function fetchLists() {
  try {
    const [acc, usr, pf, pl, tax, wh, cc, serSI, serQT, prn] = await Promise.all([
      frappeGet('frappe.client.get_list', { doctype: 'Account', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'User', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Print Template', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Price List', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Sales Taxes and Charges Template', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Warehouse', fields: ['name'], limit_page_length: 0 }),
      frappeGet('frappe.client.get_list', { doctype: 'Cost Center', fields: ['name'], limit_page_length: 0 }),
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
  isSaving.value = true
  try {
    await frappePost('frappe.client.save', { doc: settings.value })
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
