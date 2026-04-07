<template>
  <div class="h-screen bg-slate-900 overflow-hidden">
    <Item_Invoice_Template
      title="Sales Invoice (Template)"
      :doc-number="invoiceNo"
      :party-name="customerName"
      :party-details="customerDetails"
      :party-address="customerAddress"
      :party-mobile="customerMobile"
      :party-gstin="customerGstin"
      :party-balance="customerBalance"
      :party-last-inv-date="customerLastInvDate"
      :doc-date="invoiceDate"
      :items="items"
      :subtotal="subtotal"
      :total-tax="totalTax"
      :total-amount="totalAmount"
      :price-list="priceList"
      :tax-template="taxTemplate"
      :is-inclusive-tax="isInclusiveTax"
      :warehouse="warehouse"
      :cost-center="costCenter"
      :income-account="incomeAccount"
      :sidebar-date="sidebarDate"      :sidebar-items="recentInvoices"
      @back="goBack"
      @save="handleSave"
      @print="handlePrint"
      @cancel="handleCancel"
      @incentive="handleIncentive"
      @party-click="showCustomerModal = true"
    >
      <!-- Custom slots for additional logic if needed -->
      <template #header-right>
        <span class="text-blue-400 font-bold uppercase tracking-widest">Live Template Mode</span>
      </template>

      <template #row="{ item, index }">
        <tr
          :ref="el => { if (el) rowRefs[index] = el }"
          tabindex="0"
          class="border-b border-[var(--color-border)] outline-none cursor-pointer transition-all"
          :class="{
            'bg-[var(--color-lowlight)] font-bold': (selectedRowIdx === index || editingRowIdx === index) && !item.deleted,
            'opacity-40 bg-red-900/10 grayscale-[0.5]': item.deleted,
            'hover:bg-[var(--color-surface-raised)]/50': selectedRowIdx !== index && editingRowIdx !== index && !item.deleted
          }"
          @focus="selectedRowIdx = index"
          @keydown="handleRowKeydown($event, index)"
        >
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-xl font-mono text-center" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)]'">
            <span v-if="item.deleted" class="text-[10px] bg-red-600 text-white px-1 rounded block uppercase font-bold leading-tight mb-1">Deleted</span>
            {{ index + 1 }}
          </td>

          <!-- item_code -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'code'"
              ref="editCodeInput"
              v-model="item.item_code"
              class="w-full bg-white/10 px-2 py-1 text-2xl font-mono text-[var(--color-text)] outline-none"
              @keydown.enter.prevent="focusEditField('qty', index)"
              @keydown.escape="exitEditMode(index)"
            />
            <span v-else class="block px-2 py-1 text-2xl font-mono" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-highlight)]'">{{ item.item_code }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-2xl font-medium" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-text)]'">
            {{ item.item_name }}
          </td>

          <!-- qty -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'qty'"
              ref="editQtyInput"
              v-model.number="item.qty"
              type="number" min="0"
              class="w-full bg-white/10 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none text-right [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown.enter.prevent="item.qty > 0 && focusEditField('rate', index)"
              @keydown.escape="exitEditMode(index)"
            />
            <span v-else class="block px-2 py-1 text-4xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-text)]'">{{ item.qty }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-xl" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)]'">{{ item.uom || 'Nos' }}</td>

          <!-- rate -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'rate'"
              ref="editRateInput"
              v-model.number="item.rate"
              type="number" min="0" step="0.01"
              class="w-full bg-white/10 px-2 py-1 text-3xl font-mono text-[var(--color-text)] outline-none text-right [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown.enter.prevent="focusEditField('disc', index)"
              @keydown.escape="exitEditMode(index)"
            />
            <span v-else class="block px-2 py-1 text-3xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-text)]'">{{ item.rate }}</span>
          </td>

          <!-- disc % -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'disc'"
              ref="editDiscInput"
              v-model.number="item.discount_percentage"
              type="number" min="0" max="100" step="0.5"
              class="w-full bg-white/10 px-2 py-1 text-2xl font-mono text-[var(--color-text)] outline-none text-right [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown.enter.prevent="finishRowEdit(index)"
              @keydown.escape="exitEditMode(index)"
            />
            <span v-else class="block px-2 py-1 text-2xl font-mono text-right" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-warning)]'">{{ item.discount_percentage || '0' }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-2xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-warning)]/80'">
            {{ item.discount_percentage ? (item.rate * (1 - item.discount_percentage / 100)).toFixed(2) : '—' }}
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-2xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)]'">
            {{ isExempted ? 0 : (item.tax_rate ?? 0) }}
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-3xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? 'text-[var(--color-text)]' : 'text-[var(--color-text)]'">{{ item.amount }}</td>
          <td class="px-2 py-1 text-center">
            <button
              class="rounded px-1 py-0.5 hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)]"
              :class="item.deleted ? 'text-red-500 hover:text-red-400 font-bold' : (selectedRowIdx === index ? 'text-[var(--color-text)]/60 hover:text-red-700' : 'text-[var(--color-text-muted)]')"
              @click.stop="deleteItem(index)"
            >
              {{ item.deleted ? 'Undo' : '×' }}
            </button>
          </td>
        </tr>
      </template>

      <template #bottom-left>
        <div class="flex flex-col h-full overflow-hidden">
          <div class="flex-1 overflow-y-auto px-4 pb-4 pt-2 scrollbar-none">
            <div v-if="selectedRowIdx === -1 && !pendingItem" class="text-sm text-slate-400 italic">
              Scan an item or select a row to see history.
            </div>
            <div v-else-if="historyLoading" class="text-sm text-blue-400 animate-pulse">
              Fetching history...
            </div>
            <div v-else-if="!selectedItemHistory.length" class="text-sm text-slate-500 italic">
              No previous history found for this customer.
            </div>
            <div v-else class="max-h-[110px] overflow-y-auto mb-4 custom-scrollbar">
              <table class="w-full text-left text-lg border-collapse">
                <thead class="sticky top-0 bg-[var(--color-bg)] z-10">
                  <tr class="text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50">
                    <th class="py-0.5 pr-1 font-bold">Bill</th>
                    <th class="py-0.5 px-1 font-bold">Date</th>
                    <th class="py-0.5 px-1 text-right font-bold">Qty</th>
                    <th class="py-0.5 px-1 text-right font-bold">Rate</th>
                    <th class="py-0.5 pl-1 text-right font-bold">Disc%</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]/30">
                  <tr v-for="(h, i) in selectedItemHistory.slice(0, 10)" :key="i" class="text-[var(--color-text)]">
                    <td class="py-1 pr-1 font-mono leading-none whitespace-nowrap">{{ h.name }}</td>
                    <td class="py-1 px-1 font-mono leading-none whitespace-nowrap">{{ formatDateShort(h.date) }}</td>
                    <td class="py-1 px-1 text-right font-mono leading-none">{{ h.qty }}</td>
                    <td class="py-1 px-1 text-right font-mono leading-none font-bold">{{ h.rate.toFixed(2) }}</td>
                    <td class="py-1 pl-1 text-right font-mono leading-none text-[var(--color-warning)]">{{ h.discount || 0 }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Warehouse Stock -->
            <div v-if="activeItemCode && itemStock.length" class="border-t border-[var(--color-border)] pt-2">
              <div class="mb-1 text-[var(--color-text-muted)] text-xs font-bold uppercase tracking-wider">Available Stock:</div>
              <div v-if="stockLoading" class="text-sm text-blue-400 animate-pulse">Updating stock...</div>
              <div v-else class="grid grid-cols-2 gap-x-4 gap-y-1">
                <div v-for="s in itemStock" :key="s.warehouse" class="flex justify-between items-center text-lg font-mono leading-none">
                  <span class="text-[var(--color-text-muted)] truncate mr-2">{{ s.warehouse.split(' - ')[0] }}</span>
                  <span :class="s.qty > 0 ? 'text-green-400' : 'text-red-400'" class="font-bold">{{ s.qty }}</span>
                </div>
              </div>
            </div>

            <!-- Available Prices -->
            <div v-if="activeItemCode && itemPrices.length" class="border-t border-[var(--color-border)] pt-2 mt-2">
              <div class="mb-1 text-[var(--color-text-muted)] text-xs font-bold uppercase tracking-wider">Available Prices:</div>
              <div v-if="pricesLoading" class="text-sm text-blue-400 animate-pulse">Updating prices...</div>
              <div v-else class="grid grid-cols-2 gap-x-4 gap-y-1">
                <div v-for="p in itemPrices" :key="p.price_list" class="flex justify-between items-center text-lg font-mono leading-none">
                  <span class="text-[var(--color-text-muted)] truncate mr-2">{{ p.price_list }}</span>
                  <span class="text-[var(--color-highlight)] font-bold tracking-widest">{{ encryptPrice(p.rate) }}</span>
                </div>
              </div>
            </div>
            <div v-else-if="activeItemCode && !historyLoading && !pricesLoading && !itemPrices.length" class="border-t border-[var(--color-border)] pt-2 mt-2 text-sm text-slate-500 italic">
              No additional price lists available.
            </div>
          </div>
        </div>
      </template>

      <template #bottom-middle>
        <div class="flex flex-col gap-3 p-2 max-h-[300px] overflow-y-auto custom-scrollbar">
          <!-- Row 1: Price List -->
          <div class="flex flex-col gap-0.5">
            <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Price List</label>
            <select
              v-model="priceList"
              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
            >
              <option v-for="pl in localPriceLists" :key="pl" :value="pl">{{ pl }}</option>
              <option v-if="!localPriceLists.length" value="Standard Selling">Standard Selling</option>
            </select>
          </div>

          <!-- Row 2: Tax Template -->
          <div class="flex flex-col gap-0.5">
            <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Tax Template</label>
            <select
              v-model="taxTemplate"
              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
            >
              <option value="">-- None --</option>
              <option v-for="tax in localTaxTemplates" :key="tax" :value="tax">{{ tax }}</option>
            </select>
          </div>

          <!-- 3 Checkboxes -->
          <div class="flex flex-col gap-1 py-1 border-y border-[var(--color-border)]/30">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="isInclusiveTax" class="h-3 w-3 rounded border-[var(--color-border)] accent-[var(--color-highlight)]" />
              <span class="text-[var(--color-text-muted)] text-[10px] font-bold uppercase">Inclusive Tax</span>
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" checked disabled class="h-3 w-3 rounded border-[var(--color-border)] accent-[var(--color-warning)]" />
              <span class="text-[var(--color-text-muted)] text-[10px] font-bold uppercase">Ignore Pricing Rule</span>
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" disabled class="h-3 w-3 rounded border-[var(--color-border)] accent-[var(--color-danger)]" />
              <span class="text-[var(--color-text-muted)] text-[10px] font-bold uppercase">Sale Return</span>
            </label>
          </div>

          <!-- Additional Info -->
          <div class="grid grid-cols-2 gap-2">
            <!-- Warehouse (Readonly) -->
            <div class="flex flex-col gap-0.5">
              <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Warehouse</label>
              <input
                :value="warehouse"
                readonly
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)]/30 px-1 py-0.5 text-base text-[var(--color-text-muted)] outline-none cursor-not-allowed"
              />
            </div>

            <!-- Cost Center -->
            <div class="flex flex-col gap-0.5">
              <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Cost Center</label>
              <select
                v-model="costCenter"
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
              >
                <option v-for="cc in localCostCenters" :key="cc" :value="cc">{{ cc }}</option>
                <option v-if="!localCostCenters.length" :value="costCenter">{{ costCenter }}</option>
              </select>
            </div>

            <!-- wb-income-account -->
            <div class="flex flex-col gap-0.5">
              <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">wb-income-account</label>
              <select
                v-model="incomeAccount"
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
              >
                <option v-for="acc in localAccounts" :key="acc" :value="acc">{{ acc }}</option>
                <option v-if="!localAccounts.length" :value="incomeAccount">{{ incomeAccount }}</option>
              </select>
            </div>
          </div>
        </div>
      </template>

      <template #table-extra-rows>
        <!-- Pending row: qty input after item selected -->
        <template v-if="pendingItem">
          <tr class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/10">
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-xl font-mono text-center">+</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-2xl font-mono">{{ pendingItem.item_code }}</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-2xl">{{ pendingItem.item_name }}</td>
            <td class="p-0 border-r border-[var(--color-border)]">
              <input
                ref="pendingQtyInput"
                v-model.number="pendingItem.qty"
                type="number"
                min="0"
                class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none text-right [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                @keydown.enter.prevent="pendingItem.qty > 0 && confirmPendingItem()"
                @keydown.escape="cancelPendingItem"
              />
            </td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-xl">{{ pendingItem.uom || 'Nos' }}</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-3xl font-mono text-right">{{ pendingItem.rate }}</td>
            <td colspan="5" class="px-2 text-[var(--color-text-muted)] italic text-lg">Enter qty and press Enter</td>
          </tr>
        </template>

        <!-- Barcode input row -->
        <template v-else>
          <tr class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/5">
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-xl font-mono text-center">*</td>
            <td class="p-0 border-r border-[var(--color-border)]">
              <input
                ref="newCodeInput"
                v-model="newItemCode"
                class="w-full bg-transparent px-2 py-1 text-2xl font-mono text-[var(--color-highlight)] outline-none placeholder:text-[var(--color-text-muted)]/30"
                placeholder="Scan or Type Item..."
                @input="onNewCodeInput"
                @keydown="handleNewCodeKeydown"
              />
            </td>
            <td colspan="9" class="px-2 text-[var(--color-text-muted)] italic text-lg">Enter Item Code to add to invoice</td>
          </tr>
        </template>
      </template>
    </Item_Invoice_Template>

    <QuickItemSearch
      ref="quickSearchRef"
      :results="quickSearchResults"
      :price-list="priceList"
      :anchor-el="quickSearchAnchor"
      @select="onQuickSearchSelect"
      @close="quickSearchResults = []"
    />

    <CustomerSearchModal
      v-if="showCustomerModal"
      :show="showCustomerModal"
      skip-date-filter
      initial-type="Customer"
      @close="showCustomerModal = false"
      @select="handleCustomerSelected"
    />

    <Userseries
      :show="showSeriesModal"
      doctype="Sales Invoice"
      @close="showSeriesModal = false"
      @selected="handleSeriesSelected"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api'
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import Userseries from '../components/Userseries.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import { useItemCache } from '../services/itemCache.js'
import { useCustomerHistory } from '../composables/useCustomerHistory.js'
import { encryptPrice } from '../encryption.js'

const router = useRouter()

const { items: cachedItems, lastSync, refreshItemCache, searchItemsInCache } = useItemCache()
const { 
  fetchCustomerSalesHistory, clearHistory, clearItemInsights, getItemHistoryFromCache, historyLoading, 
  fetchItemStock, itemStock, stockLoading,
  fetchItemPrices, itemPrices, pricesLoading
} = useCustomerHistory()

// Page State
const showSeriesModal = ref(false)
const showCustomerModal = ref(false)
const invoiceNo = ref('NEW')
const customerName = ref('Select Customer...')
const customerDetails = ref('')
const customerAddress = ref('')
const customerMobile = ref('')
const customerGstin = ref('')
const customerBalance = ref(null)
const customerLastInvDate = ref('')
const customerState = ref('')
const invoiceDate = ref(new Date().toLocaleDateString('en-IN'))

const newItemCode = ref('')
const newCodeInput = ref(null)
const quickSearchResults = ref([])
const quickSearchRef = ref(null)
const quickSearchAnchor = ref(null)
const pendingItem = ref(null)
const pendingQtyInput = ref(null)
const selectedRowIdx = ref(-1)
const rowRefs = ref([])
const editingRowIdx = ref(-1)
const editingField = ref(null) // 'code' | 'qty' | 'rate' | 'disc'
const editCodeInput = ref(null)
const editQtyInput = ref(null)
const editRateInput = ref(null)
const editDiscInput = ref(null)

// Watch for item selection/pending to fetch live stock and prices
watch([pendingItem, selectedRowIdx], ([pending, rowIdx]) => {
  let code = null
  if (pending) code = pending.item_code
  else if (rowIdx !== -1) code = items.value[rowIdx]?.item_code

  if (code) {
    fetchItemStock(code)
    fetchItemPrices(code)
  }
})

// Use stored arrays for Price List and Tax Template
const localPriceLists = ref([])
try { localPriceLists.value = JSON.parse(localStorage.getItem('wb-pricelist') || '[]') } catch { localPriceLists.value = [] }
const localTaxTemplates = ref([])
try { localTaxTemplates.value = JSON.parse(localStorage.getItem('wb-sales-tax-template') || '[]') } catch { localTaxTemplates.value = [] }

const priceList = ref(localPriceLists.value[0] || 'Standard Selling')
const taxTemplate = ref(localTaxTemplates.value[0] || '')

const localWarehouses = ref([])
try { localWarehouses.value = JSON.parse(localStorage.getItem('wb-warehouses') || '[]') } catch { localWarehouses.value = [] }
const localCostCenters = ref([])
try { localCostCenters.value = JSON.parse(localStorage.getItem('wb-cost-centers') || '[]') } catch { localCostCenters.value = [] }
const localAccounts = ref([])
try { localAccounts.value = JSON.parse(localStorage.getItem('wb-visible-accounts') || '[]') } catch { localAccounts.value = [] }

const warehouse = ref(localStorage.getItem('wb-warehouse') || localWarehouses.value[0] || 'None')
const costCenter = ref(localStorage.getItem('wb-cost-center') || localCostCenters.value[0] || 'None')
const incomeAccount = ref(localStorage.getItem('wb-income-account') || localAccounts.value[0] || 'None')
const isInclusiveTax = ref(true)

watch(taxTemplate, (val) => {
  if (!val) return
  if (val.toLowerCase().includes('inclusive')) {
    isInclusiveTax.value = true
  } else {
    isInclusiveTax.value = false
  }
  applyRegionalTaxLogic()
})

function applyRegionalTaxLogic() {
  if (!customerState.value || !taxTemplate.value) return
  
  const companyState = localStorage.getItem('wb-company-state') || ''
  const partyState = customerState.value
  
  if (!companyState || !partyState) return
  
  const isInterState = companyState.toLowerCase() !== partyState.toLowerCase()
  const currentTax = taxTemplate.value
  
  if (isInterState) {
    if (currentTax.toLowerCase().includes('in-state')) {
      const targetTax = currentTax.replace(/in-state/i, 'Out-State')
      const found = localTaxTemplates.value.find(t => t.toLowerCase() === targetTax.toLowerCase())
      if (found) taxTemplate.value = found
    }
  } else {
    if (currentTax.toLowerCase().includes('out-state')) {
      const targetTax = currentTax.replace(/out-state/i, 'In-State')
      const found = localTaxTemplates.value.find(t => t.toLowerCase() === targetTax.toLowerCase())
      if (found) taxTemplate.value = found
    }
  }
}

const items = ref([])

const recentInvoices = ref([])

const sidebarDate = ref(new Date().toLocaleDateString('en-IN'))

// Computeds
const activeItemCode = computed(() => {
  if (pendingItem.value) return pendingItem.value.item_code
  if (selectedRowIdx.value !== -1) return items.value[selectedRowIdx.value]?.item_code
  return null
})

const isExempted = computed(() => (taxTemplate.value || '').toLowerCase().includes('exempt'))

const activeItems = computed(() => items.value.filter(i => !i.deleted))

const selectedItemHistory = computed(() => {
  // If there's a pending item (just scanned/selected), show its history first
  if (pendingItem.value) {
    return getItemHistoryFromCache(pendingItem.value.item_code)
  }
  // Otherwise show history for the focused row
  if (selectedRowIdx.value === -1) return []
  const item = items.value[selectedRowIdx.value]
  if (!item) return []
  return getItemHistoryFromCache(item.item_code)
})

const totalTax = computed(() => {
  if (isExempted.value) return '0.00'
  return activeItems.value.reduce((sum, item) => {
    const rate = item.tax_rate || 0
    let tax = 0
    if (isInclusiveTax.value) {
      // Tax is included in item.amount: Amount - (Amount / (1 + rate/100))
      tax = item.amount - (item.amount / (1 + rate / 100))
    } else {
      // Tax is extra: Amount * (rate/100)
      tax = item.amount * (rate / 100)
    }
    return sum + tax
  }, 0).toFixed(2)
})

const subtotal = computed(() => {
  return activeItems.value.reduce((sum, item) => {
    const rate = item.tax_rate || 0
    let net = item.amount
    if (isInclusiveTax.value && !isExempted.value) {
      // Amount is inclusive, subtotal should show Net: Amount / (1 + rate/100)
      net = item.amount / (1 + rate / 100)
    }
    return sum + net
  }, 0).toFixed(2)
})

const totalAmount = computed(() => {
  return (parseFloat(subtotal.value) + parseFloat(totalTax.value)).toFixed(2)
})

// Methods
function goBack() {
  router.push('/')
}

function formatDateShort(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = String(d.getFullYear()).slice(-2)
  return `${day}-${month}-${year}`
}

function handleSave() {
  const activeItems = items.value.filter(i => !i.deleted)
  if (activeItems.length === 0) {
    alert('No items to save')
    return
  }
  alert('Template Save triggered for ' + activeItems.length + ' items')
  clearHistory()
}

function handlePrint() {
  alert('Template Print triggered')
}

function handleCancel() {
  if (confirm('Clear all items?')) {
    items.value = []
    clearHistory()
  }
}

function handleIncentive() {
  alert('Incentive Entry triggered')
}

function handleItemEntry() {
  if (!newItemCode.value) return
  // If quick search is open, let keydown handler pick from list
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) return

  // Open pending row for qty entry
  const code = newItemCode.value.trim()
  const cached = searchItemsInCache(code)
  const match = cached.find(i => i.item_code.toLowerCase() === code.toLowerCase()) || cached[0]
  setPendingItem(match
    ? { item_code: match.item_code, item_name: match.item_name, qty: 0, rate: match.price || 0, uom: match.uom || 'Nos', discount_percentage: 0, tax_rate: match.tax_rate || 0, deleted: false }
    : { item_code: code, item_name: '', qty: 0, rate: 0, uom: 'Nos', discount_percentage: 0, tax_rate: 0, deleted: false }
  )
}

