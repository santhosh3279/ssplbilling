/**
 * src/services/shortcutManager.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Centralized Keyboard Shortcut Manager
 * Handles global and local (page-specific) shortcuts with priority logic.
 */

import { onUnmounted } from 'vue';

const registry = {
  global: new Map(),
  local: new Map(),
};

/**
 * Normalizes event to a string key like "CTRL+SHIFT+S" or "F8"
 */
function getEventKey(e) {
  const parts = [];
  if (e.ctrlKey || e.metaKey) parts.push('CTRL');
  if (e.shiftKey) parts.push('SHIFT');
  if (e.altKey) parts.push('ALT');
  
  // Use code for consistency (e.g., "KeyL" vs "l"), or just key.toUpperCase()
  const key = e.key.toUpperCase();
  
  // Avoid adding modifiers twice if the key itself is a modifier
  if (!['CONTROL', 'SHIFT', 'ALT', 'META'].includes(key)) {
    parts.push(key);
  }
  
  return parts.join('+');
}

/**
 * Main Event Listener
 */
function handleKeyDown(e) {
  const shortcutKey = getEventKey(e);
  
  // 1. Check Local (Page) Shortcuts first (Priority)
  if (registry.local.has(shortcutKey)) {
    const action = registry.local.get(shortcutKey);
    e.preventDefault();
    action(e);
    return;
  }

  // 2. Check Global Shortcuts
  if (registry.global.has(shortcutKey)) {
    const action = registry.global.get(shortcutKey);
    e.preventDefault();
    action(e);
    return;
  }
}

// Initialize listener once
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', handleKeyDown);
}

export const shortcutManager = {
  /**
   * Register a shortcut
   * @param {string} key - e.g. "CTRL+L", "F8", "ESCAPE"
   * @param {Function} action - Callback function
   * @param {string} level - "global" or "local"
   */
  register(key, action, level = 'local') {
    const normalizedKey = key.toUpperCase();
    registry[level].set(normalizedKey, action);
  },

  /**
   * Remove a specific shortcut
   */
  unregister(key, level = 'local') {
    const normalizedKey = key.toUpperCase();
    registry[level].delete(normalizedKey);
  },

  /**
   * Clear all shortcuts for a specific level (usually called on unmount)
   */
  clearLevel(level = 'local') {
    registry[level].clear();
  }
};

/**
 * Vue Composable for easy registration in components
 */
export function useShortcuts(shortcuts, level = 'local') {
  // Register all
  Object.entries(shortcuts).forEach(([key, action]) => {
    shortcutManager.register(key, action, level);
  });

  // Automatically cleanup on unmount if local
  if (level === 'local') {
    onUnmounted(() => {
      shortcutManager.clearLevel('local');
    });
  }
}
