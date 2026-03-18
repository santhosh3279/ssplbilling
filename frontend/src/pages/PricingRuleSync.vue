<template>
  <div class="min-h-screen bg-slate-900 text-slate-200">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-slate-600">|</span>
        <span class="text-sm font-semibold text-slate-200">Pricing Rules</span>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="lastSync" class="text-xs text-slate-500">Last sync: {{ lastSyncLabel }}</span>
        <button
          @click="syncRules"
          :disabled="loading"
          class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50"
        >
          <span v-if="loading" class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          <span v-else">🔄</span>
          {{ loading ? 'Syncing...' : 'Sync Now' }}
        </button>
      </div>
    </header>

    <!-- Content -->
    <div class="mx-auto max-w-6xl px-6 py-6">

      <!-- Stats -->
      <div class="mb-6 grid grid-cols-3 gap-4">
        <div class="rounded-xl border border-slate-700 bg-slate-800 p-4">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500">Total Rules</div>
          <div class="mt-1 text-3xl font-bold text-blue-400">{{ rules.length }}</div>
        </div>
        <div class="rounded-xl border border-slate-700 bg-slate-800 p-4">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500">Discount Rules</div>
          <div class="mt-1 text-3xl font-bold text-amber-400">{{ rules.filter(r => r.rate_or_discount === 'Discount Percentage').length }}</div>
        </div>
        <div class="rounded-xl border border-slate-700 bg-slate-800 p-4">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500">Rate Override Rules</div>
          <div class="mt-1 text-3xl font-bold text-emerald-400">{{ rules.filter(r => r.rate_or_discount === 'Rate').length }}</div>
        </div>
      </div>

      <!-- Filter -->
      <div class="mb-4 flex items-center gap-3">
        <input
          v-model="search"
          type="text"
          placeholder="Search by rule name or item code..."
          class="w-80 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
        />
        <span class="text-sm text-slate-500">{{ filteredRules.length }} rule{{ filteredRules.length !== 1 ? 's' : '' }}</span>
      </div>

      <!-- Table -->
      <div class="overflow-hidden rounded-xl border border-slate-700">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-700 bg-slate-800 text-xs font-bold uppercase tracking-wider text-slate-400">
              <th class="px-4 py-3 text-left">Rule Name</th>
              <th class="px-4 py-3 text-left">Apply On</th>
              <th class="px-4 py-3 text-left">Items</th>
              <th class="px-4 py-3 text-left">Customer</th>
              <th class="px-4 py-3 text-left">Qty Range</th>
              <th class="px-4 py-3 text-left">Type</th>
              <th class="px-4 py-3 text-right">Value</th>
              <th class="px-4 py-3 text-left">Valid Until</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !rules.length">
              <td colspan="8" class="px-4 py-8 text-center text-slate-500">Syncing pricing rules...</td>
            </tr>
            <tr v-else-if="!filteredRules.length">
              <td colspan="8" class="px-4 py-8 text-center text-slate-500">{{ rules.length ? 'No rules match search' : 'No pricing rules found. Click Sync Now.' }}</td>
            </tr>
            <tr
              v-for="rule in filteredRules"
              :key="rule.name"
              class="border-b border-slate-800 transition-colors hover:bg-slate-800/50"
            >
              <td class="px-4 py-3 font-medium text-slate-200">{{ rule.name }}</td>
              <td class="px-4 py-3 text-slate-400">{{ rule.apply_on }}</td>
              <td class="px-4 py-3">
                <div v-if="rule.item_codes && rule.item_codes.length" class="flex flex-wrap gap-1">
                  <span
                    v-for="code in rule.item_codes.slice(0, 3)"
                    :key="code"
                    class="rounded bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] text-slate-300"
                  >{{ code }}</span>
                  <span v-if="rule.item_codes.length > 3" class="text-xs text-slate-500">+{{ rule.item_codes.length - 3 }} more</span>
                </div>
                <span v-else class="text-xs text-slate-600">All Items</span>
              </td>
              <td class="px-4 py-3 text-slate-400">
                <span v-if="rule.applicable_for === 'Customer' && rule.customer">{{ rule.customer }}</span>
                <span v-else-if="rule.applicable_for === 'Customer Group' && rule.customer_group">{{ rule.customer_group }}</span>
                <span v-else class="text-slate-600">All</span>
              </td>
              <td class="px-4 py-3 text-slate-400 tabular-nums">
                <span v-if="rule.min_qty || rule.max_qty">
                  {{ rule.min_qty || 0 }} – {{ rule.max_qty || '∞' }}
                </span>
                <span v-else class="text-slate-600">Any</span>
              </td>
              <td class="px-4 py-3">
                <span class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase" :class="{
                  'bg-amber-900/50 text-amber-300': rule.rate_or_discount === 'Discount Percentage',
                  'bg-emerald-900/50 text-emerald-300': rule.rate_or_discount === 'Rate',
                  'bg-blue-900/50 text-blue-300': rule.rate_or_discount === 'Discount Amount',
                }">{{ rule.rate_or_discount }}</span>
              </td>
              <td class="px-4 py-3 text-right font-mono font-bold">
                <span v-if="rule.rate_or_discount === 'Discount Percentage'" class="text-amber-400">{{ rule.discount_percentage }}%</span>
                <span v-else-if="rule.rate_or_discount === 'Rate'" class="text-emerald-400">₹{{ rule.rate }}</span>
                <span v-else class="text-blue-400">₹{{ rule.discount_amount }}</span>
              </td>
              <td class="px-4 py-3 text-slate-400">{{ rule.valid_upto || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import { useItemCache } from '../services/itemCache.js'

const router = useRouter()
const { pricingRules, refreshItemCache, lastSync, syncLoading } = useItemCache()

const rules = ref([])
const loading = ref(false)
const search = ref('')

const lastSyncLabel = computed(() => {
  if (!lastSync.value) return ''
  return new Date(lastSync.value).toLocaleTimeString()
})

const filteredRules = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return rules.value
  return rules.value.filter(r =>
    r.name.toLowerCase().includes(q) ||
    (r.item_codes || []).some(c => c.toLowerCase().includes(q)) ||
    (r.customer || '').toLowerCase().includes(q)
  )
})

async function syncRules() {
  loading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.itemsearch_api.get_pricing_rules')
    rules.value = data || []
    // Also refresh the item cache so runtime applyPricingRule is up to date
    await refreshItemCache('Sales')
  } catch (e) {
    console.error('Pricing rule sync failed:', e)
  } finally {
    loading.value = false
  }
}

// Load on mount from cache if available, else fetch
if (pricingRules.value.length) {
  rules.value = pricingRules.value
} else {
  syncRules()
}
</script>