function onNewCodeInput() {
  const code = newItemCode.value.trim()
  if (code.length >= 2) {
    quickSearchResults.value = searchItemsInCache(code)
    quickSearchAnchor.value = newCodeInput.value
  } else {
    quickSearchResults.value = []
  }
}

function handleNewCodeKeydown(e) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'Enter') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    } else if (e.key === 'Escape') {
      e.preventDefault()
      quickSearchResults.value = []
      return
    }
  }
  if (e.key === 'Enter') {
    handleItemEntry()
  } else if (e.key === 'ArrowUp' && items.value.length > 0) {
    e.preventDefault()
    focusRow(items.value.length - 1)
  }
}

function handleRowKeydown(e, idx) {
  const item = items.value[idx]
  // Ignore events bubbled up from inputs inside the row
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return

  if (e.key === 'Enter' && !item.deleted) {
    e.preventDefault()
    focusEditField('code', idx)
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (idx < items.value.length - 1) focusRow(idx + 1)
    else focusBarcodeInput()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (idx > 0) focusRow(idx - 1)
    else focusBarcodeInput()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    focusBarcodeInput()
  } else if (e.key === 'Delete' || e.key === 'Backspace') {
    e.preventDefault()
    deleteItem(idx)
  }
}

function focusEditField(field, idx) {
  if (items.value[idx]?.deleted) return

  editingRowIdx.value = idx
  editingField.value = field
  selectedRowIdx.value = idx
  const inputMap = { code: editCodeInput, qty: editQtyInput, rate: editRateInput, disc: editDiscInput }
  nextTick(() => {
    const el = inputMap[field]?.value
    el?.focus()
    el?.select()
  })
}

