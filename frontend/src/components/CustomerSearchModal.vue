<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm outline-none"
    @click.self="handleEsc"
    @keydown="handleGlobalKeydown"
    tabindex="-1"
  >
    <div class="flex h-[90vh] w-[95vw] flex-col rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden relative">
      <!-- Header -->
      <div class="border-b border-[var(--color-border)] px-5 py-4 flex items-center justify-between bg-[var(--color-surface-raised)]">
        <div>
          <div class="text-2xl font-semibold text-[var(--color-text)]">Detailed Ledger Search</div>
          <div class="text-lg text-[var(--color-text-muted)]">Search Customers, Suppliers, and Accounting Ledgers</div>
        </div>
        <div class="flex items-center gap-3">
          <!-- Quick Filter Tabs -->
          <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-1 shadow-sm mr-4 relative group">
            <button
              v-for="t in availableTabs"
              :key="t"
              @click="activeType = t"
              class="px-4 py-1.5 text-sm font-bold transition-all rounded-md"
              :class="activeType === t ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-sm' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)]'"
            >
              {{ t }}
            </button>
            <div class="absolute -bottom-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text-muted)] whitespace-nowrap shadow-sm">Cycle: F7</kbd>
            </div>
          </div>

          <button
            @click="openNewForm"
            v-if="activeType === 'Customer' || activeType === 'Supplier' || activeType === 'Employee'"
            class="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-lg font-semibold text-[var(--color-text)] shadow-sm transition-colors hover:bg-[var(--color-surface-raised)]"
          >
            New {{ activeType }} <kbd class="ml-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-xs text-[var(--color-text-muted)]">F2</kbd>
          </button>
          <button
            @click="openEditForm(results[selectedIdx])"
            v-if="results[selectedIdx] && (results[selectedIdx].type === 'Customer' || results[selectedIdx].type === 'Supplier' || results[selectedIdx].type === 'Employee')"
            class="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-lg font-semibold text-[var(--color-text)] shadow-sm transition-colors hover:bg-[var(--color-surface-raised)]"
          >
            Edit Details <kbd class="ml-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-xs text-[var(--color-text-muted)]">F3</kbd>
          </button>
          <button
            @click="preloadLedger"
            class="flex items-center gap-2 rounded-lg border border-[var(--color-highlight)] bg-[var(--color-highlight)]/10 px-4 py-2 text-lg font-semibold text-[var(--color-highlight)] transition-colors"
          >
            🔄 Refresh <kbd class="ml-1 rounded border border-[var(--color-highlight)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-xs text-[var(--color-highlight)]">F5</kbd>
          </button>
          <button @click="$emit('close')" class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)]">✕</button>
        </div>
      </div>

      <!-- Search input -->
      <div class="border-b border-[var(--color-border)] p-4 relative">
        <input
          ref="searchInput"
          v-model="query"
          class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/20"
          placeholder="Search by Name, Mobile, WhatsApp, GST, City..."
          @keydown.esc.stop="handleEsc"
        />
        <div v-if="loading" class="absolute right-8 top-1/2 -translate-y-1/2">
          <span class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-highlight)] border-t-transparent"></span>
        </div>
      </div>

      <!-- Results Table -->
      <div ref="scrollContainer" class="flex-1 overflow-y-auto">
        <table class="w-full text-4xl">
          <thead class="sticky top-0 bg-[var(--color-surface-raised)] shadow-sm z-10">
            <tr class="text-3xl font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
              <th class="px-2.5 py-1.5 text-left w-24">Type</th>
              <th class="px-2.5 py-1.5 text-left">Ledger Name</th>
              <th class="px-2.5 py-1.5 text-left">Mobile</th>
              <th class="px-2.5 py-1.5 text-left">Group</th>
              <th class="px-2.5 py-1.5 text-right">Balance</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr
              v-for="(c, idx) in results"
              :key="c.name"
              class="cursor-pointer transition-all border-l-4 border-transparent"
              :class="selectedIdx === idx ? 'bg-[var(--color-focus)] border-l-[var(--color-focus)] text-[var(--color-text-on-focus)] font-bold' : 'hover:bg-[var(--color-midlight)]/40'"
              @click="handleSelect(c)"
            >
              <td class="px-2.5 py-1.5">
                <span
                  class="px-2 py-0.5 rounded text-2xl font-bold uppercase tracking-tight"
                  :class="selectedIdx === idx ? 'bg-black/10 text-[var(--color-text-on-focus)]' : {
                    'bg-[var(--color-customer)]/20 text-[var(--color-customer)]': c.type === 'Customer',
                    'bg-[var(--color-supplier)]/20 text-[var(--color-supplier)]': c.type === 'Supplier',
                    'bg-[var(--color-employee)]/20 text-[var(--color-employee)]': c.type === 'Employee',
                    'bg-[var(--color-midlight)] text-[var(--color-text-muted)]': c.type === 'Account'
                  }"
                >
                  {{ c.type }}
                </span>
              </td>
              <td class="px-2.5 py-1.5">
                <div class="font-medium" :class="selectedIdx === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ c.label }}</div>
              </td>
              <td class="px-2.5 py-1.5">
                <div :class="selectedIdx === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ c.mobile_no || '--' }}</div>
              </td>
              <td class="px-2.5 py-1.5">
                <span
                  v-if="c.group"
                  class="px-2 py-0.5 rounded text-2xl font-semibold tracking-tight inline-block"
                  :class="selectedIdx === idx ? 'bg-black/10 text-[var(--color-text-on-focus)] border border-black/20' : getGroupBadgeClass(c)"
                >
                  {{ c.group }}
                </span>
                <span v-else :class="selectedIdx === idx ? 'text-[var(--color-text-on-focus)]/60' : 'text-[var(--color-text-muted)]/40'">--</span>
              </td>
              <td class="px-2.5 py-1.5 text-right">
                <span
                  class="font-bold whitespace-nowrap"
                  :class="selectedIdx === idx ? 'text-[var(--color-text-on-focus)]' : ((c.balance || 0) > 0 ? 'text-[var(--color-success)]' : (c.balance || 0) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]')"
                >
                  {{ Math.abs(c.balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                  <span class="text-xs font-normal uppercase ml-0.5">
                    {{ (c.balance || 0) > 0 ? 'DR' : (c.balance || 0) < 0 ? 'CR' : '' }}
                  </span>
                </span>
              </td>
            </tr>
            <tr v-if="!results.length && !loading">
              <td colspan="5" class="px-5 py-12 text-center text-[var(--color-text-muted)] text-xl italic">
                <span v-if="query">No ledgers found matching "{{ query }}"</span>
                <span v-else>No {{ activeType === 'All' ? '' : activeType }} ledgers found.</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Detail Panel -->
      <div v-if="results[selectedIdx]" class="border-t border-[var(--color-border)] bg-[var(--color-surface-raised)] px-8 py-6">
        <div class="flex items-start gap-4">
          <div class="flex flex-col shrink-0" style="width: 10%">
            <span class="text-sm font-bold uppercase text-[var(--color-text-muted)] truncate">Last Inv</span>
            <span class="text-xl font-semibold text-[var(--color-text)] truncate">
              {{ results[selectedIdx].last_invoice_date
                  ? new Date(results[selectedIdx].last_invoice_date).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: '2-digit' })
                  : 'None' }}
            </span>
          </div>
          <div class="flex flex-col shrink-0" style="width: 10%">
            <span class="text-sm font-bold uppercase text-[var(--color-text-muted)] truncate">WhatsApp</span>
            <span class="text-2xl font-semibold text-[var(--color-text)] truncate">{{ results[selectedIdx].whatsapp || '--' }}</span>
          </div>
          <div class="flex flex-col shrink-0" style="width: 20%">
            <span class="text-sm font-bold uppercase text-[var(--color-text-muted)] truncate">Email</span>
            <span class="text-xl font-semibold text-[var(--color-text)] truncate">{{ results[selectedIdx].email || '--' }}</span>
          </div>
          <div class="flex flex-col shrink-0" style="width: 45%">
            <span class="text-sm font-bold uppercase text-[var(--color-text-muted)] truncate">Address</span>
            <span class="text-xl text-[var(--color-text)] line-clamp-2 leading-tight">
              {{ getAddressFormatted(results[selectedIdx]) }}
            </span>
          </div>
          <div class="flex flex-col shrink-0" style="width: 15%">
            <span class="text-sm font-bold uppercase text-[var(--color-text-muted)] truncate">GSTIN</span>
            <span class="text-2xl font-semibold text-[var(--color-text)] font-mono truncate">{{ results[selectedIdx].gstin || '--' }}</span>
          </div>
        </div>
      </div>

      <!-- SUB-MODALS overlay -->
      <div
        v-if="showNewForm || showEditForm || showDateModal"
        class="absolute inset-0 z-[60] flex items-center justify-center bg-black/70"
        @click.self="handleEsc"
      >
        <!-- Date Range Sub-window -->
        <DateFilter
          v-if="showDateModal"
          :show="showDateModal"
          :customer-name="results[selectedIdx]?.label"
          @close="showDateModal = false"
          @confirm="handleDateConfirm"
        />

        <!-- Supplier Creator (New / Edit) -->
        <SupplierCreator
          v-else-if="(showNewForm || showEditForm) && formPartyType === 'Supplier'"
          ref="supplierCreatorRef"
          :show="true"
          :is-edit="showEditForm"
          :supplier-row="showEditForm ? results[selectedIdx] : null"
          @close="closeSubForm"
          @saved="onSupplierSaved"
        />

        <!-- Employee Creator (New / Edit) -->
        <EmployeeCreator
          v-else-if="(showNewForm || showEditForm) && formPartyType === 'Employee'"
          :show="true"
          :is-edit="showEditForm"
          :employee-row="showEditForm ? results[selectedIdx] : null"
          @close="closeSubForm"
          @saved="onEmployeeSaved"
        />

        <!-- Customer Creator (New / Edit) -->
        <CustomerCreator
          v-else-if="(showNewForm || showEditForm) && formPartyType === 'Customer'"
          ref="customerCreatorRef"
          :show="true"
          :is-edit="showEditForm"
          :customer-row="showEditForm ? results[selectedIdx] : null"
          :initial-name="newCustomerName"
          @close="closeSubForm"
          @saved="onCustomerSaved"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed, onMounted } from 'vue'
