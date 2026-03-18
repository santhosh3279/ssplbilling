<template>
  <div class="min-h-screen bg-slate-900 text-slate-200">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-slate-600">|</span>
        <span class="text-sm font-semibold text-slate-200">Pricing Rules</span>
        <span v-if="dirtyCount" class="rounded-full bg-amber-600 px-2 py-0.5 text-xs font-bold text-white">{{ dirtyCount }} unsaved</span>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="lastSync" class="text-xs text-slate-500">Last sync: {{ lastSyncLabel }}</span>
        <button
          v-if="dirtyCount"
          @click="saveAll"
          :disabled="saving"
          class="flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-700 disabled:opacity-50"
        >
          <span v-if="saving" class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          {{ saving ? 'Saving...' : 'Save All' }}
        </button>
        <button
          @click="showNewModal = true"
          class="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
        >+ New Rule</button>
        <button
          @click="fetchRules"
          :disabled="loading"
          class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50"
        >
          <span v-if="loading" class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          <span v-else>🔄</span>
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
    </header>

    <!-- New Rule Modal -->
    <div v-if="showNewModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60" @click.self="showNewModal = false">
      <div class="w-[500px] rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-2xl">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-base font-bold text-slate-200">New Pricing Rule</h2>
          <button @click="showNewModal = false" class="text-slate-500 hover:text-slate-300">✕</button>
        </div>
        <div class="max-h-[70vh] overflow-y-auto space-y-3 pr-1">

          <!-- Row 1: Price/Product + Apply On -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Discount Type</label>
              <select v-model="newRule.price_or_product_discount" class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500">
                <option value="Price">Price</option>
                <option value="Product">Product</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Apply On</label>
              <select v-model="newRule.apply_on" class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500">
                <option>Item Code</option>
                <option>Item Group</option>
                <option>Brand</option>
                <option>Transaction</option>
              </select>
            </div>
          </div>

          <!-- Item codes -->
          <div v-if="newRule.apply_on === 'Item Code'">
            <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Item Codes (comma-separated)</label>
            <input v-model="newRule.item_codes_raw" type="text" placeholder="e.g. ITEM-001, ITEM-002"
              class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
          </div>

          <!-- Row 2: Rate/Discount type + value + priority (only for Price) -->
          <div v-if="newRule.price_or_product_discount === 'Price'" class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Rate / Discount</label>
              <select v-model="newRule.rate_or_discount" class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500">
                <option>Discount Percentage</option>
                <option>Rate</option>
                <option>Discount Amount</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">
                {{ newRule.rate_or_discount === 'Discount Percentage' ? 'Discount %' : newRule.rate_or_discount === 'Rate' ? 'Rate ₹' : 'Discount Amt ₹' }}
              </label>
              <input
                v-model.number="newRule.rate_or_discount === 'Discount Percentage' ? newRule.discount_percentage : newRule.rate_or_discount === 'Rate' ? newRule.rate : newRule.discount_amount"
                type="number" min="0" step="0.01"
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
            </div>
          </div>

          <!-- Row 3: Warehouse + Priority -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Warehouse</label>
              <input v-model="newRule.warehouse" type="text" placeholder="Leave blank for all"
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Priority</label>
              <input v-model.number="newRule.priority" type="number" min="1"
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
            </div>
          </div>

          <!-- Row 4: Qty range -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Min Qty</label>
              <input v-model.number="newRule.min_qty" type="number" min="0"
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Max Qty</label>
              <input v-model.number="newRule.max_qty" type="number" min="0"
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
            </div>
          </div>

          <!-- Row 5: Validity -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Valid From</label>
              <input v-model="newRule.valid_from" type="date"
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Valid Until</label>
              <input v-model="newRule.valid_upto" type="date"
                class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
            </div>
          </div>

          <!-- Row 6: Party / Applicable For -->
          <div class="border-t border-slate-700 pt-3">
            <div class="mb-2 text-xs font-bold uppercase text-slate-500">Party Information</div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1 block text-xs font-bold uppercase text-slate-500">Applicable For</label>
                <select v-model="newRule.applicable_for" class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500">
                  <option value="">— All —</option>
                  <option value="Customer">Customer</option>
                  <option value="Customer Group">Customer Group</option>
                  <option value="Territory">Territory</option>
                  <option value="Sales Partner">Sales Partner</option>
                  <option value="Campaign">Campaign</option>
                </select>
              </div>
              <div v-if="newRule.applicable_for">
                <label class="mb-1 block text-xs font-bold uppercase text-slate-500">{{ newRule.applicable_for }}</label>
                <input v-model="newRule.party_value" type="text" :placeholder="'Enter ' + newRule.applicable_for"
                  class="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
              </div>
            </div>
          </div>

        </div>

        <div class="mt-5 flex justify-end gap-3">
          <button @click="showNewModal = false" class="rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700">Cancel</button>
          <button @click="createRule" :disabled="creating"
            class="rounded-lg bg-emerald-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50">
            {{ creating ? 'Creating...' : 'Create Rule' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="px-6 py-6">

      <!-- Filter -->
      <div class="mb-4 flex items-center gap-3">
        <input
          v-model="search"
          type="text"
          placeholder="Search by rule name or item code..."
          class="w-80 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
        />
        <span class="text-sm text-slate-500">{{ filteredRules.length }} of {{ rules.length }} rule{{ rules.length !== 1 ? 's' : '' }}</span>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto rounded-xl border border-slate-700">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-700 bg-slate-800 text-xs font-bold uppercase tracking-wider text-slate-400">
              <th class="px-3 py-3 text-left">Rule Name</th>
              <th class="px-3 py-3 text-left">Apply On / Items</th>
              <th class="px-3 py-3 text-left">Customer</th>
              <th class="px-3 py-3 text-center">Type</th>
              <th class="px-3 py-3 text-right">Discount %</th>
              <th class="px-3 py-3 text-right">Rate ₹</th>
              <th class="px-3 py-3 text-center">Min Qty</th>
              <th class="px-3 py-3 text-center">Max Qty</th>
              <th class="px-3 py-3 text-center">Valid From</th>
              <th class="px-3 py-3 text-center">Valid Until</th>
              <th class="px-3 py-3 text-center">Active</th>
              <th class="px-3 py-3 text-center">Save</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !rules.length">
              <td colspan="12" class="px-4 py-8 text-center text-slate-500">Loading pricing rules...</td>
            </tr>
            <tr v-else-if="!filteredRules.length">
              <td colspan="12" class="px-4 py-8 text-center text-slate-500">
                {{ rules.length ? 'No rules match search' : 'No pricing rules found. Click Refresh.' }}
              </td>
            </tr>
            <tr
              v-for="rule in filteredRules"
              :key="rule.name"
              class="border-b border-slate-800 transition-colors"
              :class="dirty[rule.name] ? 'bg-amber-900/10' : 'hover:bg-slate-800/40'"
            >
              <!-- Rule Name -->
              <td class="px-3 py-2 font-medium text-slate-200 max-w-[180px]">
                <div class="truncate" :title="rule.name">{{ rule.name }}</div>
              </td>

              <!-- Apply On / Items -->
              <td class="px-3 py-2">
                <div class="text-xs text-slate-500 mb-0.5">{{ rule.apply_on }}</div>
                <div v-if="rule.item_codes && rule.item_codes.length" class="flex flex-wrap gap-1">
                  <span v-for="code in rule.item_codes.slice(0, 2)" :key="code"
                    class="rounded bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">{{ code }}</span>
                  <span v-if="rule.item_codes.length > 2" class="text-[10px] text-slate-500">+{{ rule.item_codes.length - 2 }}</span>
                </div>
                <span v-else class="text-xs text-slate-600">All Items</span>
              </td>

              <!-- Customer -->
              <td class="px-3 py-2 text-xs text-slate-400">
                <span v-if="rule.applicable_for === 'Customer' && rule.customer">{{ rule.customer }}</span>
                <span v-else-if="rule.applicable_for === 'Customer Group' && rule.customer_group">{{ rule.customer_group }}</span>
                <span v-else class="text-slate-600">—</span>
              </td>

              <!-- Type badge -->
              <td class="px-3 py-2 text-center">
                <span class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase whitespace-nowrap" :class="{
                  'bg-amber-900/50 text-amber-300': rule.rate_or_discount === 'Discount Percentage',
                  'bg-emerald-900/50 text-emerald-300': rule.rate_or_discount === 'Rate',
                  'bg-blue-900/50 text-blue-300': rule.rate_or_discount === 'Discount Amount',
                }">{{ rule.rate_or_discount }}</span>
              </td>

              <!-- Discount % -->
              <td class="px-3 py-2 text-right">
                <input
                  v-if="rule.rate_or_discount === 'Discount Percentage'"
                  type="number" min="0" max="100" step="0.5"
                  v-model.number="rule.discount_percentage"
                  @input="markDirty(rule.name)"
                  class="w-20 rounded border border-slate-600 bg-slate-800 px-2 py-1 text-right font-mono text-amber-300 outline-none focus:border-amber-500"
                />
                <span v-else class="text-slate-600">—</span>
              </td>

              <!-- Rate -->
              <td class="px-3 py-2 text-right">
                <input
                  v-if="rule.rate_or_discount === 'Rate'"
                  type="number" min="0" step="0.01"
                  v-model.number="rule.rate"
                  @input="markDirty(rule.name)"
                  class="w-24 rounded border border-slate-600 bg-slate-800 px-2 py-1 text-right font-mono text-emerald-300 outline-none focus:border-emerald-500"
                />
                <span v-else class="text-slate-600">—</span>
              </td>

              <!-- Min Qty -->
              <td class="px-3 py-2 text-center">
                <input
                  type="number" min="0" step="1"
                  v-model.number="rule.min_qty"
                  @input="markDirty(rule.name)"
                  class="w-16 rounded border border-slate-600 bg-slate-800 px-2 py-1 text-center font-mono text-slate-300 outline-none focus:border-blue-500"
                />
              </td>

              <!-- Max Qty -->
              <td class="px-3 py-2 text-center">
                <input
                  type="number" min="0" step="1"
                  v-model.number="rule.max_qty"
                  @input="markDirty(rule.name)"
                  class="w-16 rounded border border-slate-600 bg-slate-800 px-2 py-1 text-center font-mono text-slate-300 outline-none focus:border-blue-500"
                />
              </td>

              <!-- Valid From -->
              <td class="px-3 py-2 text-center">
                <input
                  type="date"
                  v-model="rule.valid_from"
                  @input="markDirty(rule.name)"
                  class="rounded border border-slate-600 bg-slate-800 px-2 py-1 text-xs text-slate-300 outline-none focus:border-blue-500"
                />
              </td>

              <!-- Valid Until -->
              <td class="px-3 py-2 text-center">
                <input
                  type="date"
                  v-model="rule.valid_upto"
                  @input="markDirty(rule.name)"
                  class="rounded border border-slate-600 bg-slate-800 px-2 py-1 text-xs text-slate-300 outline-none focus:border-blue-500"
                />
              </td>

              <!-- Active toggle -->
              <td class="px-3 py-2 text-center">
                <button
                  @click="toggleDisable(rule)"
                  class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase transition-colors"
                  :class="rule.disable ? 'bg-red-900/50 text-red-400 hover:bg-red-900/70' : 'bg-green-900/50 text-green-400 hover:bg-green-900/70'"
                >{{ rule.disable ? 'Off' : 'On' }}</button>
              </td>

              <!-- Save button -->
              <td class="px-3 py-2 text-center">
                <button
                  v-if="dirty[rule.name]"
                  @click="saveRule(rule)"
                  :disabled="savingRow[rule.name]"
                  class="rounded bg-amber-600 px-2 py-1 text-xs font-bold text-white transition hover:bg-amber-700 disabled:opacity-50"
                >{{ savingRow[rule.name] ? '...' : 'Save' }}</button>
                <span v-else class="text-slate-700">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { useItemCache } from '../services/itemCache.js'

const router = useRouter()
const { pricingRules, refreshItemCache, lastSync } = useItemCache()

const rules = ref([])
const loading = ref(false)
const saving = ref(false)
const creating = ref(false)
const showNewModal = ref(false)
const savingRow = reactive({})
const dirty = reactive({})
const search = ref('')

const defaultNewRule = () => ({
  price_or_product_discount: 'Price',
  apply_on: 'Item Code',
  item_codes_raw: '',
  rate_or_discount: 'Discount Percentage',
  discount_percentage: 0,
  rate: 0,
  discount_amount: 0,
  warehouse: '',
  min_qty: 0,
  max_qty: 0,
  valid_from: '',
  valid_upto: '',
  priority: 1,
  applicable_for: '',
  party_value: '',
})
const newRule = ref(defaultNewRule())

const lastSyncLabel = computed(() => {
  if (!lastSync.value) return ''
  return new Date(lastSync.value).toLocaleTimeString()
})

const dirtyCount = computed(() => Object.values(dirty).filter(Boolean).length)

const filteredRules = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return rules.value
  return rules.value.filter(r =>
    r.name.toLowerCase().includes(q) ||
    (r.item_codes || []).some(c => c.toLowerCase().includes(q)) ||
    (r.customer || '').toLowerCase().includes(q)
  )
})

