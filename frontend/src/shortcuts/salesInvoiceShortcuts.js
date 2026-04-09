/**
 * src/shortcuts/salesInvoiceShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Keyboard shortcuts for the SalesInvoice page.
 */

export const salesInvoiceShortcuts = (handlers) => ({
  'F1':      handlers.openShortcuts    || (() => {}),
  'F2':      handlers.clearBill        || (() => {}),
  'F3':      handlers.focusModifyPanel || (() => {}),
  'F4':      handlers.openSeries       || (() => {}),
  'F5':      handlers.print            || (() => {}),
  'F6':      handlers.openParcelAddress|| (() => {}),
  'F8':      handlers.save             || (() => {}),
  'CTRL+S':  handlers.save             || (() => {}),
  'INSERT':  handlers.openIncentive    || (() => {}),
  'PAGEUP':  handlers.pageUp           || (() => {}),
  'ESCAPE':  handlers.cancel           || (() => {}),
  'DELETE':  handlers.deleteRow        || (() => {}),
})
