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
  'F7': () => handlers.openModule('pricelist-update'),
  'F8': () => handlers.openModule('journal-contra'),
  'F9': () => handlers.openModule('payment'),
  'F10': () => handlers.openModule('material-transfer'),
  
  '1': () => handlers.openModule('sales'),
  '2': () => handlers.openModule('purchase'),
  '3': () => handlers.openModule('payment'),
  '4': () => handlers.openModule('purchase-submit'),
  '5': () => handlers.openModule('cashier'),
  '6': () => handlers.openModule('ledger'),
  '7': () => handlers.openModule('pricelist-update'),
  '8': () => handlers.openModule('journal-contra'),
  '9': () => handlers.openModule('material-transfer'),
  
  'CTRL+L': () => handlers.openCustomerSearch?.(),
  'CTRL+I': () => handlers.openItemSearch?.(),

  'ESCAPE': handlers.handleEscape,
});
