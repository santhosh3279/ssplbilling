<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="$emit('close')">
    <div class="flex h-[90vh] w-[90vw] flex-col rounded-xl bg-white shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="border-b border-gray-200 px-5 py-4 flex items-center justify-between bg-gray-50">
        <div>
          <div class="text-2xl font-semibold text-gray-700">Detailed Customer Search</div>
          <div class="text-lg text-gray-500">View contact info and select customer</div>
        </div>
        <div class="flex items-center gap-3">
          <button 
            @click="$emit('new-customer')" 
            class="flex items-center gap-2 rounded-lg border border-gray-300 bg-gray-100 px-4 py-2 text-lg font-semibold text-gray-700 hover:bg-gray-200 shadow-sm"
          >
            New Customer <kbd class="ml-1 rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-xs text-gray-400">F2</kbd>
          </button>
          <button 
            @click="$emit('edit-customer', results[selectedIdx])" 
            v-if="selectedCustomer || results[selectedIdx]"
            class="flex items-center gap-2 rounded-lg border border-gray-300 bg-gray-100 px-4 py-2 text-lg font-semibold text-gray-700 hover:bg-gray-200 shadow-sm"
          >
            Edit Details <kbd class="ml-1 rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-xs text-gray-400">F3</kbd>
          </button>
          <button 
            @click="$emit('refresh')" 
            class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-lg font-semibold text-blue-600 hover:bg-blue-100"
          >
            🔄 Refresh <kbd class="ml-1 rounded border border-blue-200 bg-white px-1.5 py-0.5 font-mono text-xs text-blue-400">F5</kbd>
          </button>
          <button @click="$emit('close')" class="text-2xl text-gray-400 hover:text-gray-600">✕</button>
        </div>
      </div>

      <!-- Search input -->
      <div class="border-b border-gray-100 p-4">
        <input
          ref="searchInput"
          :value="query"
          @input="$emit('update:query', $event.target.value)"
          class="w-full rounded border border-gray-300 px-4 py-3 text-2xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          placeholder="Type customer name or mobile..."
          @keydown.esc="$emit('close')"
          @keydown.down.prevent="$emit('update:selectedIdx', Math.min(selectedIdx + 1, results.length - 1))"
          @keydown.up.prevent="$emit('update:selectedIdx', Math.max(selectedIdx - 1, 0))"
          @keydown.enter.prevent="results[selectedIdx] && $emit('select', results[selectedIdx])"
        />
      </div>

      <!-- Results Table -->
      <div class="flex-1 overflow-y-auto">
        <table class="w-full text-2xl">
          <thead class="sticky top-0 bg-white shadow-sm">
            <tr class="text-lg font-bold uppercase tracking-wider text-gray-600 border-b">
              <th class="px-5 py-3 text-left">Customer Name</th>
              <th class="px-5 py-3 text-left">Mobile Number</th>
              <th class="px-5 py-3 text-right">Balance</th>
              <th class="px-5 py-3 text-left">Address</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="(c, idx) in results"
              :key="c.name"
              class="cursor-pointer hover:bg-blue-50/50"
              :class="{ 'bg-blue-50': selectedIdx === idx }"
              @click="$emit('select', c)"
              @mouseenter="$emit('update:selectedIdx', idx)"
            >
              <td class="px-5 py-2">
                <div class="font-medium text-gray-800">{{ c.customer_name }}</div>
              </td>
              <td class="px-5 py-2 text-gray-600">
                {{ c.mobile_no || '--' }}
              </td>
              <td class="px-5 py-2 text-right">
                <span :class="c.balance > 0 ? 'text-red-600' : c.balance < 0 ? 'text-green-600' : 'text-gray-400'" class="font-bold">
                  &#8377;{{ (c.balance || 0).toFixed(2) }}
                </span>
              </td>
              <td class="px-5 py-2 text-gray-500 text-lg truncate max-w-[300px]">
                {{ c.address_line1 }}{{ c.city ? ', ' + c.city : '' }}
              </td>
            </tr>
            <tr v-if="!results.length">
              <td colspan="4" class="px-5 py-12 text-center text-gray-400 text-xl italic">
                No customers found matching "{{ query }}"
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Detail Footer -->
      <div v-if="results[selectedIdx]" class="border-t border-gray-200 bg-blue-50/30 px-6 py-3">
        <div class="flex flex-wrap gap-x-8 gap-y-2">
          <div class="flex flex-col">
            <span class="text-[10px] font-bold uppercase text-gray-400">Current Balance</span>
            <span class="text-xl font-bold" :class="results[selectedIdx].balance > 0 ? 'text-red-600' : 'text-green-600'">
              &#8377;{{ (results[selectedIdx].balance || 0).toFixed(2) }}
              <span class="text-xs font-normal uppercase ml-1">{{ results[selectedIdx].balance > 0 ? 'Debit' : 'Credit' }}</span>
            </span>
          </div>
          <div class="flex flex-col flex-1">
            <span class="text-[10px] font-bold uppercase text-gray-400">Address</span>
            <span class="text-lg text-gray-700">
              <template v-if="results[selectedIdx].address_line1">
                {{ results[selectedIdx].address_line1 }}{{ results[selectedIdx].city ? ', ' + results[selectedIdx].city : '' }}{{ results[selectedIdx].pincode ? ' - ' + results[selectedIdx].pincode : '' }}
              </template>
              <template v-else>
                <span class="text-gray-300 italic">No address provided</span>
              </template>
            </span>
          </div>
          <div class="flex flex-col">
            <span class="text-[10px] font-bold uppercase text-gray-400">Mobile</span>
            <span class="text-lg text-gray-700">{{ results[selectedIdx].mobile_no || '--' }}</span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-gray-100 bg-gray-50 px-5 py-4 flex items-center justify-between text-lg text-gray-500">
        <div class="flex gap-4">
          <span><kbd class="rounded border bg-white px-2 py-1 font-mono">F2</kbd> New Customer</span>
          <span><kbd class="rounded border bg-white px-2 py-1 font-mono">F3</kbd> Edit</span>
          <span><kbd class="rounded border bg-white px-2 py-1 font-mono">Enter</kbd> to Select</span>
        </div>
        <button @click="$emit('close')" class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600 hover:bg-gray-50">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'

const props = defineProps({
  show: Boolean,
  query: String,
  results: {
    type: Array,
    default: () => []
  },
  selectedIdx: {
    type: Number,
    default: 0
  },
  selectedCustomer: Object
})

const emit = defineEmits([
  'close',
  'update:query',
  'update:selectedIdx',
  'select',
  'new-customer',
  'edit-customer',
  'refresh'
])

const searchInput = ref(null)

watch(() => props.show, (newVal) => {
  if (newVal) {
    nextTick(() => {
      searchInput.value?.focus()
      searchInput.value?.select()
    })
  }
})
</script>
