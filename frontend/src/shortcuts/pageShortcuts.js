/**
 * src/shortcuts/pageShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Common page-level shortcut definitions that can be reused across different
 * entry forms (Sales, Purchase, etc.)
 */

/**
 * Common entry form shortcuts (Save, New Row, etc.)
 */
export const entryFormShortcuts = (handlers) => ({
  'F8':     handlers.save,
  'CTRL+S': handlers.save,
  'F2':     handlers.newCustomer || (() => {}),
  'F4':     handlers.searchItem || (() => {}),
  'DELETE': handlers.deleteRow || (() => {}),
});
