<template>
  <div class="flex select-none gap-1 border-t border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 pb-[max(0.25rem,env(safe-area-inset-bottom))] pt-1">
    <div class="min-w-0" :class="numpad ? 'flex-[7]' : 'flex-1'">
      <div v-for="(row, r) in rows" :key="r" class="mb-1 flex gap-1">
        <button
          v-for="k in row"
          :key="k"
          type="button"
          class="key flex-1 bg-[var(--color-surface)] text-[var(--color-text)]"
          @pointerdown.prevent="emit('key', k)"
        >{{ k }}</button>
        <button
          v-if="!numpad && r === rows.length - 1"
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
        <button type="button" class="key flex-[1.4] bg-[var(--color-surface)] text-sm text-[var(--color-text-muted)]" aria-label="Clear" @pointerdown.prevent="emit('clear')">CLS</button>
        <button type="button" class="key flex-1 bg-[var(--color-surface)]" @pointerdown.prevent="emit('key', '-')">-</button>
        <button type="button" class="key flex-[4] bg-[var(--color-surface)] text-sm text-[var(--color-text-muted)]" @pointerdown.prevent="emit('key', ' ')">space</button>
        <button type="button" class="key flex-1 bg-[var(--color-surface)]" @pointerdown.prevent="emit('key', '.')">.</button>
        <button type="button" aria-label="Search" class="key flex flex-[1.8] items-center justify-center bg-[var(--color-info)] text-white" @pointerdown.prevent="emit('enter')">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" /><path d="M15.5 15.5 21 21" /></svg>
        </button>
      </div>
    </div>
    <!-- Number pad on the right: replaces the digit row so codes and barcodes are typed like on a calculator -->
    <div v-if="numpad" class="grid flex-[3] grid-cols-3 content-start gap-1 border-l border-[var(--color-border)] pl-1">
      <button
        v-for="k in NUMPAD"
        :key="k"
        type="button"
        class="key bg-[var(--color-surface)] text-[var(--color-text)]"
        :class="k === '0' ? 'col-span-2' : ''"
        @pointerdown.prevent="emit('key', k)"
      >{{ k }}</button>
      <button
        type="button"
        aria-label="Backspace"
        class="key bg-[var(--color-surface)] text-[var(--color-danger)]"
        @pointerdown.prevent="startRepeat"
        @pointerup="stopRepeat"
        @pointerleave="stopRepeat"
        @pointercancel="stopRepeat"
      >⌫</button>
    </div>
  </div>
</template>

<script setup>
/**
 * Always-on search keyboard for phones. Keys act on pointerdown and prevent the
 * default so the search input keeps focus; the page sets inputmode="none" on the
 * input so the system keyboard never opens over the results.
 * With `numpad`, the digit row moves to a number pad on the right-hand side.
 */
import { computed, onBeforeUnmount } from 'vue'

const props = defineProps({
  numpad: { type: Boolean, default: false },
})
const emit = defineEmits(['key', 'backspace', 'clear', 'enter'])

const ROWS = [
  '1234567890'.split(''),
  'QWERTYUIOP'.split(''),
  'ASDFGHJKL'.split(''),
  'ZXCVBNM'.split(''),
]
const rows = computed(() => (props.numpad ? ROWS.slice(1) : ROWS))
const NUMPAD = ['7', '8', '9', '4', '5', '6', '1', '2', '3', '0']

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