function markDirty(name) {
  dirty[name] = true
}

function toggleDisable(rule) {
  rule.disable = rule.disable ? 0 : 1
  markDirty(rule.name)
}

async function saveRule(rule) {
  savingRow[rule.name] = true
  try {
    await frappePost('ssplbilling.api.itemsearch_api.save_pricing_rule', {
      name: rule.name,
      discount_percentage: rule.discount_percentage,
      rate: rule.rate,
      discount_amount: rule.discount_amount,
      min_qty: rule.min_qty,
      max_qty: rule.max_qty,
      valid_from: rule.valid_from || '',
      valid_upto: rule.valid_upto || '',
      disable: rule.disable,
    })
    dirty[rule.name] = false
  } catch (e) {
    alert('Save failed: ' + (e?.message || e))
  } finally {
    savingRow[rule.name] = false
  }
}

async function saveAll() {
  saving.value = true
  const dirtyRules = rules.value.filter(r => dirty[r.name])
  await Promise.all(dirtyRules.map(saveRule))
  saving.value = false
  // Refresh item cache so runtime rules are up to date
  await refreshItemCache('Sales')
}

async function createRule() {
  creating.value = true
  try {
    const item_codes = newRule.value.item_codes_raw
      .split(',').map(s => s.trim()).filter(Boolean)
    // Map applicable_for to the correct party field
    const partyFields = {}
    if (newRule.value.applicable_for && newRule.value.party_value) {
      const fieldMap = {
        'Customer': 'customer', 'Customer Group': 'customer_group',
        'Territory': 'territory', 'Sales Partner': 'sales_partner', 'Campaign': 'campaign',
      }
      const field = fieldMap[newRule.value.applicable_for]
      if (field) partyFields[field] = newRule.value.party_value
    }
    await frappePost('ssplbilling.api.itemsearch_api.create_pricing_rule', {
      price_or_product_discount: newRule.value.price_or_product_discount,
      apply_on: newRule.value.apply_on,
      item_codes: JSON.stringify(item_codes),
      rate_or_discount: newRule.value.rate_or_discount,
      discount_percentage: newRule.value.discount_percentage,
      rate: newRule.value.rate,
      discount_amount: newRule.value.discount_amount,
      warehouse: newRule.value.warehouse || '',
      min_qty: newRule.value.min_qty,
      max_qty: newRule.value.max_qty,
      valid_from: newRule.value.valid_from || '',
      valid_upto: newRule.value.valid_upto || '',
      priority: newRule.value.priority,
      applicable_for: newRule.value.applicable_for || '',
      ...partyFields,
    })
    showNewModal.value = false
    newRule.value = defaultNewRule()
    await fetchRules()
  } catch (e) {
    alert('Create failed: ' + (e?.message || e))
  } finally {
    creating.value = false
  }
}

async function fetchRules() {
  loading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.itemsearch_api.get_pricing_rules')
    rules.value = (data || []).map(r => ({ ...r }))
    Object.keys(dirty).forEach(k => delete dirty[k])
    // Sync into item cache
    pricingRules.value = rules.value
  } catch (e) {
    console.error('Pricing rule fetch failed:', e)
  } finally {
    loading.value = false
  }
}

// Load on mount
if (pricingRules.value.length) {
  rules.value = pricingRules.value.map(r => ({ ...r }))
} else {
  fetchRules()
}
</script>
