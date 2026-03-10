/**
 * src/shortcuts/journalContraShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Journal & Contra Entry page.
 */

export const journalContraShortcuts = (handlers) => ({
  'F2':        handlers.switchToJournal,
  'F3':        handlers.switchToContra,
  'INSERT':    handlers.addRow,
  'F9':        handlers.saveEntry,
  'ARROWUP':   handlers.navigateUp,
  'ARROWDOWN': handlers.navigateDown,
  'PAGEUP':    handlers.focusDate,
  'ENTER':     handlers.handleEnter,
  'ESCAPE':    handlers.goBack,
});
