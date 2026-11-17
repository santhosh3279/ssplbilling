<template>
  <div class="relative h-full">
    <div
      ref="boxRef"
      tabindex="0"
      class="flex items-center justify-between gap-2 px-2 py-1 whitespace-nowrap outline-none cursor-pointer"
      :class="[textClass, focused ? 'bg-[var(--color-focus)] text-[var(--color-text-on-focus)]' : '']"
      @focus="focused = true"
      @blur="focused = false"
      @keydown="onKeydown"
    >
      <span>{{ uomLabel(itemCode, modelValue) }}</span>
      <span class="text-base opacity-60">▲▼</span>
    </div>
    <div
      v-if="focused"
      class="absolute left-0 top-full z-30 min-w-full overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl"
    >
      <div
        v-for="u in uoms"
        :key="u"
        class="px-3 py-1 whitespace-nowrap cursor-pointer"
        :class="[textClass, u === modelValue
          ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] font-bold'
          : 'text-[var(--color-text)] hover:bg-[var(--color-midlight)]']"
        @mousedown.prevent="pick(u)"
      >{{ uomLabel(itemCode, u) }}</div>
      <div class="border-t border-[var(--color-border)] px-3 py-1 text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] whitespace-nowrap">
        ↑ ↓ change · Enter ok · Esc back
      </div>
    </div>
  </div>
</template>

<script setup>
// Keyboard UOM chooser: arrow keys step through the item's UOMs, Enter confirms, Esc cancels.
import { ref } from 'vue'
import { uomLabel } from '../services/itemCache.js'

const props = defineProps({
  itemCode: { type: String, required: true },
  modelValue: { type: String, default: '' },
  uoms: { type: Array, default: () => [] },
  textClass: { type: String, default: 'text-3xl' },
})
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const boxRef = ref(null)
const focused = ref(false)

function step(dir) {
  if (!props.uoms.length) return
  const i = props.uoms.indexOf(props.modelValue)
  const next = (i + dir + props.uoms.length) % props.uoms.length
  emit('update:modelValue', props.uoms[next])
}

function pick(u) {
  emit('update:modelValue', u)
  emit('confirm')
}

function onKeydown(e) {
  if (e.key === 'ArrowDown' || e.key === 'ArrowRight') { e.preventDefault(); e.stopPropagation(); step(1) }
  else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') { e.preventDefault(); e.stopPropagation(); step(-1) }
  else if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); emit('confirm') }
  else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); emit('cancel') }
}

defineExpose({ focus: () => boxRef.value?.focus() })
</script>
