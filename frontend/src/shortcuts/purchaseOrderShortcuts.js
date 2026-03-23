/**
 * src/shortcuts/purchaseOrderShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Purchase Order page.
 */

import { entryFormShortcuts } from './pageShortcuts';

export const purchaseOrderShortcuts = (handlers) => ({
  // Include standard entry form shortcuts (F8, Ctrl+S, F2, F4, Delete)
  ...entryFormShortcuts(handlers),

  // Purchase Order specific
  'PAGEUP': handlers.focusSeries,
  'END':    handlers.toggleDiscountSave,
  'ESCAPE': handlers.contextualBack,
});
