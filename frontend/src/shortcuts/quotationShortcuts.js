/**
 * src/shortcuts/quotationShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Keyboard shortcuts for the Quotation page.
 */

export const quotationShortcuts = (handlers) => ({
  'SHIFT+F1': handlers.openShortcuts    || (() => {}),
  'F2':      handlers.clearBill        || (() => {}),
  'F3':      handlers.focusModifyPanel || (() => {}),
  'F5':      handlers.print            || (() => {}),
  'F6':      handlers.openCustomAddress|| (() => {}),
  'M':       handlers.modify           || (() => {}),
  'P':       handlers.print            || (() => {}),
  'F8':      handlers.save             || (() => {}),
  'CTRL+S':  handlers.save             || (() => {}),
  'PAGEUP':  handlers.pageUp           || (() => {}),
  'ESCAPE':  handlers.cancel           || (() => {}),
  'DELETE':  handlers.deleteRow        || (() => {}),
  'CTRL+O':  handlers.openGstBillCreator|| (() => {}),
})
