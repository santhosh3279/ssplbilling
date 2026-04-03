<template>
  <div class="flex h-screen flex-col bg-slate-900 overflow-hidden">
    <header class="shrink-0 flex items-center justify-between border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center gap-4">
        <button 
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-400 hover:bg-slate-700 hover:text-white transition-colors" 
          @click="router.push('/')"
        >
          &larr; Dashboard
        </button>
        <div>
          <h1 class="text-lg font-bold text-white uppercase tracking-wider">SSPL Billing Settings</h1>
          <p class="text-[10px] text-slate-400 uppercase tracking-widest font-medium">System Configuration</p>
        </div>
      </div>
      <div>
        <button 
          @click="saveSettings" 
          :disabled="isSaving"
          class="rounded-lg bg-blue-600 px-6 py-2 text-sm font-bold text-white shadow-md transition-all hover:bg-blue-700 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isSaving ? 'Saving...' : 'Save Settings' }}
        </button>
      </div>
    </header>

    <main class="flex-1 overflow-y-auto scrollbar-none p-6 text-slate-200">
      <div v-if="isLoading" class="flex h-full items-center justify-center text-slate-500">
        <span class="text-xl animate-pulse">Loading settings...</span>
      </div>
      <div v-else-if="settings" class="mx-auto max-w-7xl space-y-8 pb-20">
        
        <!-- Section: Price Encryption -->
        <section class="rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-sm">
          <h2 class="text-xl font-bold text-slate-100 border-b border-slate-700 pb-3 mb-4">Price Encryption</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-semibold text-slate-400 mb-1">Cipher Map (JSON array, digits 0-9)</label>
              <input 
                v-model="settings.cipher_map" 
                type="text" 
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-400 mb-1">Discount Account</label>
              <input 
                v-model="settings.discount_account" 
                type="text" 
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-400 mb-1">Freight Account</label>
              <input 
                v-model="settings.freight" 
                type="text" 
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-400 mb-1">Tax Paid on Purchase</label>
              <input 
                v-model="settings.tax_paid_on_purchase" 
                type="text" 
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-400 mb-1">Packing Charge</label>
              <input 
                v-model="settings.packing_charge" 
                type="text" 
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-400 mb-1">Loading</label>
              <input 
                v-model="settings.loading" 
                type="text" 
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-400 mb-1">Other Charges</label>
              <input 
                v-model="settings.other_charges" 
                type="text" 
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
        </section>

        <!-- Section: Billing Series -->
        <section class="rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-slate-700 pb-3 mb-4">
            <h2 class="text-xl font-bold text-slate-100">Billing Series</h2>
            <button @click="addRow('billing_series')" class="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded text-white">+ Add Row</button>
          </div>
          <table class="w-full text-sm text-left">
            <thead class="text-xs text-slate-400 uppercase bg-slate-900">
              <tr>
                <th class="px-3 py-2 rounded-tl-lg">Series</th>
                <th class="px-3 py-2">Print Format</th>
                <th class="px-3 py-2">Price List</th>
                <th class="px-3 py-2">Tax Template</th>
                <th class="px-3 py-2 rounded-tr-lg"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in settings.billing_series" :key="idx" class="border-b border-slate-700">
                <td class="px-2 py-2"><input v-model="row.series" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 focus:border-blue-500 outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.print_format" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 focus:border-blue-500 outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.price_list" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 focus:border-blue-500 outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.tax_template" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 focus:border-blue-500 outline-none" /></td>
                <td class="px-2 py-2 text-right"><button @click="removeRow('billing_series', idx)" class="text-red-400 hover:text-red-300 font-bold px-2">&times;</button></td>
              </tr>
              <tr v-if="!settings.billing_series || settings.billing_series.length === 0">
                <td colspan="5" class="text-center py-4 text-slate-500 italic">No series configured</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Section: User Series -->
        <section class="rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-slate-700 pb-3 mb-4">
            <h2 class="text-xl font-bold text-slate-100">User Series & Roles</h2>
            <button @click="addRow('user_series')" class="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded text-white">+ Add Row</button>
          </div>
          <table class="w-full text-sm text-left">
            <thead class="text-[10px] text-slate-400 uppercase bg-slate-900">
              <tr>
                <th class="px-2 py-2">User</th>
                <th class="px-2 py-2">Allowed Series</th>
                <th class="px-2 py-2">Cash</th>
                <th class="px-2 py-2">UPI</th>
                <th class="px-2 py-2">Card</th>
                <th class="px-2 py-2">Bank</th>
                <th class="px-2 py-2">Income</th>
                <th class="px-2 py-2 text-center" title="Admin">A</th>
                <th class="px-2 py-2 text-center" title="Cashier">C</th>
                <th class="px-2 py-2 text-center" title="Biller">B</th>
                <th class="px-2 py-2 text-center" title="Accounts">Acc</th>
                <th class="px-2 py-2"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in settings.user_series" :key="idx" class="border-b border-slate-700">
                <td class="px-1 py-2"><input v-model="row.user" class="w-full min-w-[100px] bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs focus:border-blue-500 outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.allowed_series_seperated_by_comma" placeholder="ALL or prefixes" class="w-full min-w-[100px] bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs focus:border-blue-500 outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.cash" class="w-full min-w-[80px] bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs focus:border-blue-500 outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.upi" class="w-full min-w-[80px] bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs focus:border-blue-500 outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.card" class="w-full min-w-[80px] bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs focus:border-blue-500 outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.bank" class="w-full min-w-[80px] bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs focus:border-blue-500 outline-none" /></td>
                <td class="px-1 py-2"><input v-model="row.income_account" class="w-full min-w-[80px] bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs focus:border-blue-500 outline-none" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.admin" :true-value="1" :false-value="0" class="cursor-pointer accent-blue-500" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.cashier" :true-value="1" :false-value="0" class="cursor-pointer accent-blue-500" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.biller" :true-value="1" :false-value="0" class="cursor-pointer accent-blue-500" /></td>
                <td class="px-1 py-2 text-center"><input type="checkbox" v-model="row.accounts" :true-value="1" :false-value="0" class="cursor-pointer accent-blue-500" /></td>
                <td class="px-1 py-2 text-right"><button @click="removeRow('user_series', idx)" class="text-red-400 hover:text-red-300 font-bold px-2">&times;</button></td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Section: Printer Settings -->
        <section class="rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-slate-700 pb-3 mb-4">
            <h2 class="text-xl font-bold text-slate-100">Printer Settings (table_vycb)</h2>
            <button @click="addRow('table_vycb')" class="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded text-white">+ Add Row</button>
          </div>
          <table class="w-full text-sm text-left">
            <thead class="text-xs text-slate-400 uppercase bg-slate-900">
              <tr>
                <th class="px-3 py-2 rounded-tl-lg">User</th>
                <th class="px-3 py-2">Printer</th>
                <th class="px-3 py-2">Template</th>
                <th class="px-3 py-2 rounded-tr-lg"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in settings.table_vycb" :key="idx" class="border-b border-slate-700">
                <td class="px-2 py-2"><input v-model="row.user" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 focus:border-blue-500 outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.printer" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 focus:border-blue-500 outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.template" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 focus:border-blue-500 outline-none" /></td>
                <td class="px-2 py-2 text-right"><button @click="removeRow('table_vycb', idx)" class="text-red-400 hover:text-red-300 font-bold px-2">&times;</button></td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Section: Visible Accounts -->
        <section class="rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-sm overflow-x-auto">
          <div class="flex items-center justify-between border-b border-slate-700 pb-3 mb-4">
            <h2 class="text-xl font-bold text-slate-100">Visible Accounts</h2>
            <button @click="addRow('visible_accounts')" class="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded text-white">+ Add Row</button>
          </div>
          <table class="w-full text-sm text-left">
            <thead class="text-xs text-slate-400 uppercase bg-slate-900">
              <tr>
                <th class="px-3 py-2 rounded-tl-lg">Account</th>
                <th class="px-3 py-2">Label</th>
                <th class="px-3 py-2 rounded-tr-lg"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in settings.visible_accounts" :key="idx" class="border-b border-slate-700">
                <td class="px-2 py-2"><input v-model="row.account" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 focus:border-blue-500 outline-none" /></td>
                <td class="px-2 py-2"><input v-model="row.label" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 focus:border-blue-500 outline-none" /></td>
                <td class="px-2 py-2 text-right"><button @click="removeRow('visible_accounts', idx)" class="text-red-400 hover:text-red-300 font-bold px-2">&times;</button></td>
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

onMounted(async () => {
  await fetchSettings()
})

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

function addRow(tableName) {
  if (!settings.value[tableName]) settings.value[tableName] = []
  settings.value[tableName].push({})
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
