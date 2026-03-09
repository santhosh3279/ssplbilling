/**
 * src/shortcuts/purchaseEntryShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Purchase Entry page.
 */

import { entryFormShortcuts } from './pageShortcuts';

export const purchaseEntryShortcuts = (handlers) => ({
  // Include standard entry form shortcuts (F8, Ctrl+S, F2, F4, Delete)
  ...entryFormShortcuts(handlers),

  // Purchase Entry specific
  'PAGEUP': handlers.focusSeries,
  'END':    handlers.toggleDiscountSave,
  'ESCAPE': handlers.contextualBack,
});
