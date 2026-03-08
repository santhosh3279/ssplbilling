/**
 * src/shortcuts/salesEntryShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Sales Entry page.
 */

import { entryFormShortcuts } from './pageShortcuts';

export const salesEntryShortcuts = (handlers) => ({
  // Include standard entry form shortcuts (F8, Ctrl+S, F2, F4, Delete)
  ...entryFormShortcuts(handlers),

  // Sales Entry specific
  'PAGEUP': handlers.focusSeries,
  'END':    handlers.toggleDiscountSave,
  'ESCAPE': handlers.contextualBack,
});
