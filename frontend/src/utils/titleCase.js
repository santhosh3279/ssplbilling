// Capitalise the first letter of every word; letters already typed in caps stay
// (so "ABC traders" -> "ABC Traders", "s.k. pipes" -> "S.K. Pipes").
export function titleCase(s) {
  return (s || '').replace(/(^|[\s(\-/.&])([a-z])/g, (_, sep, ch) => sep + ch.toUpperCase())
}

// v-title-case: title-cases an input as the user types, keeping the caret in place.
// Listens in the capture phase so it rewrites the value before v-model reads it.
export const vTitleCase = {
  mounted(el) {
    el._titleCase = () => {
      const next = titleCase(el.value)
      if (next === el.value) return
      const { selectionStart, selectionEnd } = el
      el.value = next
      try { el.setSelectionRange(selectionStart, selectionEnd) } catch { /* type without selection */ }
    }
    el.addEventListener('input', el._titleCase, true)
  },
  beforeUnmount(el) {
    el.removeEventListener('input', el._titleCase, true)
  },
}
