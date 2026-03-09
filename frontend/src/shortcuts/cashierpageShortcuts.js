/**
 * src/shortcuts/cashierpageShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Cashier Desk page.
 */

export const cashierpageShortcuts = (handlers) => ({
  'ARROWUP':   handlers.navigateBillsUp,
  'ARROWDOWN': handlers.navigateBillsDown,
  'ENTER':     handlers.handleEnter,
  'F9':        handlers.submitPayment,
  'ESCAPE':    handlers.goBack,
});
