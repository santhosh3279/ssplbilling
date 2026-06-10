/**
 * src/shortcuts/dashboardShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Dashboard page.
 */

export const dashboardShortcuts = (handlers) => ({
  'SHIFT+F2': () => handlers.openModule('purchase'),
  'SHIFT+F3': () => handlers.openModule('payment'),
  'SHIFT+F4': () => handlers.openModule('purchase-submit'),
  'SHIFT+F5': () => handlers.openModule('cashier'),
  'SHIFT+F6': () => handlers.openModule('ledger'),
  'SHIFT+F7': () => handlers.openModule('barcode-print'),
  'SHIFT+F8': () => handlers.openModule('journal-contra'),
  'SHIFT+F9': () => handlers.openModule('material-transfer'),
  'SHIFT+F10': () => handlers.openModule('quotation'),
  'CTRL+R': () => handlers.openModule('stock-reconciliation'),
  'CTRL+L': () => window.dispatchEvent(new CustomEvent('wb-global-ledger-search')),
  'CTRL+G': () => window.dispatchEvent(new CustomEvent('wb-open-gst-validator')),

  'ESCAPE': handlers.handleEscape,
  });
