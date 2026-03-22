<template>
  <div class="min-h-screen bg-slate-900 text-slate-200">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-slate-600">|</span>
        <span class="text-sm font-semibold text-slate-200">Discount Rules</span>
        <span class="ml-1 rounded-full bg-slate-700 px-2 py-0.5 text-xs text-slate-400">{{ discountRules.length }}</span>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="lastSync" class="text-xs text-slate-500">Last sync: {{ lastSyncLabel }}</span>
        <button
          @click="fetchDiscountRules"
          :disabled="loading"
          class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50"
        >
          <span v-if="loading" class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          <span v-else>🔄</span>
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
    </header>

    <!-- Content -->
    <div class="px-6 py-6">
      <!-- Filter -->
      <div class="mb-4 flex items-center gap-3">
        <input
          v-model="search"
          type="text"
          placeholder="Search by rule name, item or product group..."
          class="w-80 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
        />
        <span class="text-sm text-slate-500">{{ filteredRules.length }} of {{ discountRules.length }} rule{{ discountRules.length !== 1 ? 's' : '' }}</span>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto rounded-xl border border-slate-700">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-700 bg-slate-800 text-xs font-bold uppercase tracking-wider text-slate-400">
              <th class="px-3 py-3 text-left">Rule Name</th>
              <th class="px-3 py-3 text-left">Price List</th>
              <th class="px-3 py-3 text-center">Discount Type</th>
              <th class="px-3 py-3 text-left">Scope</th>
              <th class="px-3 py-3 text-center">Start Date</th>
              <th class="px-3 py-3 text-center">End Date</th>
              <th class="px-3 py-3 text-center">Min Qty</th>
              <th class="px-3 py-3 text-center">Free Qty</th>
              <th class="px-3 py-3 text-center">Recursive</th>
              <th class="px-3 py-3 text-right">Disc %</th>
              <th class="px-3 py-3 text-left">Custom Logic</th>
              <th class="px-3 py-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !discountRules.length">
              <td colspan="12" class="px-4 py-8 text-center text-slate-500">Loading discount rules...</td>
            </tr>
            <tr v-else-if="!filteredRules.length">
              <td colspan="12" class="px-4 py-8 text-center text-slate-500">
                {{ discountRules.length ? 'No rules match search' : 'No discount rules found. Add them in Frappe Desk → Discount Rule.' }}
              </td>
            </tr>
            <tr
              v-for="rule in filteredRules"
              :key="rule.name"
              class="border-b border-slate-800 hover:bg-slate-800/40 transition-colors"
            >
              <!-- Rule Name -->
              <td class="px-3 py-2 font-medium text-slate-200 max-w-[180px]">
                <div class="truncate" :title="rule.rule_name">{{ rule.rule_name }}</div>
              </td>

              <!-- Price List -->
              <td class="px-3 py-2 text-xs text-slate-400">{{ rule.price_list || '—' }}</td>

              <!-- Discount Type badge -->
              <td class="px-3 py-2 text-center">
                <span class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase whitespace-nowrap" :class="{
                  'bg-purple-900/50 text-purple-300': rule.discount_type === 'Product Discount',
                  'bg-amber-900/50 text-amber-300': rule.discount_type === 'Percentage Discount',
                  'bg-blue-900/50 text-blue-300': rule.discount_type === 'Custom Logic',
                }">{{ rule.discount_type || '—' }}</span>
              </td>

              <!-- Scope -->
              <td class="px-3 py-2 text-xs text-slate-400 max-w-[200px]">
                <div v-if="rule.applies_to === 'Product Group'" class="flex items-center gap-1">
                  <span class="text-slate-500">Group:</span>
                  <span class="font-medium text-slate-300">{{ rule.product_group || '—' }}</span>
                </div>
                <div v-else-if="rule.applies_to === 'Item Code' && rule.items && rule.items.length" class="flex flex-wrap gap-1">
                  <span v-for="item in rule.items.slice(0, 2)" :key="item.item_code"
                    class="rounded bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300" :title="item.item_name">
                    {{ item.item_code }}
                  </span>
                  <span v-if="rule.items.length > 2" class="text-[10px] text-slate-500">+{{ rule.items.length - 2 }}</span>
                </div>
                <span v-else class="text-slate-600">All Items</span>
              </td>

              <!-- Start Date -->
              <td class="px-3 py-2 text-center text-xs text-slate-400">{{ rule.start_date || '—' }}</td>

              <!-- End Date -->
              <td class="px-3 py-2 text-center text-xs text-slate-400">{{ rule.end_date || '—' }}</td>

              <!-- Min Qty -->
              <td class="px-3 py-2 text-center font-mono text-slate-300">{{ rule.min_quantity || '—' }}</td>

              <!-- Free Qty — Product Discount only -->
              <td class="px-3 py-2 text-center font-mono text-slate-300">
                <span v-if="rule.discount_type === 'Product Discount'">{{ rule.free_quantity || '—' }}</span>
                <span v-else class="text-slate-700">—</span>
              </td>

              <!-- Recursive — Product Discount only -->
              <td class="px-3 py-2 text-center">
                <span v-if="rule.discount_type === 'Product Discount'"
                  class="rounded-full px-2 py-0.5 text-[10px] font-bold"
                  :class="rule.recursive ? 'bg-green-900/50 text-green-400' : 'bg-slate-800 text-slate-600'"
                >{{ rule.recursive ? 'Yes' : 'No' }}</span>
                <span v-else class="text-slate-700">—</span>
              </td>

              <!-- Disc % — Percentage Discount only -->
              <td class="px-3 py-2 text-right font-mono">
                <span v-if="rule.discount_type === 'Percentage Discount'" class="text-amber-300">
                  {{ rule.percentage_discount ? rule.percentage_discount + '%' : '—' }}
                </span>
                <span v-else class="text-slate-700">—</span>
              </td>

              <!-- Custom Logic — type badge + conditional mini-table -->
              <td class="px-3 py-2 text-xs min-w-[160px]">
                <template v-if="rule.discount_type === 'Custom Logic'">
                  <!-- Type badge -->
                  <div class="mb-1">
                    <span class="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase"
                      :class="rule.custom_logic_type === 'Product'
                        ? 'bg-purple-900/50 text-purple-300'
                        : rule.custom_logic_type === 'Percentage'
                          ? 'bg-amber-900/50 text-amber-300'
                          : 'bg-slate-700 text-slate-400'"
                    >{{ rule.custom_logic_type || 'No Type' }}</span>
                  </div>
                  <!-- Rows table -->
                  <table v-if="rule.custom_logic_rows && rule.custom_logic_rows.length" class="w-full border-collapse">
                    <thead>
                      <tr class="text-[10px] text-slate-500">
                        <th class="pr-2 text-right font-normal">Min Qty</th>
                        <th v-if="rule.custom_logic_type !== 'Percentage'" class="pr-2 text-right font-normal">Nos</th>
                        <th v-if="rule.custom_logic_type !== 'Product'" class="text-right font-normal">%</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, i) in rule.custom_logic_rows" :key="i" class="font-mono text-slate-300">
                        <td class="pr-2 text-right">{{ row.min_quantity ?? '—' }}</td>
                        <td v-if="rule.custom_logic_type !== 'Percentage'" class="pr-2 text-right">{{ row.nos ?? '—' }}</td>
                        <td v-if="rule.custom_logic_type !== 'Product'" class="text-right">{{ row.percentage ?? '—' }}</td>
                      </tr>
                    </tbody>
                  </table>
                  <span v-else class="text-slate-600 text-[10px]">No rows</span>
                </template>
                <span v-else class="text-slate-700">—</span>
              </td>

              <!-- Status -->
              <td class="px-3 py-2 text-center">
                <span class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase"
                  :class="rule.enabled ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'"
                >{{ rule.enabled ? 'On' : 'Off' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="mt-3 text-xs text-slate-600">
        Manage discount rules in Frappe Desk → Ssplbilling → Discount Rule.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useItemCache } from '../services/itemCache.js'

const router = useRouter()
const { discountRules, refreshDiscountRuleCache, lastSync } = useItemCache()

const loading = ref(false)
const search = ref('')

const lastSyncLabel = computed(() => {
  if (!lastSync.value) return ''
  return new Date(lastSync.value).toLocaleTimeString()
})

const filteredRules = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return discountRules.value
  return discountRules.value.filter(r =>
    (r.rule_name || '').toLowerCase().includes(q) ||
    (r.product_group || '').toLowerCase().includes(q) ||
    (r.items || []).some(i => i.item_code.toLowerCase().includes(q) || (i.item_name || '').toLowerCase().includes(q))
  )
})

async function fetchDiscountRules() {
  loading.value = true
  try {
    await refreshDiscountRuleCache()
  } finally {
    loading.value = false
  }
}

// Load on mount if cache empty
if (!discountRules.value.length) {
  fetchDiscountRules()
}
</script>
