<template>
  <div class="h-screen bg-slate-900 overflow-hidden">
    <Item_Invoice_Template
      title="Sales Invoice (Template)"
      :doc-number="invoiceNo"
      :party-name="customerName"
      :party-details="customerDetails"
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
    </Item_Invoice_Template>

    <CustomerSearchModal
      v-if="showCustomerModal"
      :show="showCustomerModal"
      @close="showCustomerModal = false"
      @selected="handleCustomerSelected"
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api'
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import Userseries from '../components/Userseries.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'

const router = useRouter()

// Page State
const showSeriesModal = ref(false)
const showCustomerModal = ref(false)
const invoiceNo = ref('NEW')
const customerName = ref('Select Customer...')
const customerDetails = ref('')
const invoiceDate = ref(new Date().toLocaleDateString('en-IN'))
const priceList = ref('Standard Selling')
const taxTemplate = ref('')
const isInclusiveTax = ref(true)
const warehouse = ref(localStorage.getItem('wb-warehouse') || 'None')
const costCenter = ref(localStorage.getItem('wb-cost-center') || 'None')

const items = ref([
  { item_code: 'ITEM-001', item_name: 'Sample Item Alpha', qty: 1, rate: 1000, discount_percentage: 0, amount: 1000 },
  { item_code: 'ITEM-002', item_name: 'Sample Item Beta', qty: 2, rate: 500, discount_percentage: 10, amount: 900 }
])

const recentInvoices = ref([
  { name: 'SINV-001', customer_name: 'Walk-in Customer', grand_total: 1900, docstatus: 0 },
  { name: 'SINV-002', customer_name: 'John Doe', grand_total: 2500, docstatus: 1 }
])

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

function handleCustomerSelected(cust) {
  customerName.value = cust.customer_name || cust.name
  customerDetails.value = cust.mobile || cust.email || ''
  showCustomerModal.value = false
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
  } catch (e) {
    console.error('[SalesInvoice] Failed to fetch series defaults:', e)
  }
}

onMounted(() => {
  showSeriesModal.value = true
})
</script>
