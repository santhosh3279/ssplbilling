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
  'F2':     handlers.newBill,
  'F3':     handlers.focusModifyPanel,
  'F4':     handlers.focusSidebarSeries,
  'F5':     handlers.print,
  'CTRL+M': handlers.enterEditMode,
  'PAGEUP': handlers.focusSeries,
  'END':    handlers.toggleDiscountSave,
  'HOME':   handlers.jumpToFirstRow,
  'INSERT': handlers.openIncentive,
  'ESCAPE': handlers.contextualBack,
});
