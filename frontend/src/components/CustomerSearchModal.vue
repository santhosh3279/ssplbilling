<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 outline-none"
    @keydown="handleGlobalKeydown"
    tabindex="-1"
  >
    <div class="flex h-[90vh] w-[95vw] flex-col rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden relative">
      <!-- Header -->
      <div class="border-b border-[var(--color-border)] px-5 py-4 flex items-center bg-[var(--color-surface-raised)]">
        <!-- Left: Title -->
        <div class="w-1/3">
          <div class="text-2xl font-semibold text-[var(--color-text)]">{{ title || 'Detailed Ledger Search' }}</div>
          <div class="text-lg text-[var(--color-text-muted)]">{{ subtitle || 'Search Customers, Suppliers, and Accounting Ledgers' }}</div>
        </div>

        <!-- Center: Quick Filter Tabs -->
        <div class="w-1/3 flex justify-center">
          <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-1 shadow-sm relative group">
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
        </div>

        <!-- Right: Actions -->
        <div class="w-1/3 flex items-center justify-end gap-3">
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

          <!-- Hide Secondary Toggle -->
          <div
            v-if="showHideSecondary"
            @click="hideSecondary = !hideSecondary"
            class="flex items-center gap-3 bg-[var(--color-bg)] px-4 py-2 rounded-lg border border-[var(--color-border)] shadow-sm mx-1 cursor-pointer select-none transition-colors hover:bg-[var(--color-surface-raised)]"
          >
            <span class="text-lg font-semibold uppercase tracking-wider" :class="hideSecondary ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)]'">Hide Secondary</span>
            <button
              class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none pointer-events-none"
              :class="hideSecondary ? 'bg-[var(--color-info)]' : 'bg-gray-400'"
            >
              <span
                class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                :class="hideSecondary ? 'translate-x-5' : 'translate-x-0'"
              ></span>
            </button>
          </div>

          <button
            @click="preloadLedger(true)"
            class="flex items-center gap-2 rounded-lg border border-[var(--color-highlight)] bg-[var(--color-highlight)]/10 px-4 py-2 text-lg font-semibold text-[var(--color-highlight)] transition-colors"
          >
            🔄 Refresh <kbd class="ml-1 rounded border border-[var(--color-highlight)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-xs text-[var(--color-highlight)]">F5</kbd>
          </button>
          <button @click="$emit('close')" class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)] ml-2">✕</button>
        </div>
      </div>

      <!-- Search input -->
      <div class="border-b border-[var(--color-border)] p-4 relative">
        <input
          ref="searchInput"
          v-model="query"
          class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/20"
          style="font-size: 27px; padding: 2.4px 3.2px;"
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
              <th class="px-2.5 py-1.5 text-left">Link</th>
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
              <td class="px-2.5 py-1.5">
                <div v-if="partyLinks[c.name]?.is_primary" class="flex flex-col gap-0.5">
                  <span
                    class="px-2 py-0.5 rounded text-xl font-bold uppercase tracking-tight inline-block w-fit"
                    :class="selectedIdx === idx ? 'bg-black/10 text-[var(--color-text-on-focus)] border border-black/20' : 'bg-[var(--color-info)]/20 text-[var(--color-info)] border border-[var(--color-info)]/30'"
                  >
                    Primary
                  </span>
                  <div v-if="partyLinks[c.name]?.links?.length" class="text-[10px] leading-tight opacity-70 italic truncate max-w-[120px]">
                    → {{ partyLinks[c.name].links[0].party }}
                  </div>
                </div>
                <div v-else-if="partyLinks[c.name]?.is_secondary" class="flex flex-col gap-0.5">
                  <span
                    class="px-2 py-0.5 rounded text-xl font-bold uppercase tracking-tight inline-block w-fit"
                    :class="selectedIdx === idx ? 'bg-black/10 text-[var(--color-text-on-focus)] border border-black/20' : 'bg-gray-500/20 text-gray-500 border border-gray-500/30'"
                  >
                    Secondary
                  </span>
                  <div v-if="partyLinks[c.name]?.links?.length" class="text-[10px] leading-tight opacity-70 italic truncate max-w-[120px]">
                    ← {{ partyLinks[c.name].links[0].party }}
                  </div>
                </div>
                <span v-else :class="selectedIdx === idx ? 'text-[var(--color-text-on-focus)]/40' : 'text-[var(--color-text-muted)]/20'">--</span>
              </td>
              <td class="px-2.5 py-1.5 text-right">
                <span
                  class="font-bold whitespace-nowrap"
                  :class="selectedIdx === idx ? 'text-[var(--color-text-on-focus)]' : (getDisplayBalance(c) > 0 ? 'text-[var(--color-success)]' : getDisplayBalance(c) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]')"
                >
                  {{ Math.abs(getDisplayBalance(c)).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                  <span class="text-xs font-normal uppercase ml-0.5">
                    {{ getDisplayBalance(c) > 0 ? 'DR' : getDisplayBalance(c) < 0 ? 'CR' : '' }}
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
            <span class="text-2xl font-bold uppercase text-[var(--color-text-muted)] truncate">Last Inv</span>
            <span class="text-4xl font-semibold text-[var(--color-text)] truncate">
              {{ results[selectedIdx].last_invoice_date
                  ? new Date(results[selectedIdx].last_invoice_date).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: '2-digit' })
                  : 'None' }}
            </span>
          </div>
          <div class="flex flex-col shrink-0" style="width: 10%">
            <span class="text-2xl font-bold uppercase text-[var(--color-text-muted)] truncate">WhatsApp</span>
            <span class="text-4xl font-semibold text-[var(--color-text)] truncate">{{ results[selectedIdx].whatsapp || '--' }}</span>
          </div>
          <div class="flex flex-col shrink-0" style="width: 20%">
            <span class="text-2xl font-bold uppercase text-[var(--color-text-muted)] truncate">Email</span>
            <span class="text-4xl font-semibold text-[var(--color-text)] truncate">{{ results[selectedIdx].email || '--' }}</span>
          </div>
          <div class="flex flex-col shrink-0" style="width: 45%">
            <span class="text-2xl font-bold uppercase text-[var(--color-text-muted)] truncate">Address</span>
            <span class="text-4xl text-[var(--color-text)] line-clamp-2 leading-tight">
              {{ getAddressFormatted(results[selectedIdx]) }}
            </span>
          </div>
          <div class="flex flex-col shrink-0" style="width: 15%">
            <span class="text-2xl font-bold uppercase text-[var(--color-text-muted)] truncate">GSTIN</span>
            <span class="text-4xl font-semibold text-[var(--color-text)] font-mono truncate">{{ results[selectedIdx].gstin || '--' }}</span>
          </div>
        </div>
      </div>

      <!-- SUB-MODALS overlay -->
      <div
        v-if="showNewForm || showEditForm || showDateModal"
        class="absolute inset-0 z-[60] flex items-center justify-center bg-black/70"
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
import { ref, nextTick, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { getUserRole } from '../composables/usePermission.js'
import { useLedgerCache } from '../services/ledgerCache.js'
import DateFilter from './DateFilter.vue'
import CustomerCreator from './CustomerCreator.vue'
import SupplierCreator from './SupplierCreator.vue'
import EmployeeCreator from './EmployeeCreator.vue'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  skipDateFilter: { type: Boolean, default: false },
  initialType: { type: String, default: 'All' },
  allowedTypes: { type: Array, default: () => ['Customer', 'Supplier', 'Employee', 'Account'] },
  filterList: { type: Array, default: null },
  overrideLedgers: { type: Array, default: null },
  initialQuery: { type: String, default: '' },
  hideSecondary: { type: Boolean, default: true },
  showHideSecondary: { type: Boolean, default: true }
})

