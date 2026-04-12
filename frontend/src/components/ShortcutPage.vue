<template>
  <div v-if="show" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/70 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="w-[720px] max-h-[85vh] overflow-y-auto rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 rounded-t-xl sticky top-0">
        <div class="text-sm font-bold uppercase tracking-wider text-[var(--color-text)]">Keyboard Shortcuts</div>
        <div class="flex items-center gap-3">
          <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text-muted)]">F1</kbd>
          <span class="text-[10px] text-[var(--color-text-muted)]">to toggle</span>
          <button @click="$emit('close')" class="ml-2 rounded px-2 py-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] text-lg leading-none">&times;</button>
        </div>
      </div>

      <div class="p-5 grid grid-cols-2 gap-6">
        <!-- Navigation -->
        <section>
          <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Navigation</div>
          <table class="w-full border-collapse text-xs">
            <tbody>
              <tr v-for="s in navigationShortcuts" :key="s.key" class="border-b border-[var(--color-border)] last:border-0">
                <td class="py-1.5 pr-4 w-28">
                  <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)] whitespace-nowrap">{{ s.key }}</kbd>
                </td>
                <td class="py-1.5 text-[var(--color-text-muted)]">{{ s.desc }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Bill Actions -->
        <section>
          <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Bill Actions</div>
          <table class="w-full border-collapse text-xs">
            <tbody>
              <tr v-for="s in billShortcuts" :key="s.key" class="border-b border-[var(--color-border)] last:border-0">
                <td class="py-1.5 pr-4 w-28">
                  <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)] whitespace-nowrap">{{ s.key }}</kbd>
                </td>
                <td class="py-1.5 text-[var(--color-text-muted)]">{{ s.desc }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Row / Item -->
        <section>
          <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Row / Item</div>
          <table class="w-full border-collapse text-xs">
            <tbody>
              <tr v-for="s in rowShortcuts" :key="s.key" class="border-b border-[var(--color-border)] last:border-0">
                <td class="py-1.5 pr-4 w-28">
                  <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)] whitespace-nowrap">{{ s.key }}</kbd>
                </td>
                <td class="py-1.5 text-[var(--color-text-muted)]">{{ s.desc }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Page Specific (slot for overrides) -->
        <section v-if="extra && extra.length">
          <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">{{ extraTitle || 'Page Shortcuts' }}</div>
          <table class="w-full border-collapse text-xs">
            <tbody>
              <tr v-for="s in extra" :key="s.key" class="border-b border-[var(--color-border)] last:border-0">
                <td class="py-1.5 pr-4 w-28">
                  <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)] whitespace-nowrap">{{ s.key }}</kbd>
                </td>
                <td class="py-1.5 text-[var(--color-text-muted)]">{{ s.desc }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: { type: Boolean, default: false },
  extra: { type: Array, default: () => [] },       // [{ key, desc }] page-specific shortcuts
  extraTitle: { type: String, default: '' },
})
const emit = defineEmits(['close'])

useSubwindowWatcher(computed(() => props.show), { ESCAPE: () => emit('close') })

const navigationShortcuts = [
  { key: 'Up / Down',    desc: 'Navigate between rows' },
  { key: 'Tab',          desc: 'Next column in row' },
  { key: 'Shift+Tab',    desc: 'Previous column in row' },
  { key: 'Home',         desc: 'Jump to first row' },
  { key: 'Page Up',      desc: 'Focus series selector' },
  { key: 'F3',           desc: 'Focus modify panel (sidebar)' },
  { key: 'F4',           desc: 'Focus sidebar series' },
]

const billShortcuts = [
  { key: 'Ctrl+S / F8',  desc: 'Save bill' },
  { key: 'F2',           desc: 'New bill' },
  { key: 'F5',           desc: 'Print bill' },
  { key: 'F1',           desc: 'Show this shortcuts panel' },
  { key: 'Esc',          desc: 'Back / cancel' },
  { key: 'End',          desc: 'Jump to discount / save' },
  { key: 'Insert',       desc: 'Open incentive entry' },
]

const rowShortcuts = [
  { key: 'Enter',        desc: 'Confirm item code / move to qty' },
  { key: 'Delete',       desc: 'Delete selected row' },
  { key: 'Backspace',    desc: 'Restore deleted row' },
]
</script>
