<template>
  <span class="relative inline-flex h-9 w-9 shrink-0 items-center justify-center rounded border border-[var(--color-border)] text-[var(--color-text)] focus-within:ring-2 focus-within:ring-[var(--color-info)]" :class="{ 'opacity-40': disabled }">
    <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M16 3v4M8 3v4M3 11h18" />
    </svg>
    <input
      type="date"
      :value="modelValue"
      :disabled="disabled"
      :min="min"
      :max="max"
      :aria-label="label"
      :title="label"
      class="calendar-input absolute inset-0 h-full w-full cursor-pointer opacity-0 disabled:cursor-not-allowed"
      @click="openCalendar"
      @keydown.enter.prevent.stop="openCalendar"
      @change="selectDate"
    />
  </span>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: 'Choose date' },
  disabled: Boolean,
  min: String,
  max: String,
})
const emit = defineEmits(['update:modelValue'])

function openCalendar(event) {
  try {
    event.target.showPicker?.()
  } catch {
    // The native input remains usable when programmatic opening is unavailable.
  }
}

function selectDate(event) {
  if (event.target.validity.valid) emit('update:modelValue', event.target.value)
}
</script>

<style scoped>
.calendar-input::-webkit-calendar-picker-indicator {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  cursor: pointer;
}
</style>
