<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] overflow-hidden">
    <header class="shrink-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center gap-4">
        <button
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
          @click="router.push('/')"
        >
          &larr; Dashboard
        </button>
        <div>
          <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Competitive Items</h1>
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">Pricelist percentages per competitive item</p>
        </div>
      </div>
      <span class="text-xs text-[var(--color-text-muted)]">
        <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">F2</kbd> New
        <kbd class="ml-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">F8</kbd> Save
        <kbd class="ml-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Esc</kbd> Back
      </span>
    </header>

    <main class="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-[340px_1fr] text-[var(--color-text)]">
      <!-- List -->
      <aside class="flex flex-col overflow-hidden border-b md:border-b-0 md:border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div class="flex gap-2 p-3 border-b border-[var(--color-border)]">
          <input
            ref="searchInput"
            v-model="query"
            :class="inputCls"
            placeholder="Search..."
            @keydown.down.prevent="moveHighlight(1)"
            @keydown.up.prevent="moveHighlight(-1)"
            @keydown.enter.prevent="filtered[highlight] && openRecord(filtered[highlight].name)"
          />
          <button
            class="shrink-0 rounded-lg bg-[var(--color-info)] px-4 py-2 text-sm font-bold uppercase tracking-wider text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)]/80 active:scale-95"
            @click="newRecord"
          >
            + New
          </button>
        </div>
        <div class="flex-1 overflow-y-auto max-h-[30vh] md:max-h-none">
          <div v-if="listLoading" class="p-4 text-sm text-[var(--color-text-muted)] animate-pulse">Loading…</div>
          <div v-else-if="!filtered.length" class="p-4 text-sm italic text-[var(--color-text-muted)]">No competitive items.</div>
          <button
            v-for="(c, i) in filtered"
            :key="c.name"
            class="flex w-full items-center justify-between gap-2 border-b border-[var(--color-border)]/50 px-4 py-3 text-left transition-colors"
            :class="c.name === form.name
              ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
              : i === highlight ? 'bg-[var(--color-info)]/15' : 'hover:bg-[var(--color-surface-raised)]'"
            @click="openRecord(c.name)"
          >
            <span class="truncate font-semibold">{{ c.name }}</span>
            <span class="shrink-0 text-xs font-bold opacity-70">{{ c.item_count }} item{{ c.item_count === 1 ? '' : 's' }}</span>
          </button>
        </div>
      </aside>

      <!-- Editor -->
      <section class="overflow-y-auto p-6">
        <div v-if="detailLoading" class="flex h-full items-center justify-center text-[var(--color-text-muted)]">
          <span class="text-xl animate-pulse">Loading…</span>
        </div>

        <div v-else class="mx-auto max-w-3xl space-y-6">
          <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-5">
            <h2 class="text-xl font-bold border-b border-[var(--color-border)] pb-3">
              {{ form.name ? 'Edit Competitive Item' : 'New Competitive Item' }}
            </h2>

            <div>
              <label class="block text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Competitive Item Name *</label>
              <input
                ref="nameInput"
                v-model="form.competitive_item_name"
                :class="inputCls"
                style="font-size: 1.5rem;"
                placeholder="e.g. Brand X 1kg"
                @keydown.enter.prevent="focusPct(0)"
              />
            </div>

            <div>
              <label class="block text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Pricelist Percentages</label>
              <div class="flex flex-col gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-3">
                <div v-for="(row, i) in pctRows" :key="row.pricelist" class="flex items-center gap-3">
                  <span class="flex-1 truncate font-semibold" :title="row.pricelist">{{ row.pricelist }}</span>
                  <input
                    :ref="el => (pctInputs[i] = el)"
                    v-model="row.percentage"
                    type="number"
                    step="any"
                    placeholder="0"
                    class="w-32 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-right font-mono text-xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                    @keydown.enter.prevent="i < pctRows.length - 1 ? focusPct(i + 1) : save()"
                  />
                  <span class="font-bold text-[var(--color-text-muted)]">%</span>
                </div>
              </div>
            </div>

            <div class="flex flex-wrap justify-end gap-3 pt-2">
              <button
                v-if="form.name"
                :disabled="saving"
                class="rounded-lg border border-[var(--color-danger)] px-5 py-2 text-sm font-bold uppercase tracking-wider text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10 disabled:opacity-50"
                @click="remove"
              >
                Delete
              </button>
              <button
                :disabled="saving || !form.competitive_item_name.trim()"
                class="rounded-lg bg-[var(--color-info)] px-8 py-2 text-sm font-bold uppercase tracking-wider text-[var(--color-text-on-highlight)] shadow-md hover:bg-[var(--color-info)]/80 active:scale-95 disabled:opacity-50"
                @click="save"
              >
                {{ saving ? 'Saving…' : (form.name ? 'Update (F8)' : 'Create (F8)') }}
              </button>
            </div>
          </div>

          <div v-if="form.name" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <h3 class="mb-3 text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Linked Items ({{ linkedItems.length }})</h3>
            <div v-if="!linkedItems.length" class="text-sm italic text-[var(--color-text-muted)]">
              No items use this yet. Set it in Item Creation.
            </div>
            <ul v-else class="divide-y divide-[var(--color-border)]/50 max-h-72 overflow-y-auto">
              <li v-for="it in linkedItems" :key="it.item_code" class="flex justify-between gap-3 py-2 text-sm">
                <span class="truncate font-semibold">{{ it.item_name }}</span>
                <span class="shrink-0 font-mono text-[var(--color-text-muted)]">{{ it.item_code }}</span>
              </li>
            </ul>
          </div>
        </div>
      </section>
    </main>

    <div
      v-if="toast"
      class="fixed bottom-6 right-6 z-50 rounded-lg px-4 py-3 text-sm font-medium text-white shadow-lg"
      :class="toast.type === 'error' ? 'bg-[var(--color-danger)]' : 'bg-[var(--color-success)]'"
    >
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