import { frappeGet } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { getUserRole } from '../composables/usePermission.js'
import DateFilter from './DateFilter.vue'
import CustomerCreator from './CustomerCreator.vue'
import SupplierCreator from './SupplierCreator.vue'
import EmployeeCreator from './EmployeeCreator.vue'

const props = defineProps({
  show: Boolean,
  skipDateFilter: { type: Boolean, default: false },
  initialType: { type: String, default: 'All' },
  allowedTypes: { type: Array, default: () => ['Customer', 'Supplier', 'Employee', 'Account'] },
  filterList: { type: Array, default: null },
  overrideLedgers: { type: Array, default: null },
  initialQuery: { type: String, default: '' }
})

const availableTabs = computed(() => [...new Set(['All', ...props.allowedTypes])])

const emit = defineEmits(['close', 'select'])

useSubwindowWatcher(computed(() => props.show))

// ─── State ────────────────────────────────────────────────────────────────────
const query        = ref('')
const allLedgers   = ref([])
const activeType   = ref(props.initialType)
const selectedIdx  = ref(0)
const loading      = ref(false)

const searchInput        = ref(null)
const scrollContainer    = ref(null)
const customerCreatorRef = ref(null)
const supplierCreatorRef = ref(null)

const showNewForm    = ref(false)
const showEditForm   = ref(false)
const showDateModal  = ref(false)
const formPartyType  = ref('Customer') // 'Customer' | 'Supplier' | 'Employee'
const newCustomerName = ref('')

