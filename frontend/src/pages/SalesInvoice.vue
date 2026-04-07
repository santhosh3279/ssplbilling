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
      :sidebar-date="sidebarDate"
      :sidebar-items="recentInvoices"
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

      <template #bottom-left>
        <div class="p-4">
          <h3 class="text-xs font-bold uppercase text-slate-500 mb-2">Item Insights</h3>
          <p class="text-sm text-slate-400 italic">Select an item row to see history and stock details here.</p>
        </div>
      </template>

      <template #table-extra-rows>
        <!-- Pending row: qty input after item selected -->
        <tr v-if="pendingItem" class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/10">
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-xl font-mono text-center">+</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-2xl font-mono">{{ pendingItem.item_code }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-2xl">{{ pendingItem.item_name }}</td>
          <td class="p-0 border-r border-[var(--color-border)]">
            <input
              ref="pendingQtyInput"
              v-model.number="pendingItem.qty"
              type="number"
              min="1"
              class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none text-right [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown.enter="confirmPendingItem"
              @keydown.escape="cancelPendingItem"
            />
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-xl">{{ pendingItem.uom || 'Nos' }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-3xl font-mono text-right">{{ pendingItem.rate }}</td>
          <td colspan="5" class="px-2 text-[var(--color-text-muted)] italic text-lg">Enter qty and press Enter</td>
        </tr>

        <!-- Barcode input row -->
        <tr v-else class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/5">
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api'
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import Userseries from '../components/Userseries.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import { useItemCache } from '../services/itemCache.js'

const router = useRouter()

const { items: cachedItems, lastSync, refreshItemCache, searchItemsInCache } = useItemCache()

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
const invoiceDate = ref(new Date().toLocaleDateString('en-IN'))
const priceList = ref('Standard Selling')
const taxTemplate = ref('')
const isInclusiveTax = ref(true)
const warehouse = ref(localStorage.getItem('wb-warehouse') || 'None')
const costCenter = ref(localStorage.getItem('wb-cost-center') || 'None')

const newItemCode = ref('')
const newCodeInput = ref(null)
const quickSearchResults = ref([])
const quickSearchRef = ref(null)
const quickSearchAnchor = ref(null)
const pendingItem = ref(null)
const pendingQtyInput = ref(null)

const items = ref([])

const recentInvoices = ref([])

const sidebarDate = ref(new Date().toLocaleDateString('en-IN'))

// Computeds
const subtotal = computed(() => {
  return items.value.reduce((sum, item) => sum + item.amount, 0).toFixed(2)
})

const totalTax = ref('0.00')
const totalAmount = computed(() => {
  return (parseFloat(subtotal.value) + parseFloat(totalTax.value)).toFixed(2)
})

// Methods
function goBack() {
  router.push('/')
}

function handleSave() {
  alert('Template Save triggered')
}

function handlePrint() {
  alert('Template Print triggered')
}

function handleCancel() {
  if (confirm('Clear all items?')) {
    items.value = []
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
    ? { item_code: match.item_code, item_name: match.item_name, qty: 1, rate: match.price || 0, uom: match.uom || 'Nos', discount_percentage: 0 }
    : { item_code: code, item_name: '', qty: 1, rate: 0, uom: 'Nos', discount_percentage: 0 }
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
  }
}

function onQuickSearchSelect(item) {
  if (!item) return
  quickSearchResults.value = []
  newItemCode.value = ''
  setPendingItem({ item_code: item.item_code, item_name: item.item_name, qty: 1, rate: item.price || 0, uom: item.uom || 'Nos', discount_percentage: 0 })
}

function setPendingItem(item) {
  pendingItem.value = item
  nextTick(() => { pendingQtyInput.value?.focus(); pendingQtyInput.value?.select() })
}

function confirmPendingItem() {
  if (!pendingItem.value) return
  const p = pendingItem.value
  items.value.push({
    item_code: p.item_code,
    item_name: p.item_name,
    qty: p.qty || 1,
    uom: p.uom || 'Nos',
    rate: p.rate || 0,
    discount_percentage: p.discount_percentage || 0,
    amount: ((p.qty || 1) * (p.rate || 0)).toFixed(2)
  })
  pendingItem.value = null
  newItemCode.value = ''
  quickSearchResults.value = []
  nextTick(() => { newCodeInput.value?.focus() })
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
