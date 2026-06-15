<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] text-[13px]">
    <!-- HEADER -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            @click="$router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← Dashboard
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-semibold text-[var(--color-text)]">
            Document Naming Settings
          </h1>
        </div>
        <div class="flex items-center gap-2">
          <button 
            @click="fetchNamingSeries" 
            :disabled="loading"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:text-[var(--color-info)] transition-colors"
          >
            ↻ Refresh
          </button>
          <button 
            @click="saveAll" 
            :disabled="saving"
            class="rounded bg-[var(--color-info)] px-4 py-1.5 text-xs font-bold text-white hover:bg-[var(--color-info)]/90 disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : 'Save All Changes' }}
          </button>
        </div>
      </div>
    </header>

    <!-- CONTENT -->
    <main class="flex-1 p-6">
      <div class="mx-auto max-w-[1600px]">
        <div v-if="loading" class="flex h-64 items-center justify-center">
          <div class="text-[var(--color-text-muted)] animate-pulse">Loading naming series...</div>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <div v-for="(series, doctype) in namingSeries" :key="doctype" 
               class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3 shadow-sm">
            <div class="mb-2 flex items-center justify-between border-b border-[var(--color-border)] pb-1">
              <h2 class="text-[24px] font-bold uppercase tracking-widest text-[var(--color-info)]">{{ doctype }}</h2>
              <span class="rounded bg-gray-100 px-1 py-[1px] text-[20px] text-gray-500">{{ series.length }} series</span>
            </div>

            <div class="space-y-1">
              <div v-for="(s, index) in series" :key="index" class="flex items-center gap-1 border-b border-[var(--color-border)]/50 pb-1 last:border-0">
                <input 
                  v-model="s.prefix"
                  class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-[6px] py-[3px] text-[24px] outline-none focus:border-[var(--color-info)] font-mono"
                  placeholder="e.g. SINV-.YYYY.-####"
                />
                <div class="flex items-center gap-0.5 shrink-0">
                  <span class="text-[18px] uppercase font-bold text-[var(--color-text-muted)]">Next:</span>
                  <input 
                    v-model.number="s.current"
                    type="number"
                    class="w-32 rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-[2px] text-[24px] outline-none focus:border-[var(--color-info)] font-mono text-center"
                  />
                </div>
                <button 
                  @click="updateSingleCounter(s)"
                  :disabled="updatingCounter === s.prefix || !s.prefix"
                  class="rounded bg-[var(--color-info)] px-[5px] py-[2px] text-[20px] font-bold text-white hover:bg-[var(--color-info)]/90 disabled:opacity-40 transition-colors shrink-0"
                  title="Update counter for this series"
                >
                  {{ updatingCounter === s.prefix ? '...' : 'Update' }}
                </button>
                <button 
                  @click="removeSeries(doctype, index)"
                  class="text-red-400 hover:text-red-600 px-[2px] shrink-0 text-[28px] font-bold"
                  title="Remove"
                >
                  ✕
                </button>
              </div>
              
              <button 
                @click="addSeries(doctype)"
                class="mt-1 w-full rounded border border-dashed border-[var(--color-border)] py-1 text-[20px] font-bold uppercase tracking-wider text-[var(--color-text-muted)] hover:border-[var(--color-info)] hover:text-[var(--color-info)]"
              >
                + Add New Series
              </button>
            </div>
          </div>
        </div>

        <!-- HELP CARD -->
        <div class="mt-8 rounded-lg border border-blue-200 bg-blue-50 p-4 text-xs text-blue-700">
          <h3 class="mb-2 font-bold uppercase tracking-wider">💡 Naming Series Help</h3>
          <ul class="list-inside list-disc space-y-1 opacity-80">
            <li>Use <code class="font-bold">.YYYY.</code> for 4-digit year, <code class="font-bold">.YY.</code> for 2-digit year.</li>
            <li>Use <code class="font-bold">.MM.</code> for month, <code class="font-bold">.DD.</code> for day.</li>
            <li>The number of hashes (<code class="font-bold">#</code>) at the end determines the digits in the sequence (e.g. <code class="font-bold">####</code> for 0001).</li>
            <li><code class="font-bold">Next Counter</code>: This is the number that will be used for the next document. Incremented automatically.</li>
            <li>Example: <code class="font-bold">SINV-.YYYY.-.MM.-####</code> becomes <code class="font-bold">SINV-2026-04-0001</code>.</li>
          </ul>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { frappeGet, frappePost } from '../api'

const namingSeries = ref({})
const loading = ref(true)
const saving = ref(false)
const updatingCounter = ref(null)

async function fetchNamingSeries() {
  loading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.dashboard_api.get_all_naming_series')
    namingSeries.value = data
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

function addSeries(doctype) {
  namingSeries.value[doctype].push({ prefix: '', current: 0 })
}

function removeSeries(doctype, index) {
  namingSeries.value[doctype].splice(index, 1)
}

async function updateSingleCounter(s) {
  if (!s.prefix || !s.prefix.trim()) {
    alert('Series prefix is required to update counter.')
    return
  }
  updatingCounter.value = s.prefix
  try {
    await frappePost('ssplbilling.api.dashboard_api.update_single_series_counter', {
      prefix: s.prefix,
      current: s.current
    })
    alert(`Counter for series "${s.prefix}" updated to ${s.current}!`)
    await fetchNamingSeries()
  } catch (err) {
    console.error(err)
    alert('Failed to update series counter.')
  } finally {
    updatingCounter.value = null
  }
}

async function saveAll() {
  saving.value = true
  try {
    const promises = Object.entries(namingSeries.value).map(([doctype, series]) => {
      // Filter out empty prefixes
      const filtered = series.filter(s => s.prefix && s.prefix.trim())
      return frappePost('ssplbilling.api.dashboard_api.update_naming_series', {
        doctype,
        series_list: filtered
      })
    })
    
    await Promise.all(promises)
    alert('All naming series and counters updated successfully!')
    await fetchNamingSeries()
  } catch (err) {
    console.error(err)
    alert('Failed to save some series. Check console for details.')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchNamingSeries()
})
</script>
