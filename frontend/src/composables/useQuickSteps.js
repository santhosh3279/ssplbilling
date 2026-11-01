import { computed, ref, watch } from 'vue'
import { searchSuppliers } from '../api'

// Joins the answers of a multi-step quick button; ai_chat_quick.STEP_SEP splits them again.
export const STEP_SEP = ' | '

const SUGGESTERS = {
  supplier: async (text) =>
    ((await searchSuppliers(text)) || []).slice(0, 8).map((s) => ({
      value: s.name,
      label: s.supplier_name && s.supplier_name !== s.name ? `${s.supplier_name} (${s.name})` : s.name,
    })),
}

/**
 * Quick buttons with `steps` (e.g. supplier, then sales months) ask one thing per Enter in the
 * chat box. `pendingQuick` is the picked quick action, `input` the chat box text.
 */
export function useQuickSteps(pendingQuick, input) {
  const answers = ref([])
  const step = computed(() => pendingQuick.value?.steps?.[answers.value.length] || null)
  const suggestions = ref([])
  let timer = null
  let seq = 0

  watch(pendingQuick, () => {
    answers.value = []
    suggestions.value = []
  })

  watch([input, step], ([text, s]) => {
    clearTimeout(timer)
    const suggest = s?.suggest && SUGGESTERS[s.suggest]
    const q = (text || '').trim()
    if (!suggest || !q) {
      seq++
      suggestions.value = []
      return
    }
    timer = setTimeout(async () => {
      const mine = ++seq
      try {
        const rows = await suggest(q)
        if (mine === seq) suggestions.value = rows
      } catch {
        if (mine === seq) suggestions.value = []
      }
    }, 250)
  })

  /** Records one answer. Returns undefined (nothing to take), null (ask the next step) or the
   * joined query once every step is answered. */
  function take(text) {
    const value = (text || '').trim() || step.value?.default || ''
    if (!value) return undefined
    answers.value.push(value)
    seq++
    suggestions.value = []
    return step.value ? null : answers.value.join(STEP_SEP)
  }

  const prompt = computed(() => {
    const s = step.value
    if (!s) return ''
    const done = answers.value.length ? ` (${answers.value.join(' · ')})` : ''
    return `${pendingQuick.value.label}${done} — ${s.label}: ${s.hint}`
  })

  return { step, answers, suggestions, take, prompt }
}