// ─── Data Preloading ──────────────────────────────────────────────────────────
async function preloadLedger() {
  loading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.customersearch_api.get_all_ledgers')
    allLedgers.value = data || []
  } catch (e) {
    console.error('[CustomerSearchModal] Preload failed:', e)
  } finally {
    loading.value = false
  }
}

// ─── Filtering ────────────────────────────────────────────────────────────────
const results = computed(() => {
  const q = query.value.trim().toLowerCase()

  // When overrideLedgers is provided (e.g. row 2+ MOP accounts), use it directly
  if (props.overrideLedgers) {
    if (!q) return props.overrideLedgers
    return props.overrideLedgers.filter(l =>
      (l.label || '').toLowerCase().includes(q) ||
      (l.name || '').toLowerCase().includes(q)
    )
  }

  let list = allLedgers.value.filter(l => props.allowedTypes.includes(l.type))

  // Filter by allowed names if filterList is provided
  if (props.filterList && props.filterList.length > 0) {
    list = list.filter(l => props.filterList.includes(l.name))
  }

  // Admin and accounts role see all GL accounts — skip the Account filter entirely
  const _role = getUserRole()
  if (_role !== 'admin' && _role !== 'accounts') {

  // Build allowed Account set: user's MOP accounts (cash/card/bank/upi) UNION global visible_accounts.
  // If neither is configured, no Account filter is applied (show all).
  const userMopAccounts = [
    localStorage.getItem('wb-cash'),
    localStorage.getItem('wb-card'),
    localStorage.getItem('wb-bank'),
    localStorage.getItem('wb-upi'),
  ].filter(Boolean)

  let globalVisibleAccounts = []
  try {
    const raw = localStorage.getItem('wb-visible-accounts')
    if (raw) globalVisibleAccounts = JSON.parse(raw)
  } catch (_) { /* ignore malformed JSON */ }

  const allowedAccountSet = new Set([...userMopAccounts, ...globalVisibleAccounts])
  if (allowedAccountSet.size > 0) {
    list = list.filter(l => l.type !== 'Account' || allowedAccountSet.has(l.name))
  }

  } // end non-admin Account filter

  if (activeType.value !== 'All') list = list.filter(l => l.type === activeType.value)
  if (!q) return list
  return list.filter(l =>
    (l.label || '').toLowerCase().includes(q) ||
    (l.name || '').toLowerCase().includes(q) ||
    (l.mobile_no || '').includes(q) ||
    (l.whatsapp || '').includes(q) ||
    (l.gstin || '').toLowerCase().includes(q) ||
    (l.city || '').toLowerCase().includes(q) ||
    (l.email || '').toLowerCase().includes(q)
  )
})

