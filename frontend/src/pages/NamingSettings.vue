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
      <div class="mx-auto max-w-5xl">
        <div v-if="loading" class="flex h-64 items-center justify-center">
          <div class="text-[var(--color-text-muted)] animate-pulse">Loading naming series...</div>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div v-for="(series, doctype) in namingSeries" :key="doctype" 
               class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div class="mb-4 flex items-center justify-between border-b border-[var(--color-border)] pb-2">
              <h2 class="text-xs font-bold uppercase tracking-widest text-[var(--color-info)]">{{ doctype }}</h2>
              <span class="rounded bg-gray-100 px-2 py-0.5 text-[10px] text-gray-500">{{ series.length }} series</span>
            </div>

            <div class="space-y-3">
              <div v-for="(s, index) in series" :key="index" class="flex flex-col gap-1 border-b border-[var(--color-border)]/50 pb-3 last:border-0">
                <div class="flex gap-2">
                  <input 
                    v-model="s.prefix"
                    class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1.5 text-xs outline-none focus:border-[var(--color-info)] font-mono"
                    placeholder="e.g. SINV-.YYYY.-####"
                  />
                  <button 
                    @click="removeSeries(doctype, index)"
                    class="text-red-400 hover:text-red-600 px-1"
                    title="Remove"
                  >
                    ✕
                  </button>
                </div>
                <div class="flex items-center gap-2 pl-1">
                  <span class="text-[10px] uppercase font-bold text-[var(--color-text-muted)]">Next Counter:</span>
                  <input 
                    v-model.number="s.current"
                    type="number"
                    class="w-24 rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-0.5 text-[10px] outline-none focus:border-[var(--color-info)] font-mono"
                  />
                  <span class="text-[9px] text-[var(--color-text-muted)] italic">(Used if template matches today)</span>
                </div>
              </div>
              
              <button 
                @click="addSeries(doctype)"
                class="mt-2 w-full rounded border border-dashed border-[var(--color-border)] py-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)] hover:border-[var(--color-info)] hover:text-[var(--color-info)]"
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
