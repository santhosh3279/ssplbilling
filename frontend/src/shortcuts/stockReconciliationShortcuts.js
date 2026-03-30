/**
 * src/shortcuts/stockReconciliationShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Stock Reconciliation page.
 */

import { entryFormShortcuts } from './pageShortcuts';

export const stockReconciliationShortcuts = (handlers) => ({
  // Include standard entry form shortcuts (F8, Ctrl+S, F4, Delete)
  ...entryFormShortcuts(handlers),

  // Stock Reconciliation specific
  'F2': handlers.focusWarehouse,
  'F7': handlers.fetchItems,
  'ESCAPE': handlers.contextualBack,
});
