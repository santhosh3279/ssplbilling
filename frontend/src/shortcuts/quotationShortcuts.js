/**
 * src/shortcuts/quotationShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Keyboard shortcuts for the Quotation page.
 */

export const quotationShortcuts = (handlers) => ({
  'F1':      handlers.openShortcuts    || (() => {}),
  'F2':      handlers.clearBill        || (() => {}),
  'F3':      handlers.focusModifyPanel || (() => {}),
  'F4':      handlers.openSeries       || (() => {}),
  'F5':      handlers.print            || (() => {}),
  'CTRL+M':  handlers.modify           || (() => {}),
  'CTRL+P':  handlers.print            || (() => {}),
  'F8':      handlers.save             || (() => {}),
  'CTRL+S':  handlers.save             || (() => {}),
  'PAGEUP':  handlers.pageUp           || (() => {}),
  'ESCAPE':  handlers.cancel           || (() => {}),
  'DELETE':  handlers.deleteRow        || (() => {}),
})