watch([query, activeType], () => { selectedIdx.value = 0 })

watch(() => props.initialType, (val) => { activeType.value = val })

function getAddressFormatted(c) {
  if (c.type === 'Account') return 'General Accounting Ledger'
  if (c.type === 'Employee') return 'Employee Record'
  return [c.address_line1, c.city].filter(Boolean).join(', ') || 'No address provided'
}

// ─── Navigation & Events ──────────────────────────────────────────────────────
function handleEsc() {
  if (showNewForm.value || showEditForm.value || showDateModal.value) {
    closeSubForm()
  } else {
    emit('close')
  }
}

function handleGlobalKeydown(e) {
  if (showNewForm.value || showEditForm.value) {
    if (formPartyType.value === 'Customer' && e.key === 'End') {
      e.preventDefault()
      customerCreatorRef.value?.submit()
    }
    return
  }
  if (showDateModal.value) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIdx.value = Math.min(selectedIdx.value + 1, results.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIdx.value = Math.max(selectedIdx.value - 1, 0)
  } else if (e.key === 'Enter') {
    const item = results.value[selectedIdx.value]
    if (item) { e.preventDefault(); handleSelect(item) }
  } else if (e.key === 'F2') {
    e.preventDefault()
    if (activeType.value === 'Customer' || activeType.value === 'Supplier' || activeType.value === 'Employee') openNewForm()
  } else if (e.key === 'F3') {
    e.preventDefault()
    const item = results.value[selectedIdx.value]
    if (item && (item.type === 'Customer' || item.type === 'Supplier' || item.type === 'Employee')) openEditForm(item)
  } else if (e.key === 'F5') {
    e.preventDefault()
    preloadLedger()
  } else if (e.key === 'F7') {
    e.preventDefault()
    const types = availableTabs.value
    activeType.value = types[(types.indexOf(activeType.value) + 1) % types.length]
  } else if (e.key === 'PageUp') {
    e.preventDefault()
    searchInput.value?.focus()
    searchInput.value?.select()
  }
}

function handleSelect(item) {
  if (props.skipDateFilter) {
    emit('select', item)
  } else {
    showDateModal.value = true
  }
}

function handleDateConfirm(dates) {
  const item = results.value[selectedIdx.value]
  if (item) { showDateModal.value = false; emit('select', item, dates) }
}

function focus() {
  nextTick(() => {
    if (formPartyType.value === 'Customer' && (showNewForm.value || showEditForm.value)) {
      customerCreatorRef.value?.focusFirst()
    } else if (formPartyType.value === 'Supplier' && (showNewForm.value || showEditForm.value)) {
      supplierCreatorRef.value?.focusFirst()
    } else {
      searchInput.value?.focus()
      searchInput.value?.select()
    }
  })
}

defineExpose({ focus, closeSubForm })