function exitEditMode(idx) {
  recalcAmount(idx)
  editingRowIdx.value = -1
  editingField.value = null
  nextTick(() => { rowRefs.value[idx]?.focus() })
}

function finishRowEdit(idx) {
  recalcAmount(idx)
  editingRowIdx.value = -1
  editingField.value = null
  if (idx < items.value.length - 1) focusRow(idx + 1)
  else focusBarcodeInput()
}

function recalcAmount(idx) {
  const item = items.value[idx]
  if (!item) return
  item.amount = parseFloat(((item.qty || 0) * (item.rate || 0) * (1 - (item.discount_percentage || 0) / 100)).toFixed(2))
}

function focusRow(idx) {
  selectedRowIdx.value = idx
  nextTick(() => { rowRefs.value[idx]?.focus() })
}

function focusBarcodeInput() {
  selectedRowIdx.value = -1
  nextTick(() => { newCodeInput.value?.focus() })
}

function deleteItem(idx) {
  const item = items.value[idx]
  if (!item) return
  item.deleted = !item.deleted
  if (item.deleted && editingRowIdx.value === idx) {
    editingRowIdx.value = -1
    editingField.value = null
  }
}

function onQuickSearchSelect(item) {
  if (!item) return
  quickSearchResults.value = []
  newItemCode.value = ''
  setPendingItem({ 
    item_code: item.item_code, 
    item_name: item.item_name, 
    qty: 0, 
    rate: item.price || 0, 
    uom: item.uom || 'Nos', 
    discount_percentage: 0,
    tax_rate: item.tax_rate || 0,
    deleted: false
  })
}

