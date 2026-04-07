<template>
  <div class="w-[500px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] p-6 shadow-2xl overflow-hidden">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-[var(--color-text)]">Customer Information</h2>
        <p class="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wider">Please fill in the details below</p>
      </div>
      <button 
        @click="$emit('close')" 
        class="h-8 w-8 rounded-full flex items-center justify-center hover:bg-[var(--color-surface-raised)] transition-colors text-[var(--color-text-muted)]"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>

    <div class="flex flex-col gap-5">
      <!-- Customer Name -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Customer Name</label>
        <input
          v-model="form.customer_name"
          class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-base font-semibold text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-all"
          placeholder="e.g. John Doe"
        />
      </div>

      <!-- Address Line 1 -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Address Line 1</label>
        <input
          v-model="form.address_line_1"
          class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-all"
          placeholder="Street / Building / House No."
        />
      </div>

      <!-- Address Line 2 -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Address Line 2</label>
        <input
          v-model="form.address_line_2"
          class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-all"
          placeholder="Area / Locality / Landmark"
        />
      </div>

      <!-- Mobile Number -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Mobile Number</label>
        <div class="relative">
          <span class="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] font-bold">+91</span>
          <input
            v-model="form.mobile_number"
            class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] pl-12 pr-4 py-3 text-base font-mono tracking-widest text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-all"
            placeholder="9876543210"
            maxlength="10"
          />
        </div>
      </div>
    </div>

    <div class="mt-8 flex gap-3">
      <button 
        @click="$emit('close')"
        class="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-3 font-bold text-[var(--color-text)] hover:brightness-110 active:scale-[0.98] transition-all"
      >
        Cancel
      </button>
      <button 
        @click="handleSubmit"
        class="flex-1 rounded-xl bg-[var(--color-highlight)] py-3 font-bold text-[var(--color-text-on-highlight)] shadow-lg shadow-[var(--color-highlight)]/20 hover:brightness-110 active:scale-[0.98] transition-all"
      >
        Save Details
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const emit = defineEmits(['close', 'submit'])

const form = reactive({
  customer_name: '',
  address_line_1: '',
  address_line_2: '',
  mobile_number: ''
})

function handleSubmit() {
  emit('submit', { ...form })
}
</script>