const availableTabs = computed(() => {
  const types = props.allowedTypes
  if (types.length === 1) return types
  return [...new Set(['All', ...types])]
})

const emit = defineEmits(['close', 'select'])

useSubwindowWatcher(computed(() => props.show))

const router = useRouter()

// ─── State ────────────────────────────────────────────────────────────────────
const { ledgers: allLedgers, partyLinks, refreshLedgerCache, syncLoading } = useLedgerCache()
const query        = ref('')
const activeType   = ref(props.initialType)
const selectedIdx  = ref(0)
const loading      = computed(() => syncLoading.value)

const searchInput        = ref(null)
const scrollContainer    = ref(null)
const customerCreatorRef = ref(null)
const supplierCreatorRef = ref(null)

const showNewForm    = ref(false)
const showEditForm   = ref(false)
const showDateModal  = ref(false)
const isGlMode       = ref(false)
const formPartyType  = ref('Customer') // 'Customer' | 'Supplier' | 'Employee'
const newCustomerName = ref('')
const hideSecondary = ref(props.hideSecondary)

const savedQuery = ref('')
const savedActiveType = ref('All')
const savedSelectedName = ref(null)
const shouldRestoreState = ref(false)

// Update internal state if prop changes
watch(() => props.hideSecondary, (val) => {
  hideSecondary.value = val
})