function setPendingItem(item) {
  pendingItem.value = item
  nextTick(() => { pendingQtyInput.value?.focus(); pendingQtyInput.value?.select() })
}

function confirmPendingItem() {
  if (!pendingItem.value || pendingItem.value.qty <= 0) return
  const p = pendingItem.value
  items.value.push({
    item_code: p.item_code,
    item_name: p.item_name,
    qty: p.qty,
    uom: p.uom || 'Nos',
    rate: p.rate || 0,
    discount_percentage: p.discount_percentage || 0,
    tax_rate: p.tax_rate || 0,
    amount: parseFloat(((p.qty) * (p.rate || 0)).toFixed(2)),
    deleted: false
  })
  pendingItem.value = null
  newItemCode.value = ''
  quickSearchResults.value = []
  nextTick(() => { newCodeInput.value?.focus(); newCodeInput.value?.scrollIntoView({ block: 'nearest' }) })
}

function cancelPendingItem() {
  pendingItem.value = null
  nextTick(() => { newCodeInput.value?.focus() })
}

function handleCustomerSelected(cust) {
  customerName.value = cust.label || cust.name
  customerDetails.value = cust.mobile_no || cust.email || ''
  customerMobile.value = cust.mobile_no || ''
  customerGstin.value = cust.gstin || ''
  customerBalance.value = cust.balance ?? 0
  customerState.value = cust.state || ''
  
  // Format Address
  const addrParts = [cust.address_line1, cust.city, cust.state].filter(Boolean)
  customerAddress.value = addrParts.join(', ')

  // Format Date (Last Invoice)
  if (cust.last_invoice_date) {
    const d = new Date(cust.last_invoice_date)
    customerLastInvDate.value = d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' })
  } else {
    customerLastInvDate.value = 'None'
  }

  applyRegionalTaxLogic()
  fetchCustomerSalesHistory(cust.name)
  showCustomerModal.value = false

  nextTick(() => {
    newCodeInput.value?.focus()
  })
}

async function handleSeriesSelected(series) {
  try {
    const res = await frappeGet('ssplbilling.api.sales_invoice_api.get_series_defaults', {
      naming_series: series
    })
    invoiceNo.value = res.invoice_no
    priceList.value = res.price_list
    taxTemplate.value = res.tax_template
    
    // Priority: Series config > User Default > existing
    if (res.warehouse) warehouse.value = res.warehouse
    if (res.cost_center) costCenter.value = res.cost_center

    console.log('[SalesInvoice] Series selected and UI updated:', series, res)
    
    // After series selection, close the series modal and open customer modal
    showSeriesModal.value = false
    showCustomerModal.value = true
  } catch (e) {
    console.error('[SalesInvoice] Failed to fetch series defaults:', e)
  }
}

onMounted(() => {
  showSeriesModal.value = true

  // Ensure item cache is populated (TTL 5 mins)
  if (!cachedItems.value.length || (Date.now() - lastSync.value) > 5 * 60 * 1000) {
    refreshItemCache('Sales', priceList.value, warehouse.value)
  }
})
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: var(--color-highlight);
}
</style>
