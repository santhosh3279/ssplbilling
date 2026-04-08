/**
 * src/shortcuts/salesInvoiceShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Keyboard shortcuts for the SalesInvoice page.
 */

export const salesInvoiceShortcuts = (handlers) => ({
  'F1':     handlers.openShortcuts   || (() => {}),
  'F4':     handlers.openSeries      || (() => {}),
  'F5':     handlers.print           || (() => {}),
  'F6':     handlers.selectCustomer  || (() => {}),
  'F8':     handlers.save            || (() => {}),
  'CTRL+S': handlers.save            || (() => {}),
  'ESCAPE': handlers.cancel          || (() => {}),
  'DELETE': handlers.deleteRow       || (() => {}),
})
