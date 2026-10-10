<template>
  <div class="select-none border-t border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 pb-[max(0.25rem,env(safe-area-inset-bottom))] pt-1">
    <div v-for="(row, r) in ROWS" :key="r" class="mb-1 flex gap-1">
      <button
        v-for="k in row"
        :key="k"
        type="button"
        class="key flex-1 bg-[var(--color-surface)] text-[var(--color-text)]"
        @pointerdown.prevent="emit('key', k)"
      >{{ k }}</button>
      <button
        v-if="r === ROWS.length - 1"
        type="button"
        aria-label="Backspace"
        class="key flex-[1.6] bg-[var(--color-surface)] text-[var(--color-danger)]"
        @pointerdown.prevent="startRepeat"
        @pointerup="stopRepeat"
        @pointerleave="stopRepeat"
        @pointercancel="stopRepeat"
      >⌫</button>
    </div>
    <div class="flex gap-1">
      <button type="button" class="key flex-[1.4] bg-[var(--color-surface)] text-sm text-[var(--color-text-muted)]" @pointerdown.prevent="emit('clear')">Clear</button>
      <button type="button" class="key flex-1 bg-[var(--color-surface)]" @pointerdown.prevent="emit('key', '-')">-</button>
      <button type="button" class="key flex-[4] bg-[var(--color-surface)] text-sm text-[var(--color-text-muted)]" @pointerdown.prevent="emit('key', ' ')">space</button>
      <button type="button" class="key flex-1 bg-[var(--color-surface)]" @pointerdown.prevent="emit('key', '.')">.</button>
      <button type="button" class="key flex-[1.8] bg-[var(--color-info)] text-sm font-bold text-white" @pointerdown.prevent="emit('enter')">Search</button>
    </div>
  </div>
</template>

<script setup>
/**
 * Always-on search keyboard for phones. Keys act on pointerdown and prevent the
 * default so the search input keeps focus; the page sets inputmode="none" on the
 * input so the system keyboard never opens over the results.
 */
import { onBeforeUnmount } from 'vue'

const emit = defineEmits(['key', 'backspace', 'clear', 'enter'])

const ROWS = [
  '1234567890'.split(''),
  'QWERTYUIOP'.split(''),
  'ASDFGHJKL'.split(''),
  'ZXCVBNM'.split(''),
]

// Holding backspace keeps deleting, like a system keyboard
let repeatDelay = null
let repeatTimer = null

function startRepeat() {
  emit('backspace')
  repeatDelay = setTimeout(() => {
    repeatTimer = setInterval(() => emit('backspace'), 70)
  }, 400)
}

function stopRepeat() {
  clearTimeout(repeatDelay)
  clearInterval(repeatTimer)
  repeatDelay = repeatTimer = null
}

onBeforeUnmount(stopRepeat)
</script>

<style scoped>
.key {
  min-width: 0;
  height: 2.6rem;
  border-radius: 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  box-shadow: 0 1px 0 var(--color-border);
  touch-action: manipulation;
}
.key:active {
  filter: brightness(0.85);
}
</style>