// ─── Data Preloading ──────────────────────────────────────────────────────────
async function preloadLedger(force = false) {
  if (force || allLedgers.value.length === 0) {
    // Block if forced or if we have no data at all
    try {
      await refreshLedgerCache(force)
    } catch (e) {
      console.error('[CustomerSearchModal] Preload failed:', e)
    }
  } else {
    // Non-blocking background refresh to ensure latest data/balances
    refreshLedgerCache(force).catch(e => {
      console.warn('[CustomerSearchModal] Background refresh failed:', e)
    })
  }
}

// ─── Filtering ────────────────────────────────────────────────────────────────
const userRole = computed(() => getUserRole())

const isSameCompany = computed(() => {
  const wbCompany = localStorage.getItem('wb-company')
  const aeCompany = localStorage.getItem('ae-alternative_company')
  return wbCompany && aeCompany && wbCompany === aeCompany
})

function getDisplayBalance(c) {
  if (isSameCompany.value) {
    return c.alternative_balance || 0
  }
  return c.balance || 0
}

const allowedAccountSet = computed(() => {
  const role = userRole.value
  if (role === 'admin' || role === 'accounts') return null

  const accounts = [
    localStorage.getItem('wb-cash'),
    localStorage.getItem('wb-card'),
    localStorage.getItem('wb-bank'),
    localStorage.getItem('wb-upi'),
  ].filter(Boolean)

  try {
    const raw = localStorage.getItem('wb-visible-accounts')
    if (raw) accounts.push(...JSON.parse(raw))
  } catch (_) {}

  const allowed = new Set(accounts)

  if (isSameCompany.value) {
    const wbCompany = localStorage.getItem('wb-company')
    const wbAbbr = wbCompany === 'CHETTIYAR KADA' ? 'SSPL' : 'NCK'
    const altAbbr = wbCompany === 'CHETTIYAR KADA' ? 'NCK' : 'SSPL'

    accounts.forEach(acc => {
      if (acc.endsWith(` - ${wbAbbr}`)) {
        const altAcc = acc.replace(` - ${wbAbbr}`, ` - ${altAbbr}`)
        allowed.add(altAcc)
      }
    })
  }

  return allowed
})

function tokenMatch(l, fields, tokens) {
  if (tokens.length === 0) return true
  
  const words = []
  for (const f of fields) {
    const val = l[f]
    if (val) {
      const fieldWords = String(val).toLowerCase().split(/[^a-zA-Z0-9]+/).filter(Boolean)
      words.push(...fieldWords)
    }
  }
  
  return tokens.every(t => words.some(w => w.startsWith(t)))
}

// Rank based on ledger activity only (busiest ledgers first).
const byActivity = (a, b) => {
  const diff = (b.activity || 0) - (a.activity || 0)
  if (diff !== 0) return diff
  return (a.label || '').localeCompare(b.label || '')
}

const TYPE_PRIORITY = { Customer: 0, Supplier: 1 }

// Sub-sorts the top 3 activity ledgers: Customer first, Supplier second, and Accounts/others third.
function applyTopThreeSubSort(list) {
  if (list.length <= 1) return list
  const count = Math.min(3, list.length)
  const topThree = list.slice(0, count)
  const remainder = list.slice(count)

  topThree.sort((a, b) => {
    const pa = TYPE_PRIORITY[a.type] ?? 2
    const pb = TYPE_PRIORITY[b.type] ?? 2
    if (pa !== pb) return pa - pb
    
    // Preserve activity ranking if types are equal
    const actDiff = (b.activity || 0) - (a.activity || 0)
    if (actDiff !== 0) return actDiff
    return (a.label || '').localeCompare(b.label || '')
  })

  return [...topThree, ...remainder]
}

