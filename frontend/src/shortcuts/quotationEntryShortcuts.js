/**
 * src/shortcuts/quotationEntryShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Quotation Entry page.
 */

import { entryFormShortcuts } from './pageShortcuts';

export const quotationEntryShortcuts = (handlers) => ({
  // Include standard entry form shortcuts (F8, Ctrl+S, F2, F4, Delete)
  ...entryFormShortcuts(handlers),

  // Quotation Entry specific
  'F2':     handlers.newQuotation,
  'F3':     handlers.focusModifyPanel,
  'F4':     handlers.focusSidebarSeries,
  'F5':     handlers.print,
  'PAGEUP': handlers.focusSeries,
  'END':    handlers.toggleDiscountSave,
  'HOME':   handlers.jumpToFirstRow,
  'ESCAPE': handlers.contextualBack,
});
