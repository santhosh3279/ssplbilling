/**
 * src/shortcuts/payrecShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Payment & Receipt Entry page.
 */

export const payrecShortcuts = (handlers) => ({
  'F2':        handlers.switchToReceipt,
  'F3':        handlers.switchToPayment,
  'F4':        handlers.switchToGeneral,
  'F5':        handlers.switchToOpening,
  'INSERT':    handlers.addRow,
  'F9':        handlers.saveEntry,
  'ARROWUP':   handlers.navigateUp,
  'ARROWDOWN': handlers.navigateDown,
  'PAGEUP':    handlers.focusDate,
  'PAGEDOWN':  handlers.focusLastRow,
  'ENTER':     handlers.handleEnter,
  'ESCAPE':    handlers.goBack,
});
