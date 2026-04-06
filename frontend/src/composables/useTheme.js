import { ref } from 'vue'

const STORAGE_KEY = 'wb-theme'
const DEFAULT_THEME = 'light'

// Module-level singleton so all callers share the same reactive state
const theme = ref(null)

function _normalise(raw) {
  // Accept 'Light'/'Dark' (legacy) or 'light'/'dark'
  return String(raw || '').toLowerCase() === 'dark' ? 'dark' : 'light'
}

/**
 * Apply `themeName` ('light' | 'dark') to <html> and persist to localStorage.
 * Safe to call before Vue is mounted (used in App.vue onMounted).
 */
function applyTheme(themeName) {
  const t = _normalise(themeName)
  theme.value = t
  const root = document.documentElement
  root.classList.remove('light', 'dark')
  root.classList.add(t)
  localStorage.setItem(STORAGE_KEY, t)
}

/** Read saved preference (or default) and apply it. */
function initTheme() {
  const saved = localStorage.getItem(STORAGE_KEY)
  applyTheme(saved || DEFAULT_THEME)
}

/** Flip between light and dark. */
function toggleTheme() {
  applyTheme(theme.value === 'dark' ? 'light' : 'dark')
}

export function useTheme() {
  // Ensure theme ref is populated if composable is used before initTheme runs
  if (theme.value === null) {
    theme.value = _normalise(localStorage.getItem(STORAGE_KEY))
  }
  return { theme, applyTheme, initTheme, toggleTheme }
}