const router = useRouter()
const API = 'ssplbilling.api.competitive_api'

const inputCls = 'w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none focus:border-[var(--color-info)]'

const records = ref([])
const listLoading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)
const query = ref('')
const highlight = ref(0)
const toast = ref(null)

const searchInput = ref(null)
const nameInput = ref(null)
const pctInputs = []

const form = reactive({ name: '', competitive_item_name: '' })
const pctRows = ref([])
const linkedItems = ref([])

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return q ? records.value.filter(r => r.name.toLowerCase().includes(q)) : records.value
})

watch(query, () => { highlight.value = 0 })

function showToast(message, type = 'success') {
  toast.value = { message, type }
  setTimeout(() => { if (toast.value?.message === message) toast.value = null }, 3000)
}

// One row per configured selling price list (same source as PriceListUpdate), plus saved extras
function buildRows(saved = []) {
  let names = []
  try { names = JSON.parse(localStorage.getItem('wb-pricelist') || '[]') } catch { names = [] }
  if (!names.length) names = ['Standard Selling']
  for (const s of saved) {
    if (s.pricelist && !names.includes(s.pricelist)) names.push(s.pricelist)
  }
  names = names.filter(n => !n.toLowerCase().includes('buying'))
  pctRows.value = names.map(pricelist => {
    const hit = saved.find(s => s.pricelist === pricelist)
    return { pricelist, percentage: hit ? hit.percentage : '' }
  })
  pctInputs.length = pctRows.value.length
}

function focusPct(i) {
  nextTick(() => {
    const el = pctInputs[i]
    if (el) { el.focus(); el.select() } else save()
  })
}

function moveHighlight(dir) {
  const n = filtered.value.length
  if (n) highlight.value = (highlight.value + dir + n) % n
}

async function loadList() {
  listLoading.value = true
  try {
    records.value = await frappeGet(`${API}.get_competitive_items`) || []
  } catch (e) {
    showToast('Failed to load list: ' + e.message, 'error')
  } finally {
    listLoading.value = false
  }
}

function newRecord() {
  form.name = ''
  form.competitive_item_name = ''
  linkedItems.value = []
  buildRows()
  nextTick(() => nameInput.value?.focus())
}

async function openRecord(name) {
  detailLoading.value = true
  try {
    const data = await frappeGet(`${API}.get_competitive_item`, { name })
    form.name = data.name
    form.competitive_item_name = data.name
    linkedItems.value = data.items || []
    buildRows(data.pricelist_percentages || [])
  } catch (e) {
    showToast('Failed to load: ' + e.message, 'error')
  } finally {
    detailLoading.value = false
    nextTick(() => nameInput.value?.focus())
  }
}

async function save() {
  if (saving.value || !form.competitive_item_name.trim()) return
  saving.value = true
  try {
    const res = await frappePost(`${API}.save_competitive_item`, {
      data: JSON.stringify({
        name: form.name,
        competitive_item_name: form.competitive_item_name.trim(),
        pricelist_percentages: pctRows.value
          .filter(r => r.percentage !== '' && r.percentage !== null)
          .map(r => ({ pricelist: r.pricelist, percentage: parseFloat(r.percentage) })),
      }),
    })
    showToast(`${res.name} saved`)
    await loadList()
    await openRecord(res.name)
  } catch (e) {
    showToast('Save failed: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!form.name || !confirm(`Delete competitive item ${form.name}?`)) return
  saving.value = true
  try {
    await frappePost(`${API}.delete_competitive_item`, { name: form.name })
    showToast(`${form.name} deleted`)
    newRecord()
    await loadList()
  } catch (e) {
    showToast('Delete failed: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

function onKeydown(e) {
  if (e.key === 'F2') {
    e.preventDefault()
    newRecord()
  } else if (e.key === 'F8') {
    e.preventDefault()
    save()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    router.push('/')
  }
}

onMounted(() => {
  buildRows()
  loadList()
  window.addEventListener('keydown', onKeydown)
  nextTick(() => nameInput.value?.focus())
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>
