/**
 * src/shortcuts/salesInvoiceShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Keyboard shortcuts for the SalesInvoice page.
 */

export const salesInvoiceShortcuts = (handlers) => ({
  'SHIFT+F1': handlers.openShortcuts    || (() => {}),
  'F2':      handlers.clearBill        || (() => {}),
  'F3':      handlers.focusModifyPanel || (() => {}),
  'F5':      handlers.print            || (() => {}),
  'M':       handlers.modify           || (() => {}),
  'P':       handlers.print            || (() => {}),
  'F6':      handlers.openParcelAddress|| (() => {}),
  'F8':      handlers.save             || (() => {}),
  'CTRL+S':  handlers.save             || (() => {}),
  'PAGEUP':  handlers.pageUp           || (() => {}),
  'ESCAPE':  handlers.cancel           || (() => {}),
  'DELETE':  handlers.deleteRow        || (() => {}),
  'CTRL+O':  handlers.openGstBillCreator|| (() => {}),
  'CTRL+K':  handlers.openBillMirror    || (() => {}),
  'CTRL+SHIFT+K': handlers.retryMirrorBill || (() => {}),
})
