<template>
  <div v-if="label">
    <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">{{ label }}</label>
    <input
      v-model="model"
      :list="list"
      type="text"
      class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
    />
  </div>
  <input
    v-else
    v-model="model"
    :list="list"
    :type="type"
    :placeholder="placeholder"
    :class="[
      'bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:border-[var(--color-info)] outline-none',
      compact
        ? 'w-full min-w-[80px] px-2 py-1 text-xs'
        : 'w-full px-2 py-1 text-sm',
    ]"
  />
</template>

<script setup>
defineProps({
  list: String,
  label: String,
  placeholder: String,
  compact: Boolean,
  type: { type: String, default: 'text' },
})

const model = defineModel({ type: [String, Number] })
</script>
