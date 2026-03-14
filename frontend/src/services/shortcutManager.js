/**
 * src/services/shortcutManager.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Centralized Keyboard Shortcut Manager
 * Handles global and local (page-specific) shortcuts with priority logic.
 *
 * Priority (highest → lowest):
 *   subwindow  →  local (page)  →  global
 *
 * When any subwindow is active (subwindowDepth > 0), local and global shortcuts
 * are suppressed so they cannot fire "through" an open subwindow.
 * Subwindow components call useSubwindow() to increment/decrement the depth.
 */

import { onMounted, onUnmounted } from 'vue';

const registry = {
  global: new Map(),
  local: new Map(),
  subwindow: new Map(),
};

// Tracks how many subwindows are currently mounted. Supports nested subwindows.
let subwindowDepth = 0;

/**
 * Normalizes event to a string key like "CTRL+SHIFT+S" or "F8"
 */
function getEventKey(e) {
  const parts = [];
  if (e.ctrlKey || e.metaKey) parts.push('CTRL');
  if (e.shiftKey) parts.push('SHIFT');
  if (e.altKey) parts.push('ALT');

  const key = e.key.toUpperCase();

  if (!['CONTROL', 'SHIFT', 'ALT', 'META'].includes(key)) {
    parts.push(key);
  }

  return parts.join('+');
}

/**
 * Main Event Listener — respects subwindow > local > global priority.
 */
function handleKeyDown(e) {
  const shortcutKey = getEventKey(e);

  // 1. Subwindow shortcuts always fire first
  if (registry.subwindow.has(shortcutKey)) {
    e.preventDefault();
    registry.subwindow.get(shortcutKey)(e);
    return;
  }

  // 2. If any subwindow is active, suppress local and global shortcuts.
  //    The subwindow's own window listener will handle the key instead.
  if (subwindowDepth > 0) return;

  // 3. Local (page) shortcuts
  if (registry.local.has(shortcutKey)) {
    e.preventDefault();
    registry.local.get(shortcutKey)(e);
    return;
  }

  // 4. Global shortcuts
  if (registry.global.has(shortcutKey)) {
    e.preventDefault();
    registry.global.get(shortcutKey)(e);
    return;
  }
}

// Initialize listener once at module load time
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', handleKeyDown);
}

export const shortcutManager = {
  /**
   * Register a shortcut.
   * @param {string} key    - e.g. "CTRL+L", "F8", "ESCAPE"
   * @param {Function} action
   * @param {string} level  - "global" | "local" | "subwindow"
   */
  register(key, action, level = 'local') {
    registry[level].set(key.toUpperCase(), action);
  },

  /**
   * Remove a specific shortcut.
   */
  unregister(key, level = 'local') {
    registry[level].delete(key.toUpperCase());
  },

  /**
   * Remove a shortcut only if the stored action still matches the registered one.
   * Prevents a departing component from wiping shortcuts registered by the newly-
   * mounted component when both share the same key.
   */
  unregisterIfMatches(key, action, level = 'local') {
    const normalizedKey = key.toUpperCase();
    if (registry[level].get(normalizedKey) === action) {
      registry[level].delete(normalizedKey);
    }
  },

  /**
   * Clear all shortcuts for a specific level.
   */
  clearLevel(level = 'local') {
    registry[level].clear();
  },

  /** Called when a subwindow mounts. */
  enterSubwindow() {
    subwindowDepth++;
  },

  /** Called when a subwindow unmounts. */
  exitSubwindow() {
    subwindowDepth = Math.max(0, subwindowDepth - 1);
  },
};

/**
 * Vue composable — register shortcuts for the current component.
 * On unmount, only the shortcuts registered by THIS call are removed.
 */
export function useShortcuts(shortcuts, level = 'local') {
  const entries = Object.entries(shortcuts);

  entries.forEach(([key, action]) => {
    shortcutManager.register(key, action, level);
  });

  if (level !== 'global') {
    onUnmounted(() => {
      entries.forEach(([key, action]) => {
        shortcutManager.unregisterIfMatches(key, action, level);
      });
    });
  }
}

/**
 * Vue composable — call this inside any component that is used as a subwindow
 * (i.e. receives an `isSubWindow` prop and mounts over a parent page).
 *
 * While mounted, suppresses the parent page's local and global shortcuts so
 * the subwindow's own keyboard handlers have exclusive access to all keys.
 */
export function useSubwindow() {
  onMounted(() => shortcutManager.enterSubwindow());
  onUnmounted(() => shortcutManager.exitSubwindow());
}
