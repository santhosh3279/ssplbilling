<template>
  <div class="w-[600px] rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden">
    <div class="border-b border-[var(--color-border)] px-5 py-4 bg-[var(--color-surface)] flex justify-between items-center">
      <div>
        <div class="text-xl font-bold text-[var(--color-text)]">GST Validation & Address Lookup</div>
        <div class="text-sm text-[var(--color-text-muted)]">Powered by India Compliance</div>
      </div>
      <button @click="$emit('close')" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-xl">✕</button>
    </div>

    <div class="p-6 flex flex-col gap-6">
      <!-- Input Section -->
      <div class="flex flex-col gap-2">
        <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Enter GSTIN</label>
        <div class="flex gap-2">
          <input
            v-model="gstin"
            ref="inputRef"
            class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 font-mono text-lg uppercase text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            placeholder="22AAAAA0000A1Z5"
            maxlength="15"
            @keydown.enter="fetchInfo"
          />
          <button
            @click="fetchInfo"
            :disabled="loading || gstin.length !== 15"
            class="rounded bg-[var(--color-info)] px-6 py-2 font-bold text-white shadow-md transition-all active:scale-95 disabled:opacity-50"
          >
            {{ loading ? 'Searching...' : 'Search' }}
          </button>
        </div>
      </div>

      <!-- Results Section -->
      <div v-if="result" class="flex flex-col gap-4 border-t border-[var(--color-border)] pt-6 animate-in fade-in slide-in-from-top-2">
        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-1">
            <span class="text-[9px] font-bold uppercase text-[var(--color-text-muted)]">Business Name</span>
            <span class="text-base font-semibold text-[var(--color-text)]">{{ result.business_name || '--' }}</span>
          </div>
          <div class="flex flex-col gap-1 text-right">
            <span class="text-[9px] font-bold uppercase text-[var(--color-text-muted)]">Status / Category</span>
            <div class="flex items-center justify-end gap-2">
              <span class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase bg-[var(--color-success)]/20 text-[var(--color-success)]">{{ result.status }}</span>
              <span class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]">{{ result.gst_category }}</span>
            </div>
          </div>
        </div>

        <div v-if="result.permanent_address" class="flex flex-col gap-1 bg-[var(--color-surface-raised)] p-4 rounded-lg border border-[var(--color-border)]">
          <span class="text-[9px] font-bold uppercase text-[var(--color-text-muted)] mb-1">Registered Address</span>
          <div class="text-base text-[var(--color-text)] leading-relaxed">
            <p>{{ result.permanent_address.address_line1 }}</p>
            <p v-if="result.permanent_address.address_line2">{{ result.permanent_address.address_line2 }}</p>
            <p>{{ result.permanent_address.city }}, {{ result.permanent_address.state }} - {{ result.permanent_address.pincode }}</p>
          </div>
          
          <button 
            @click="copyAddress"
            class="mt-3 text-[10px] font-bold uppercase text-[var(--color-info)] hover:underline flex items-center gap-1"
          >
            📋 Copy to clipboard
          </button>
        </div>
        
        <div v-if="result.all_addresses && result.all_addresses.length > 1" class="flex flex-col gap-2">
          <span class="text-[9px] font-bold uppercase text-[var(--color-text-muted)]">Additional Places of Business ({{ result.all_addresses.length - 1 }})</span>
          <div class="max-h-40 overflow-y-auto pr-2 flex flex-col gap-2">
            <div 
              v-for="(addr, idx) in result.all_addresses.slice(1)" 
              :key="idx"
              class="text-xs text-[var(--color-text-muted)] p-2 border border-[var(--color-border)] rounded hover:bg-[var(--color-surface-raised)] transition-colors"
            >
              {{ addr.address_line1 }}, {{ addr.city }}, {{ addr.state }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="error" class="bg-[var(--color-danger)]/10 text-[var(--color-danger)] p-4 rounded-lg border border-[var(--color-danger)]/20 text-sm">
        {{ error }}
      </div>
    </div>

    <div class="bg-[var(--color-surface)] border-t border-[var(--color-border)] px-6 py-4 flex justify-end">
      <button 
        class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-2 font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]"
        @click="$emit('close')"
      >
        Close
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { validateGstin } from '../api.js'

const emit = defineEmits(['close'])

const gstin = ref('')
const inputRef = ref(null)
const loading = ref(false)
const result = ref(null)
const error = ref(null)

onMounted(() => {
  inputRef.value?.focus()
})

async function fetchInfo() {
  if (!gstin.value || gstin.value.length !== 15) return
  
  loading.value = true
  error.value = null
  result.value = null
  
  try {
    const data = await validateGstin(gstin.value)
    result.value = data
  } catch (e) {
    error.value = e.message || 'Failed to fetch GSTIN data'
  } finally {
    loading.value = false
  }
}

function copyAddress() {
  if (!result.value?.permanent_address) return
  const addr = result.value.permanent_address
  const text = `${result.value.business_name}\n${addr.address_line1}\n${addr.address_line2 ? addr.address_line2 + '\n' : ''}${addr.city}, ${addr.state} - ${addr.pincode}`
  
  navigator.clipboard.writeText(text).then(() => {
    alert('Address copied to clipboard!')
  })
}
</script>
