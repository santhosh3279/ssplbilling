<template>
  <div>
    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="custSearchModalRef"
      :show="showCustomerSearchModal"
      :initial-type="searchType"
      :allowed-types="['Account', 'Customer', 'Supplier', 'Employee']"
      @close="showCustomerSearchModal = false"
      @select="pickCust"
    />

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="itemSearchModalRef"
      :show="showItemSearchModal"
      search-type="Sales"
      :price-list="defaultPriceList"
      :warehouse="defaultWarehouse"
      @close="showItemSearchModal = false"
      @select="pickItem"
    />

    <!-- CUSTOMER LEDGER SUB-WINDOW -->
    <CustomerLedger
      v-if="showLedgerWindow"
      :is-sub-window="true"
      :ledger-name="ledgerCustomerName"
      :ledger-type="ledgerType"
      :initial-from-date="ledgerFromDate"
      :initial-to-date="ledgerToDate"
      @close="closeLedgerAndReturnToSearch"
    />

    <!-- STOCK LEDGER SUB-WINDOW -->
    <StockLedger
      v-if="showStockLedgerWindow"
      :is-sub-window="true"
      :item-code="stockLedgerItemCode"
      :initial-from-date="stockLedgerFromDate"
      :initial-to-date="stockLedgerToDate"
      @close="closeStockLedgerAndReturnToSearch"
    />

    <!-- OUTSTANDING BILLS MODAL -->
    <OutstandingBillsModal
      v-if="showOutstandingBillsModal"
      :party="outstandingParty"
      :party-type="outstandingPartyType"
      :entered-amount="0"
      @close="showOutstandingBillsModal = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import CustomerSearchModal from './CustomerSearchModal.vue'
import ItemSearch from './ItemSearch.vue'
import CustomerLedger from '../pages/CustomerLedger.vue'
import StockLedger from '../pages/StockLedger.vue'
import OutstandingBillsModal from './OutstandingBillsModal.vue'
import { frappeGet } from '../api.js'

const showCustomerSearchModal = ref(false)
const showItemSearchModal = ref(false)
const showLedgerWindow = ref(false)
const showStockLedgerWindow = ref(false)
const showOutstandingBillsModal = ref(false)

const custSearchModalRef = ref(null)
const itemSearchModalRef = ref(null)

const searchPurpose = ref('ledger')
const searchType = ref('All')

const ledgerCustomerName = ref('')
const ledgerType = ref('Customer')
const ledgerFromDate = ref('')
const ledgerToDate = ref('')

const stockLedgerItemCode = ref('')
const stockLedgerFromDate = ref('')
const stockLedgerToDate = ref('')

const outstandingParty = ref('')
const outstandingPartyType = ref('Customer')

// Get defaults from localStorage (synced by Dashboard)
const defaultWarehouse = computed(() => localStorage.getItem('wb-warehouse') || '')
const defaultPriceList = computed(() => {
  const settings = JSON.parse(localStorage.getItem('wb-settings-v2') || '{}')?.data || {}
  const firstSeries = (settings.billing_series || [])[0]
  return firstSeries?.price_list || 'Standard Selling'
})

async function openCustomerSearch(type = 'All', purpose = 'ledger') {
  searchType.value = type
  searchPurpose.value = purpose
  showCustomerSearchModal.value = true
  
  nextTick(() => {
    custSearchModalRef.value?.closeSubForm()
    custSearchModalRef.value?.focus()
  })
}

async function openItemSearch() {
  showItemSearchModal.value = true
  nextTick(() => {
    itemSearchModalRef.value?.closeSubForm()
    itemSearchModalRef.value?.focus()
  })
}

async function pickCust(item, dates) {
  showCustomerSearchModal.value = false
  if (searchPurpose.value === 'outstanding') {
    try {
      const res = await frappeGet('ssplbilling.api.outstanding_api.get_party_outstanding', {
        party_type: item.type || 'Customer',
        party: item.name,
      })
      
      const hasInvoices = (res.invoices || []).length > 0
      const hasPayments = (res.payment_entries || []).length > 0
      const hasJournals = (res.journal_entries || []).length > 0
      
      if (hasInvoices || hasPayments || hasJournals) {
        outstandingParty.value = item.name
        outstandingPartyType.value = item.type || 'Customer'
        showOutstandingBillsModal.value = true
      }
    } catch (e) {
      console.error('GlobalModals: Failed to fetch outstanding items:', e)
    }
    return
  }
  ledgerCustomerName.value = item.name
  ledgerType.value = item.type || 'Customer'
  if (dates) {
    ledgerFromDate.value = dates.from
    ledgerToDate.value = dates.to
  } else {
    ledgerFromDate.value = ''
    ledgerToDate.value = ''
  }
  showLedgerWindow.value = true
}

function closeLedgerAndReturnToSearch() {
  showLedgerWindow.value = false
  openCustomerSearch(searchType.value, searchPurpose.value)
}

function pickItem(item, dates) {
  showItemSearchModal.value = false
  stockLedgerItemCode.value = item.item_code
  if (dates) {
    stockLedgerFromDate.value = dates.from
    stockLedgerToDate.value = dates.to
  } else {
    stockLedgerFromDate.value = ''
    stockLedgerToDate.value = ''
  }
  showStockLedgerWindow.value = true
}

function closeStockLedgerAndReturnToSearch() {
  showStockLedgerWindow.value = false
  openItemSearch()
}

function handleGlobalLedgerSearch() {
  openCustomerSearch('All', 'ledger')
}

function handleGlobalItemSearch() {
  openItemSearch()
}

onMounted(() => {
  window.addEventListener('wb-global-ledger-search', handleGlobalLedgerSearch)
  window.addEventListener('wb-global-item-search', handleGlobalItemSearch)
})

onUnmounted(() => {
  window.removeEventListener('wb-global-ledger-search', handleGlobalLedgerSearch)
  window.removeEventListener('wb-global-item-search', handleGlobalItemSearch)
})
</script>
