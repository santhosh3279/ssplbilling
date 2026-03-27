/**
 * src/services/shortcutManager.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Centralized Keyboard Shortcut Manager
 *
 * Priority (highest → lowest):
 *   active subwindow  →  active page (local)  →  global
 *
 * Subwindow shortcuts use a STACK instead of a shared flat Map:
 *   - Only the TOP entry is checked when dispatching.
 *   - When any layer is on the stack, local and global shortcuts are suppressed.
 *
 * How layers are built for a component that is both a subwindow AND has shortcuts:
 *   1. useSubwindow()            → pushes an empty Map  (blocks parent on mount)
 *   2. useShortcuts(s,'subwindow')→ pushes a shortcuts Map on top
 *   Stack: [..., emptyMap, shortcutsMap]  ← top is shortcutsMap (active)
 *
 * When a deeper sub-subwindow opens (useSubwindow() only, no own shortcuts):
 *   Stack: [..., emptyMap, shortcutsMap, emptyMap2]  ← top is emptyMap2
 *   → nothing fires, parent shortcuts are suppressed  ✓
 *
 * When that sub-subwindow closes: emptyMap2 is popped, shortcutsMap is top again.
 */

import { onMounted, onUnmounted, watch } from 'vue'

// Flat registries for page-level and global shortcuts
const registry = {
  global: new Map(),
  local:  new Map(),
}

// Stack of Maps — each mounted subwindow layer owns one slot.
// Only the last slot (top) is consulted on keydown.
const subwindowStack = []

function getEventKey(e) {
  const parts = []
  if (e.ctrlKey || e.metaKey) parts.push('CTRL')
  if (e.shiftKey)              parts.push('SHIFT')
  if (e.altKey)                parts.push('ALT')
  const key = e.key.toUpperCase()
  if (!['CONTROL', 'SHIFT', 'ALT', 'META'].includes(key)) parts.push(key)
  return parts.join('+')
}

function handleKeyDown(e) {
  const key = getEventKey(e)

  // 1. Active subwindow — only the top of the stack is checked.
  //    Even if the top map has no matching key, local/global are still blocked.
  if (subwindowStack.length > 0) {
    const topMap = subwindowStack[subwindowStack.length - 1]
    if (topMap.has(key)) {
      e.preventDefault()
      topMap.get(key)(e)
    } else if (['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12'].includes(key)) {
      // Always prevent default for function keys even if not handled, to stop browser search etc.
      e.preventDefault()
    }
    return
  }

  // 2. Active page (local)
  if (registry.local.has(key)) {
    e.preventDefault()
    registry.local.get(key)(e)
    return
  }

  // 3. Global (lowest priority)
  if (registry.global.has(key)) {
    e.preventDefault()
    registry.global.get(key)(e)
    return
  }

  // 4. Default prevention for unhandled function keys
  if (['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12'].includes(key)) {
    e.preventDefault()
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('keydown', handleKeyDown)
}

// ─── Internal helpers ────────────────────────────────────────────────────────

function stackPush(map) {
  subwindowStack.push(map)
}

function stackRemove(map) {
  const idx = subwindowStack.lastIndexOf(map)
  if (idx >= 0) subwindowStack.splice(idx, 1)
}

// ─── Public API (used by composables and external code) ──────────────────────

export const shortcutManager = {
  /** Register a key at 'global' or 'local' level. */
  register(key, action, level = 'local') {
    registry[level]?.set(key.toUpperCase(), action)
  },

  /** Remove a key from 'global' or 'local' level. */
  unregister(key, level = 'local') {
    registry[level]?.delete(key.toUpperCase())
  },

  /**
   * Remove a key only if the stored action still matches.
   * Prevents a departing component from clearing a key re-registered by the
   * incoming component (same route, different instance).
   */
  unregisterIfMatches(key, action, level = 'local') {
    const k = key.toUpperCase()
    if (registry[level]?.get(k) === action) registry[level].delete(k)
  },

  clearLevel(level = 'local') {
    registry[level]?.clear()
  },
}

// ─── Public helpers ───────────────────────────────────────────────────────────

/** Returns true when any subwindow layer is on the stack (used by components
 *  that manage their own open-trigger logic outside the shortcut manager). */
export function isSubwindowActive() {
  return subwindowStack.length > 0
}

// ─── Vue composables ─────────────────────────────────────────────────────────

/**
 * Register shortcuts for the current component.
 *
 * level = 'global'    — permanent app-wide shortcuts (App.vue)
 * level = 'local'     — page-level shortcuts, cleaned up on unmount
 * level = 'subwindow' — stack-based: pushes a Map on mount, pops on unmount;
 *                       only the topmost subwindow layer receives key events
 */
export function useShortcuts(shortcuts, level = 'local') {
  if (level === 'subwindow') {
    const map = new Map()
    Object.entries(shortcuts).forEach(([key, action]) => {
      map.set(key.toUpperCase(), action)
    })
    onMounted(() => stackPush(map))
    onUnmounted(() => stackRemove(map))
    return
  }

  const entries = Object.entries(shortcuts)
  entries.forEach(([key, action]) => shortcutManager.register(key, action, level))

  if (level !== 'global') {
    onUnmounted(() => {
      entries.forEach(([key, action]) => {
        shortcutManager.unregisterIfMatches(key, action, level)
      })
    })
  }
}

/**
 * Call inside any component that is used as a subwindow overlay.
 *
 * Pushes an EMPTY Map onto the subwindow stack on mount, blocking the parent
 * page's local and global shortcuts. Pops it on unmount.
 *
 * If the component also calls useShortcuts(shortcuts, 'subwindow'), that call
 * pushes its own Map ON TOP, so the component's shortcuts are the active ones
 * while any deeper sub-subwindow will push yet another layer above it.
 */
export function useSubwindow() {
  let map
  onMounted(() => {
    map = new Map()
    stackPush(map)
  })
  onUnmounted(() => {
    if (map) stackRemove(map)
  })
}

/**
 * For components that are always mounted but control visibility through a
 * reactive `show` prop/ref rather than being conditionally mounted via v-if.
 *
 * Watches `showRef` and pushes a Map onto the subwindow stack when true,
 * removes it when false.  Pass `shortcuts` to also register subwindow-level
 * shortcuts (same semantics as useShortcuts(s, 'subwindow')).
 *
 * Usage inside a component's <script setup>:
 *   useSubwindowWatcher(computed(() => props.show))
 *   useSubwindowWatcher(computed(() => props.show), { ESCAPE: () => emit('close') })
 */
export function useSubwindowWatcher(showRef, shortcuts = {}) {
  let map = null

  function open() {
    if (map) return
    map = new Map(Object.entries(shortcuts).map(([k, v]) => [k.toUpperCase(), v]))
    stackPush(map)
  }

  function close() {
    if (map) { stackRemove(map); map = null }
  }

  watch(showRef, val => (val ? open() : close()), { immediate: true })
  onUnmounted(close)
}