const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  const tokens = q ? q.split(/\s+/) : []

  // When overrideLedgers is provided (e.g. row 2+ MOP accounts), use it directly
  if (props.overrideLedgers) {
    if (tokens.length === 0) return props.overrideLedgers.slice(0, 100)
    return props.overrideLedgers
      .filter(l => tokenMatch(l, ['label', 'name'], tokens))
      .slice(0, 100)
  }

  let list = allLedgers.value.filter(l => props.allowedTypes.includes(l.type))

  // Filter by allowed names if filterList is provided
  if (props.filterList && props.filterList.length > 0) {
    list = list.filter(l => props.filterList.includes(l.name))
  }

  // Account visibility filter
  const allowedSet = allowedAccountSet.value
  if (allowedSet && allowedSet.size > 0) {
    list = list.filter(l => l.type !== 'Account' || allowedSet.has(l.name))
  }

  if (activeType.value !== 'All') {
    list = list.filter(l => l.type === activeType.value)
  }

  // Party Link Filter: Toggle to hide secondary parties
  if (hideSecondary.value) {
    list = list.filter(l => !partyLinks.value[l.name]?.is_secondary)
  }

  if (tokens.length === 0) {
    const sorted = list.sort(byActivity)
    return applyTopThreeSubSort(sorted).slice(0, 100)
  }

  const searchFields = ['label', 'name', 'mobile_no', 'whatsapp', 'gstin', 'city', 'email']
  const filtered = list.filter(l => tokenMatch(l, searchFields, tokens)).sort(byActivity)
  return applyTopThreeSubSort(filtered).slice(0, 100)
})

