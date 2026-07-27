<template>
  <div v-if="label" ref="rootEl" class="relative">
    <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">{{ label }}</label>
    <input
      v-model="model"
      type="text"
      :placeholder="placeholder"
      class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
      @focus="open = true"
      @input="open = true; activeIdx = 0"
      @keydown="onKeydown"
    />
    <ul
      v-if="open && filtered.length"
      class="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg"
    >
      <li
        v-for="(o, i) in filtered"
        :key="o"
        class="cursor-pointer px-3 py-1.5 text-sm text-[var(--color-text)]"
        :class="i === activeIdx ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'hover:bg-[var(--color-surface-raised)]'"
        @mousedown.prevent="select(o)"
        @mouseenter="activeIdx = i"
      >
        {{ o }}
      </li>
    </ul>
  </div>
  <div v-else ref="rootEl" class="relative">
    <input
      v-model="model"
      type="text"
      :placeholder="placeholder"
      :class="[
        'bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:border-[var(--color-info)] outline-none',
        compact
          ? 'w-full min-w-[80px] px-2 py-1 text-xs'
          : 'w-full px-2 py-1 text-sm',
      ]"
      @focus="open = true"
      @input="open = true; activeIdx = 0"
      @keydown="onKeydown"
    />
    <ul
      v-if="open && filtered.length"
      class="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg"
      :class="compact ? 'text-xs' : 'text-sm'"
    >
      <li
        v-for="(o, i) in filtered"
        :key="o"
        class="cursor-pointer px-2 py-1 text-[var(--color-text)]"
        :class="i === activeIdx ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'hover:bg-[var(--color-surface-raised)]'"
        @mousedown.prevent="select(o)"
        @mouseenter="activeIdx = i"
      >
        {{ o }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  options: { type: Array, default: () => [] },
  label: String,
  placeholder: String,
  compact: Boolean,
  type: { type: String, default: 'text' },
})

const model = defineModel({ type: [String, Number] })

const rootEl = ref(null)
const open = ref(false)
const activeIdx = ref(0)

const filtered = computed(() => {
  const q = String(model.value ?? '').toLowerCase()
  const list = props.options || []
  if (!q) return list
  return list.filter((o) => String(o).toLowerCase().includes(q))
})

function select(o) {
  model.value = o
  open.value = false
}

function onKeydown(e) {
  if (!open.value && ['ArrowDown', 'ArrowUp'].includes(e.key)) {
    open.value = true
    return
  }
  if (!filtered.value.length) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIdx.value = (activeIdx.value + 1) % filtered.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIdx.value = (activeIdx.value - 1 + filtered.value.length) % filtered.value.length
  } else if (e.key === 'Enter') {
    if (open.value) {
      e.preventDefault()
      select(filtered.value[activeIdx.value])
    }
  } else if (e.key === 'Escape') {
    open.value = false
  }
}

function onClickOutside(e) {
  if (rootEl.value && !rootEl.value.contains(e.target)) open.value = false
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', onClickOutside))
</script>
