<template>
  <div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-[2px]" v-if="!showPriceListUpdate">
    <div class="w-[700px] overflow-hidden rounded-2xl bg-[var(--color-bg)] border border-[var(--color-highlight)]/40 shadow-2xl">
      <div class="bg-[var(--color-highlight)]/20 px-8 py-6 flex items-center gap-5 border-b border-[var(--color-highlight)]/30">
        <div class="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-highlight)]/40 text-4xl text-[var(--color-highlight)]">💰</div>
        <div>
          <div class="text-4xl font-bold text-[var(--color-text)]">Update Item Price?</div>
          <div class="text-xl text-[var(--color-highlight)] uppercase tracking-wider font-bold">Price Change Detected</div>
        </div>
      </div>

      <div class="p-8 space-y-6">
        <div class="flex flex-col gap-2">
          <div class="text-3xl font-bold text-[var(--color-text)]">{{ data.item_name || data.item_code }}</div>
          <div class="text-xl text-[var(--color-text-muted)]">Item Code: {{ data.item_code }}</div>
        </div>

        <div class="grid grid-cols-3 gap-6 rounded-xl bg-[var(--color-surface-raised)]/50 p-6 border border-[var(--color-border)]/50">
          <div class="flex flex-col">
            <span class="text-lg text-[var(--color-text-muted)] uppercase font-bold">Price List Rate</span>
            <span class="text-5xl font-mono text-[var(--color-text-muted)]">{{ (data.standard_rate || 0).toFixed(2) }}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-lg text-[var(--color-text-muted)] uppercase font-bold">New Rate</span>
            <span class="text-5xl font-mono text-[var(--color-text)]">{{ (data.current_rate || 0).toFixed(2) }}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-lg text-[var(--color-text-muted)] uppercase font-bold">Factor</span>
            <span class="text-5xl font-mono text-[var(--color-highlight)]">{{ multiplicationFactor.toFixed(4) }}</span>
          </div>
        </div>

        <div class="text-2xl text-[var(--color-text-muted)] leading-relaxed">
          Factor = New Rate ÷ Price List Rate. Saved as a special discount for
          <span class="text-[var(--color-text)] font-medium">{{ customer }}</span>.
        </div>
      </div>

      <div class="flex flex-col gap-3 p-8 pt-0">
        <button
          ref="savePriceYesBtn"
          :disabled="saving"
          @click="saveForCustomer"
          @keydown="onKeydown"
          class="w-full rounded-xl border-[3px] border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4 text-3xl font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-all outline-none focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/20 disabled:opacity-50"
        >
          {{ saving ? 'Saving…' : 'Save for Customer' }}
        </button>
        <button
          ref="savePriceNoBtn"
          @click="$emit('dismiss')"
          @keydown="onKeydown"
          class="w-full rounded-xl border-[3px] border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4 text-3xl font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition-all outline-none focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/20"
        >
          Dismiss
        </button>
        <div class="mt-4 text-center">
          <span class="text-lg text-[var(--color-text-muted)] uppercase font-bold tracking-widest">
            Press <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 font-mono text-[var(--color-text-muted)]">F4</kbd> for Advanced Update
          </span>
        </div>
      </div>
    </div>
  </div>
  <PriceListUpdate
    v-if="showPriceListUpdate"
    :is-sub-window="true"
    :item-code="data.item_code"
    :selected-price-list="priceList"
    @close="$emit('dismiss')"
    @saved="$emit('dismiss')"
  />
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { frappeGet } from '../api.js'
import { useSubwindow } from '../services/shortcutManager'
import PriceListUpdate from '../pages/PriceListUpdate.vue'

const props = defineProps({
  data: { type: Object, required: true },   // { item_code, item_name, standard_rate, current_rate }
  customer: { type: String, default: '' },   // actual Customer doc name
  priceList: { type: String, default: '' }
})

const emit = defineEmits(['saved', 'updatePricelist', 'dismiss', 'advanced'])

useSubwindow()

const savePriceYesBtn = ref(null)
const savePriceNoBtn = ref(null)
const saving = ref(false)
const showPriceListUpdate = ref(false)

// Core calculation: factor = user rate ÷ price list rate
const multiplicationFactor = computed(() => {
  const std = parseFloat(props.data.standard_rate || 0)
  const curr = parseFloat(props.data.current_rate || 0)
  return std > 0 ? parseFloat((curr / std).toFixed(6)) : 1
})

onMounted(() => {
  nextTick(() => { savePriceNoBtn.value?.focus() })
})

async function saveForCustomer() {
  if (saving.value) return
  saving.value = true
  const factor = multiplicationFactor.value
  try {
    await frappeGet('ssplbilling.api.customer_pricing_api.save_customer_item_price', {
      customer: props.customer,
      item_code: props.data.item_code,
      multiplication_factor: factor
    })
    // Refresh the full customer pricing cache and emit it to the parent
    const freshPricing = await frappeGet('ssplbilling.api.customer_pricing_api.get_customer_pricing', {
      customer: props.customer
    }).catch(() => null)
    emit('saved', freshPricing || {})
  } catch (e) {
    console.error('[CustomerPrice] Failed to save:', e)
    emit('dismiss')
  } finally {
    saving.value = false
  }
}

function onKeydown(e) {
  if (e.key === 'Escape') { e.preventDefault(); return }
  if (e.key === 'F4') { e.preventDefault(); showPriceListUpdate.value = true; return }

  const btns = [savePriceYesBtn.value, savePriceNoBtn.value].filter(Boolean)
  const currIdx = btns.indexOf(document.activeElement)

  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault()
    btns[(currIdx - 1 + btns.length) % btns.length]?.focus()
  } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    e.preventDefault()
    btns[(currIdx + 1) % btns.length]?.focus()
  }
}
</script>
