<template>
  <div class="h-screen bg-[var(--color-bg)] overflow-hidden">
    <Item_Invoice_Template
      ref="invoiceTemplateRef"
      title="STORE TRANSFER"
      title-bar-color="#90cdf4"
      :doc-number="transferNo"
      :doc-date="transferDate"
      :items="items"
      :total-amount="totalAmount"
      :sidebar-date="sidebarDate"
      :sidebar-items="recentTransfers"
      :sidebar-search="sidebarSearch"
      :sidebar-series="sidebarSeries"
      :available-series="availableSeries"
      :draft-only="draftOnly"
      :sidebar-loading="sidebarLoading"
      :save-button-text="saveButtonText"
      :is-read-only="isReadOnly"
      @sidebar-date-change="handleSidebarDateChange"
      @doc-date-change="handleDocDateChange"
      @update:sidebarSearch="sidebarSearch = $event"
      @update:sidebarSeries="sidebarSeries = $event"
      @toggle-draft-only="draftOnly = !draftOnly"
      @select-sidebar-item="handleSelectSidebarItem"
      @back="goBack"
      @save="handleSave"
      @submit="handleSubmit"
      @print="handlePrint"
      @cancel="handleCancel"
      :show-submit-button="true"
      :is-draft="isDraft"
    >
      <template #header-bar>
        <div class="flex flex-col gap-2">
          <div class="flex items-center gap-6">
            <div v-if="transferNo" class="flex items-center gap-2 border-r border-[var(--color-border)] pr-6 shrink-0">
              <div class="text-4xl text-[var(--color-text)] tabular-nums font-mono font-bold">{{ transferNo }}</div>
            </div>

            <div class="flex-1 flex items-center gap-8">
              <div class="flex flex-col gap-1">
                <label class="text-sm font-bold uppercase text-[var(--color-text-muted)]">Source Warehouse</label>
                <select 
                  v-model="fromWarehouse" 
                  :disabled="isReadOnly"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)]"
                >
                  <option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.name }}</option>
                </select>
              </div>

              <div class="text-4xl text-[var(--color-text-muted)]">→</div>

              <div class="flex flex-col gap-1">
                <label class="text-sm font-bold uppercase text-[var(--color-text-muted)]">Destination Warehouse</label>
                <select 
                  v-model="toWarehouse" 
                  :disabled="isReadOnly"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)]"
                >
                  <option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.name }}</option>
                </select>
              </div>
            </div>

            <div class="flex items-center gap-3 border-l border-[var(--color-border)] pl-6 whitespace-nowrap ml-auto">
              <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Date</label>
              <div class="flex items-center gap-1">
                <button @click="handleDocDateChange(-1)" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center">&larr;</button>
                <div class="text-3xl text-[var(--color-text)] tabular-nums">{{ formatDate(transferDate) }}</div>
                <button @click="handleDocDateChange(1)" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center">&rarr;</button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template #table-extra-rows>
        <tr v-if="!isReadOnly" class="bg-[var(--color-surface-raised)]/30">
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-3xl font-mono text-center text-[var(--color-text-muted)]">*</td>
          <td colspan="2" class="p-0 border-r border-[var(--color-border)]">
            <input
              ref="barcodeInput"
              v-model="barcodeQuery"
              placeholder="Scan Barcode or Type Item Name..."
              class="w-full bg-transparent px-4 py-3 text-4xl font-mono text-[var(--color-text)] outline-none placeholder:text-[var(--color-text-muted)]/50"
              @keydown.enter="handleBarcodeEnter"
            />
          </td>
          <td colspan="8"></td>
        </tr>
      </template>

      <template #row="{ item, index }">
        <tr class="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]/50">
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl font-mono text-center">{{ index + 1 }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-4xl font-mono">{{ item.item_code }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-4xl font-medium">{{ item.item_name }}</td>
          <td class="p-0 border-r border-[var(--color-border)]">
            <input 
              v-if="!isReadOnly"
              v-model.number="item.qty"
              type="number"
              class="w-full bg-transparent px-2 py-1 text-6xl font-mono text-[var(--color-text)] text-right outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
            />
            <span v-else class="block px-2 py-1 text-6xl font-mono text-right tabular-nums">{{ item.qty }}</span>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl">{{ item.uom }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-5xl font-mono text-right tabular-nums">{{ item.rate }}</td>
          <td colspan="3" class="border-r border-[var(--color-border)]"></td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-5xl font-mono text-right tabular-nums">{{ (item.qty * item.rate).toFixed(2) }}</td>
          <td class="px-2 py-1 text-center">
            <button v-if="!isReadOnly" class="rounded px-1 py-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)]" @click="removeItem(index)">&times;</button>
          </td>
        </tr>
      </template>

      <template #bottom-middle>
         <div class="flex flex-col gap-2 p-2">
            <div class="flex flex-col gap-0.5">
              <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Series</label>
              <select v-model="selectedSeries" :disabled="isReadOnly" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-xl text-[var(--color-text)]">
                <option v-for="s in availableSeries" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
         </div>
      </template>

    </Item_Invoice_Template>

    <!-- Item Search Modal -->
    <ItemSearch 
      v-if="showItemSearch"
      :show="showItemSearch"
      :initial-query="barcodeQuery"
      :skip-date-filter="true"
      @close="showItemSearch = false"
      @select="handleItemSelect"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import ItemSearch from '../components/ItemSearch.vue'
import { frappeGet, frappePost } from '../api'

const router = useRouter()
const transferNo = ref('')
const transferDate = ref(new Date().toISOString().split('T')[0])
const fromWarehouse = ref('')
const toWarehouse = ref('')
const items = ref([])
const warehouses = ref([])
const availableSeries = ref([])
const selectedSeries = ref('')

const isReadOnly = ref(false)
const isDraft = ref(false)
const transferName = ref('')

const barcodeQuery = ref('')
const barcodeInput = ref(null)
const showItemSearch = ref(false)

const sidebarDate = ref(new Date().toISOString().split('T')[0])
const recentTransfers = ref([])
const sidebarSearch = ref('')
const sidebarSeries = ref([])
const draftOnly = ref(false)
const sidebarLoading = ref(false)

const totalAmount = computed(() => {
  return items.value.reduce((sum, item) => sum + (item.qty * item.rate), 0).toFixed(2)
})

const saveButtonText = computed(() => {
  if (isReadOnly.value && !isDraft.value) return 'New'
  if (isReadOnly.value && isDraft.value) return 'Edit'
  return 'Save'
})

onMounted(async () => {
  await fetchMetadata()
  await fetchRecentTransfers()
  focusBarcodeInput()
})

async function fetchMetadata() {
  const res = await frappePost('ssplbilling.api.storetransfer_api.get_metadata')
  warehouses.value = res.warehouses
  availableSeries.value = res.naming_series
  if (availableSeries.value.length) selectedSeries.value = availableSeries.value[0]
  
  if (warehouses.value.length >= 2) {
    fromWarehouse.value = warehouses.value[0].name
    toWarehouse.value = warehouses.value[1].name
  }
}

async function fetchRecentTransfers() {
  sidebarLoading.value = true
  recentTransfers.value = await frappePost('ssplbilling.api.storetransfer_api.get_recent_transfers', { date: sidebarDate.value })
  sidebarLoading.value = false
}

function focusBarcodeInput() {
  setTimeout(() => barcodeInput.value?.focus(), 100)
}

async function handleBarcodeEnter() {
  if (!barcodeQuery.value) return
  
  const res = await frappePost('ssplbilling.api.SaleEntry_api.get_item_details', { 
    item_code: barcodeQuery.value,
    warehouse: fromWarehouse.value
  })
  
  if (res.found) {
    addItem(res)
    barcodeQuery.value = ''
  } else {
    showItemSearch.value = true
  }
}

function handleItemSelect(item) {
  addItem(item)
  barcodeQuery.value = ''
  showItemSearch.value = false
  focusBarcodeInput()
}

function addItem(details) {
  const existing = items.value.find(i => i.item_code === details.item_code)
  if (existing) {
    existing.qty += 1
  } else {
    items.value.push({
      item_code: details.item_code,
      item_name: details.item_name,
      qty: 1,
      uom: details.uom,
      rate: details.rate || 0
    })
  }
}

function removeItem(index) {
  items.value.splice(index, 1)
}

async function handleSave() {
  if (isReadOnly.value && !isDraft.value) {
    resetForm()
    return
  }
  if (isReadOnly.value && isDraft.value) {
    isReadOnly.value = false
    return
  }

  if (!items.value.length) { alert('No items to save'); return }
  if (fromWarehouse.value === toWarehouse.value) { alert('Source and Destination warehouses must be different'); return }

  try {
    const res = await frappePost('ssplbilling.api.storetransfer_api.save_store_transfer', {
      data: {
        naming_series: selectedSeries.value,
        posting_date: transferDate.value,
        from_warehouse: fromWarehouse.value,
        to_warehouse: toWarehouse.value,
        items: items.value
      }
    })
    
    transferNo.value = res.name
    transferName.value = res.name
    isReadOnly.value = true
    isDraft.value = true
    await fetchRecentTransfers()
  } catch (err) {
    console.error(err)
  }
}

async function handleSubmit() {
  if (!transferName.value) return
  try {
    await frappePost('ssplbilling.api.storetransfer_api.submit_store_transfer', { name: transferName.value })
    isDraft.value = false
    await fetchRecentTransfers()
  } catch (err) {
    console.error(err)
  }
}

function resetForm() {
  transferNo.value = ''
  transferName.value = ''
  items.value = []
  isReadOnly.value = false
  isDraft.value = false
  focusBarcodeInput()
}

function goBack() {
  router.push('/dashboard')
}

function handleSidebarDateChange(dir) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + dir)
  sidebarDate.value = d.toISOString().split('T')[0]
  fetchRecentTransfers()
}

function handleDocDateChange(dir) {
  const d = new Date(transferDate.value)
  d.setDate(d.getDate() + dir)
  transferDate.value = d.toISOString().split('T')[0]
}

async function handleSelectSidebarItem(item) {
  const details = await frappePost('ssplbilling.api.storetransfer_api.get_store_transfer_details', { name: item.name })
  transferNo.value = details.name
  transferName.value = details.name
  transferDate.value = details.posting_date
  fromWarehouse.value = details.from_warehouse
  toWarehouse.value = details.to_warehouse
  items.value = details.items.map(i => ({
    item_code: i.item_code,
    item_name: i.item_name,
    qty: i.qty,
    uom: i.uom,
    rate: i.basic_rate
  }))
  isReadOnly.value = true
  isDraft.value = details.docstatus === 0
}

function formatDate(dateString) {
  if (!dateString) return ''
  const d = new Date(dateString)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-')
}

function handlePrint() {
  // Print logic if needed
}

function handleCancel() {
  if (confirm('Are you sure you want to cancel?')) {
    resetForm()
  }
}
</script>

<style scoped>
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox */
input[type=number] {
  -moz-appearance: textfield;
}
</style>
