/**
 * src/shortcuts/globalShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Application-wide keyboard shortcuts.
 */

export const globalShortcuts = {
  'CTRL+L': () => {
    window.dispatchEvent(new CustomEvent('wb-global-ledger-search'));
  },
  'CTRL+I': () => {
    window.dispatchEvent(new CustomEvent('wb-global-item-search'));
  },
  // Add other shared shortcuts here (e.g., Home, Settings)
  'ALT+H': () => {
    window.dispatchEvent(new CustomEvent('wb-navigate-home'));
  },
  'ALT+D': () => {
    window.dispatchEvent(new CustomEvent('wb-global-date-focus'));
  }
};
