/**
 * src/shortcuts/journalContraShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Journal & Contra Entry page.
 */

export const journalContraShortcuts = (handlers) => ({
  'F7':        handlers.cycleEntryType,
  'INSERT':    handlers.addRow,
  'F9':        handlers.saveEntry,
  'ARROWUP':   handlers.navigateUp,
  'ARROWDOWN': handlers.navigateDown,
  'PAGEUP':    handlers.focusDate,
  'PAGEDOWN':  handlers.focusLastRow,
  'ENTER':     handlers.handleEnter,
  'END':       handlers.jumpToRemarks,
  'ESCAPE':    handlers.goBack,
});