watch([query, activeType], () => {
  if (!shouldRestoreState.value) {
    selectedIdx.value = 0
  }
})

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

  if (e.key === 'Delete') {
    e.preventDefault()
    query.value = ''
    focus()
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIdx.value = Math.min(selectedIdx.value + 1, results.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIdx.value = Math.max(selectedIdx.value - 1, 0)
  } else if (e.key === 'Home') {
    e.preventDefault()
    selectedIdx.value = 0
  } else if (e.key === 'End') {
    e.preventDefault()
    selectedIdx.value = results.value.length - 1
  } else if (e.key === 'Enter') {
    const item = results.value[selectedIdx.value]
    if (item) {
      e.preventDefault()
      if (props.skipDateFilter) {
        handleSelect(item)
      } else {
        isGlMode.value = true
        showDateModal.value = true
      }
    }
  } else if (e.key === 'F2') {
    e.preventDefault()
    if (activeType.value === 'Customer' || activeType.value === 'Supplier' || activeType.value === 'Employee') openNewForm()
  } else if (e.key === 'F3') {
    e.preventDefault()
    const item = results.value[selectedIdx.value]
    if (item && (item.type === 'Customer' || item.type === 'Supplier' || item.type === 'Employee')) openEditForm(item)
  } else if (e.key === 'F4') {
    e.preventDefault()
    const item = results.value[selectedIdx.value]
    if (item) {
      isGlMode.value = true
      showDateModal.value = true
    }
  } else if (e.key === 'F5') {
    e.preventDefault()
    preloadLedger(true)
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
  // Enter or Click now always performs immediate selection (e.g., for the invoice or default ledger view)
  emit('select', item)
}

function handleDateConfirm(dates) {
  const item = results.value[selectedIdx.value]
  if (item) {
    // Save state before closing to open General Ledger
    savedQuery.value = query.value
    savedActiveType.value = activeType.value
    savedSelectedName.value = item.name
    shouldRestoreState.value = true

    // Date confirmation now always results in opening the General Ledger subwindow (only triggered via F4)
    showDateModal.value = false
    isGlMode.value = false
    
    window.dispatchEvent(new CustomEvent('wb-open-general-ledger', {
      detail: {
        party: item.name,
        party_type: item.type,
        label: item.label,
        from: dates.from,
        to: dates.to
      }
    }))
    
    emit('close')
  }
}

function focus() {
  nextTick(() => {
    if (formPartyType.value === 'Customer' && (showNewForm.value || showEditForm.value)) {
      customerCreatorRef.value?.focusFirst()
    } else if (formPartyType.value === 'Supplier' && (showNewForm.value || showEditForm.value)) {
      supplierCreatorRef.value?.focusFirst()
    } else {
      searchInput.value?.focus()
      if (query.value && query.value.length === 1) {
        const len = searchInput.value.value.length
        searchInput.value.setSelectionRange(len, len)
      } else {
        searchInput.value?.select()
      }
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
  if (val) {
    if (shouldRestoreState.value) {
      query.value = savedQuery.value
      activeType.value = savedActiveType.value
      
      nextTick(() => {
        if (savedSelectedName.value) {
          const idx = results.value.findIndex(c => c.name === savedSelectedName.value)
          if (idx !== -1) {
            selectedIdx.value = idx
          }
        }
        shouldRestoreState.value = false
      })
    } else {
      query.value = props.initialQuery || ''
      activeType.value = props.initialType
    }
    
    if (!props.overrideLedgers) preloadLedger()
    focus()
  } else {
    closeSubForm()
  }
})

function handleWindowKeyDown(e) {
  if (!props.show) return

  // If a subform/creator/date filter is open, let its inputs and shortcuts handle it
  if (showNewForm.value || showEditForm.value || showDateModal.value) return

  const target = e.target
  const isInteractive = target && (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.tagName === 'SELECT' ||
    target.tagName === 'BUTTON' ||
    target.isContentEditable
  )

  // If focus is already on an interactive element other than searchInput, don't hijack it
  if (isInteractive && target !== searchInput.value) return

  // printable keys
  const isPrintable = e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey
  const isBackspaceOrDelete = e.key === 'Backspace' || e.key === 'Delete'

  if (isPrintable || isBackspaceOrDelete) {
    if (document.activeElement !== searchInput.value) {
      searchInput.value?.focus()
    }
    return
  }

  // navigation / actions
  const navKeys = ['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', 'Escape', 'F2', 'F3', 'F4', 'F5', 'F7', 'PageUp']
  if (navKeys.includes(e.key)) {
    if (document.activeElement !== searchInput.value) {
      handleGlobalKeydown(e)
    }
  }
}

onMounted(() => {
  if (props.show) {
    query.value = props.initialQuery || ''
    activeType.value = props.initialType
    if (!props.overrideLedgers) preloadLedger()
    focus()
  }
  window.addEventListener('keydown', handleWindowKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleWindowKeyDown)
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
  await preloadLedger(true)
  const savedName = result.name || result.supplier_name
  const foundItem = allLedgers.value.find(c => c.name === savedName)
  if (showNewForm.value) {
    if (foundItem) {
      handleSelect(foundItem)
    } else {
      handleSelect({
        name: result.name,
        label: result.supplier_name || result.name,
        type: 'Supplier',
        mobile_no: result.mobile_no || '',
        email: result.email_id || '',
        gstin: result.gstin || '',
        group: result.supplier_group || '',
        balance: 0,
      })
    }
  } else {
    const foundIdx = results.value.findIndex(c => c.name === savedName)
    if (foundIdx !== -1) selectedIdx.value = foundIdx
    closeSubForm()
  }
}

async function onEmployeeSaved(result) {
  await preloadLedger(true)
  const savedName = result.name || result.employee_name
  const foundItem = allLedgers.value.find(c => c.name === savedName)
  if (showNewForm.value) {
    if (foundItem) {
      handleSelect(foundItem)
    } else {
      handleSelect({
        name: result.name,
        label: result.employee_name || result.name,
        type: 'Employee',
        mobile_no: result.cell_number || '',
        email: result.personal_email || '',
        gstin: '',
        group: result.department || '',
        balance: 0,
      })
    }
  } else {
    const foundIdx = results.value.findIndex(c => c.name === savedName)
    if (foundIdx !== -1) selectedIdx.value = foundIdx
    closeSubForm()
  }
}

// ─── Customer saved callback ──────────────────────────────────────────────────
async function onCustomerSaved(result) {
  await preloadLedger(true)
  const savedName = result.name || result.customer_name
  const foundItem = allLedgers.value.find(c => c.name === savedName)
  if (showNewForm.value) {
    if (foundItem) {
      handleSelect(foundItem)
    } else {
      handleSelect({
        name: result.name,
        label: result.customer_name || result.name,
        type: 'Customer',
        mobile_no: result.mobile_no || '',
        email: result.email_id || '',
        gstin: result.gstin || '',
        group: result.customer_group || '',
        pricelist_multiplication_factor: result.pricelist_multiplication_factor || 1.0,
        balance: 0,
      })
    }
  } else {
    const foundIdx = results.value.findIndex(c => c.name === savedName)
    if (foundIdx !== -1) selectedIdx.value = foundIdx
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
