<template>
  <div v-if="show" class="fixed inset-0 z-[100] bg-[var(--color-bg)] flex flex-col">
    <!-- Header -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="$emit('close')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← Close
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-bold text-[var(--color-text)]">License Details</h1>
        </div>
        <button
          @click="refresh"
          :disabled="loading"
          class="flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-midlight)] transition disabled:opacity-50"
        >
          <span :class="{ 'animate-spin inline-block': loading }">🔄</span>
          <span>{{ loading ? 'Checking...' : 'Re-verify' }}</span>
        </button>
      </div>
    </header>

    <!-- Body -->
    <div class="flex-1 overflow-auto px-10 py-10">
      <div class="mx-auto max-w-2xl space-y-6">
        <!-- Status banner -->
        <div
          class="rounded-xl p-4 flex items-center gap-3"
          :class="license?.valid ? 'bg-[var(--color-success)]/10 border border-[var(--color-success)]/30' : 'bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/30'"
        >
          <span class="text-2xl">{{ license?.valid ? '✅' : '🔒' }}</span>
          <div>
            <div class="font-bold text-sm" :class="license?.valid ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
              {{ license?.valid ? 'License Active' : 'License Invalid' }}
            </div>
            <div class="text-xs text-[var(--color-text-muted)]">{{ license?.message }}</div>
          </div>
        </div>

        <!-- Core details -->
        <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 text-sm space-y-3">
          <div class="flex justify-between">
            <span class="text-[var(--color-text-muted)]">Licensed Site</span>
            <span class="font-semibold text-[var(--color-text)]">{{ license?.site || '—' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-[var(--color-text-muted)]">Expiry Date</span>
            <span class="font-semibold text-[var(--color-text)]">{{ license?.expiry_date || '—' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-[var(--color-text-muted)]">Days Remaining</span>
            <span class="font-bold" :class="(license?.days_remaining ?? 0) < 30 ? 'text-[var(--color-warning)]' : 'text-[var(--color-text)]'">
              {{ license?.days_remaining ?? '—' }}
            </span>
          </div>
          <div class="flex justify-between">
            <span class="text-[var(--color-text-muted)]">Concurrent Tab Limit</span>
            <span class="font-semibold text-[var(--color-text)]">
              {{ license?.max_tabs ?? 'Unlimited' }}
            </span>
          </div>
          <div class="flex justify-between">
            <span class="text-[var(--color-text-muted)]">Tabs Currently Open</span>
            <span class="font-semibold text-[var(--color-text)]">
              {{ tabLimitInfo.active_tabs }}<span v-if="license?.max_tabs"> / {{ license.max_tabs }}</span>
            </span>
          </div>
        </div>

        <!-- Features -->
        <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
          <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] mb-3">
            Licensed Features ({{ license?.features?.length || 0 }})
          </div>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="f in license?.features || []"
              :key="f"
              class="rounded-full bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2.5 py-1 text-[11px] font-medium text-[var(--color-text)]"
            >
              {{ f }}
            </span>
            <span v-if="!license?.features?.length" class="text-xs text-[var(--color-text-muted)]">No features listed</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { frappeGet } from '../api'
import { tabLimitInfo } from '../services/tabSession'

const props = defineProps({
  show: { type: Boolean, default: false },
})
defineEmits(['close'])

const license = ref(null)
const loading = ref(false)

async function refresh() {
  loading.value = true
  try {
    const lic = await frappeGet('ssplbilling.api.license_api.get_license_status')
    license.value = lic
    localStorage.setItem('ae_license_info', JSON.stringify(lic))
  } catch (e) {
    console.warn('[LicenseDetails] failed to fetch license status:', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.show, (val) => {
  if (val) {
    license.value = JSON.parse(localStorage.getItem('ae_license_info') || 'null')
    refresh()
  }
})
</script>
