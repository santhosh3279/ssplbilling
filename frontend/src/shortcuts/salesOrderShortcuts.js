/**
 * src/shortcuts/salesOrderShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Keyboard shortcuts for the Sales Order Entry page.
 */

import { entryFormShortcuts } from './pageShortcuts';

export const salesOrderShortcuts = (handlers) => ({
  ...entryFormShortcuts(handlers),

  'PAGEUP': handlers.focusSeries,
  'END':    handlers.toggleDiscountSave,
  'ESCAPE': handlers.contextualBack,
});
