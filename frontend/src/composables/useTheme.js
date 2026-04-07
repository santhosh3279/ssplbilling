import { ref } from 'vue'

const STORAGE_KEY = 'Session_Theme'
const PERSISTENT_KEY = 'wb-theme'
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
  const sessionSaved = localStorage.getItem(STORAGE_KEY)
  const persistentSaved = localStorage.getItem(PERSISTENT_KEY)
  
  // Fallback chain: Session_Theme -> wb-theme -> default
  applyTheme(sessionSaved || persistentSaved || DEFAULT_THEME)
}

/** Flip between light and dark. */
function toggleTheme() {
  applyTheme(theme.value === 'dark' ? 'light' : 'dark')
}

export function useTheme() {
  // Ensure theme ref is populated if composable is used before initTheme runs
  if (theme.value === null) {
    const sessionSaved = localStorage.getItem(STORAGE_KEY)
    const persistentSaved = localStorage.getItem(PERSISTENT_KEY)
    theme.value = _normalise(sessionSaved || persistentSaved)
  }
  return { theme, applyTheme, initTheme, toggleTheme }
}