watch(selectedIdx, async (idx) => {
  await nextTick()
  const container = scrollContainer.value
  const activeRow = container?.querySelector(`tbody tr:nth-child(${idx + 1})`)
  if (container && activeRow) {
    const rowTop = activeRow.offsetTop
    const rowBottom = rowTop + activeRow.offsetHeight
    const headerHeight = container.querySelector('thead')?.offsetHeight || 50
    if (rowTop < container.scrollTop + headerHeight) {
      container.scrollTop = rowTop - headerHeight
    } else if (rowBottom > container.scrollTop + container.offsetHeight) {
      container.scrollTop = rowBottom - container.offsetHeight
    }
  }
})

watch(() => props.show, (val) => {
  if (val) { query.value = props.initialQuery || ''; activeType.value = props.initialType; if (!props.overrideLedgers) preloadLedger(); focus() }
  else closeSubForm()
})

onMounted(() => {
  if (props.show) {
    query.value = props.initialQuery || ''
    activeType.value = props.initialType
    if (!props.overrideLedgers) preloadLedger()
    focus()
  }
})

// ─── Sub-Form: open / close ───────────────────────────────────────────────────
function openNewForm() {
  formPartyType.value = activeType.value === 'Supplier' ? 'Supplier' : activeType.value === 'Employee' ? 'Employee' : 'Customer'
  if (formPartyType.value === 'Customer') newCustomerName.value = query.value.trim()
  showNewForm.value = true
  focus()
}

function openEditForm(target) {
  if (!target || (target.type !== 'Customer' && target.type !== 'Supplier' && target.type !== 'Employee')) return
  formPartyType.value = target.type
  showEditForm.value = true
  focus()
}

function closeSubForm() {
  showNewForm.value = false
  showEditForm.value = false
  showDateModal.value = false
  focus()
}

// ─── Supplier saved callback ──────────────────────────────────────────────────
async function onSupplierSaved(result) {
  await preloadLedger()
  const savedName = result.name || result.supplier_name
  const foundIdx = results.value.findIndex(c => c.name === savedName)
  if (foundIdx !== -1) selectedIdx.value = foundIdx
  if (showNewForm.value) {
    handleSelect(results.value[selectedIdx.value])
  } else {
    closeSubForm()
  }
}

async function onEmployeeSaved(result) {
  await preloadLedger()
  const savedName = result.name || result.employee_name
  const foundIdx = results.value.findIndex(c => c.name === savedName)
  if (foundIdx !== -1) selectedIdx.value = foundIdx
  if (showNewForm.value) {
    handleSelect(results.value[selectedIdx.value])
  } else {
    closeSubForm()
  }
}

// ─── Customer saved callback ──────────────────────────────────────────────────
async function onCustomerSaved(result) {
  await preloadLedger()
  const savedName = result.name || result.customer_name
  const foundIdx = results.value.findIndex(c => c.name === savedName)
  if (foundIdx !== -1) selectedIdx.value = foundIdx
  if (showNewForm.value) {
    handleSelect(results.value[selectedIdx.value])
  } else {
    closeSubForm()
  }
}
function getGroupBadgeClass(c) {
  const group = (c.group || '').toLowerCase()
  const type = c.type

  // 1. Specific Group Name Overrides
  if (group.includes('wholesale')) {
    return 'bg-[var(--color-customer)]/20 text-[var(--color-customer)] border border-[var(--color-customer)]/50'
  }
  if (group.includes('retail')) {
    return 'bg-[var(--color-success)]/20 text-[var(--color-success)] border border-[var(--color-success)]/50'
  }
  if (group.includes('gst')) {
    return 'bg-[var(--color-danger)]/20 text-[var(--color-danger)] border border-[var(--color-danger)]/50'
  }
  if (group === 'all customer groups') {
    return 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] border border-[var(--color-border)]'
  }

  // 2. Default Type-based Fallbacks
  if (type === 'Customer') return 'bg-[var(--color-customer)]/20 text-[var(--color-customer)] border border-[var(--color-customer)]/50'
  if (type === 'Supplier') return 'bg-[var(--color-supplier)]/20 text-[var(--color-supplier)] border border-[var(--color-supplier)]/50'
  if (type === 'Employee') return 'bg-[var(--color-employee)]/20 text-[var(--color-employee)] border border-[var(--color-employee)]/50'
  return 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] border border-[var(--color-border)]'
}
</script>
