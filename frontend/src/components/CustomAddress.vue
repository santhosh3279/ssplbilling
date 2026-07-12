<template>
  <div
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
    @click.self="emit('close')"
  >
    <div class="flex flex-col bg-[var(--color-bg)] rounded-2xl border border-[var(--color-border)] shadow-2xl overflow-hidden w-[600px]">

      <!-- Header -->
      <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
        <span class="text-2xl font-bold uppercase tracking-tight text-[var(--color-text)]">Custom Address</span>
        <button
          class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition"
          @click="emit('close')"
        >✕</button>
      </header>

      <!-- Fields -->
      <div class="flex flex-col gap-5 p-6">

        <div class="flex flex-col gap-2">
          <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Customer Name <span class="text-[var(--color-danger)]">*</span></label>
          <input
            ref="nameInput"
            v-model="form.customer_name"
            type="text"
            placeholder="Customer name"
            class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
            @keydown.enter.prevent="focusMobile"
            @keydown.tab.prevent="focusMobile"
            @keydown.esc.prevent="emit('close')"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Mobile Number</label>
          <input
            ref="mobileInput"
            v-model="form.mobile_number"
            type="text"
            placeholder="Mobile"
            class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
            @keydown.enter.prevent="focusRemarks"
            @keydown.tab.prevent="focusRemarks"
            @keydown.esc.prevent="emit('close')"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Remarks</label>
          <input
            ref="remarksInput"
            v-model="form.remarks"
            type="text"
            placeholder="Remarks"
            class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
            @keydown.enter.prevent="focusLine1"
            @keydown.tab.prevent="focusLine1"
            @keydown.esc.prevent="emit('close')"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Address Line 1</label>
          <input
            ref="line1Input"
            v-model="form.address_line_1"
            type="text"
            placeholder="Street / Building"
            class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
            @keydown.enter.prevent="focusLine2"
            @keydown.tab.prevent="focusLine2"
            @keydown.esc.prevent="emit('close')"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Address Line 2</label>
          <input
            ref="line2Input"
            v-model="form.address_line_2"
            type="text"
            placeholder="Area / Landmark"
            class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
            @keydown.enter.prevent="saveBtn?.focus()"
            @keydown.esc.prevent="emit('close')"
          />
        </div>

      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-4 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
        <button
          @click="emit('close')"
          class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-8 py-3 text-2xl font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition"
        >Cancel</button>
        <button
          ref="saveBtn"
          @click="handleSave"
          class="rounded-xl px-10 py-3 text-2xl font-bold text-[var(--color-text-on-highlight)] transition-all active:scale-95"
          :style="{ backgroundColor: 'var(--color-highlight)' }"
        >Save</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  initialData: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close', 'saved'])

const form = ref({
  customer_name: props.initialData.customer_name || '',
  mobile_number: props.initialData.mobile_number || '',
  remarks: props.initialData.remarks || '',
  address_line_1: props.initialData.address_line_1 || '',
  address_line_2: props.initialData.address_line_2 || '',
})

const nameInput    = ref(null)
const mobileInput  = ref(null)
const remarksInput = ref(null)
const line1Input   = ref(null)
const line2Input   = ref(null)
const saveBtn      = ref(null)

function focusMobile()  { nextTick(() => { mobileInput.value?.focus(); mobileInput.value?.select() }) }
function focusRemarks() { nextTick(() => { remarksInput.value?.focus(); remarksInput.value?.select() }) }
function focusLine1()   { nextTick(() => line1Input.value?.focus()) }
function focusLine2()   { nextTick(() => line2Input.value?.focus()) }

function handleSave() {
  if (!form.value.customer_name.trim()) { nameInput.value?.focus(); return }
  emit('saved', { ...form.value })
  emit('close')
}

function onKeydown(e) {
  if (e.key === 'End')    { e.preventDefault(); handleSave() }
  if (e.key === 'Escape') { e.preventDefault(); emit('close') }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  nextTick(() => { nameInput.value?.focus() })
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>
