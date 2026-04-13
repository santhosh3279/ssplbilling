/**
 * src/shortcuts/dashboardShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Dashboard page.
 */

export const dashboardShortcuts = (handlers) => ({
  'F1': () => handlers.openModule('sales'),
  'F2': () => handlers.openModule('purchase'),
  'F3': () => handlers.openModule('payment'),
  'F4': () => handlers.openModule('purchase-submit'),
  'F5': () => handlers.openModule('cashier'),
  'F6': () => handlers.openModule('ledger'),
  'F7': () => handlers.openModule('barcode-print'),
  'F8': () => handlers.openModule('journal-contra'),
  'F9': () => handlers.openModule('material-transfer'),
  'F10': () => handlers.openModule('quotation'),
  'CTRL+R': () => handlers.openModule('stock-reconciliation'),
  
  'CTRL+L': () => handlers.openCustomerSearch?.(),
  'CTRL+I': () => handlers.openItemSearch?.(),

  'ESCAPE': handlers.handleEscape,
});
