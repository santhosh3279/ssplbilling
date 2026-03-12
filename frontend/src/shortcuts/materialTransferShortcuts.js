/**
 * src/shortcuts/materialTransferShortcuts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Specific keyboard shortcuts for the Material Transfer page.
 */

import { entryFormShortcuts } from './pageShortcuts';

export const materialTransferShortcuts = (handlers) => ({
  // Include standard entry form shortcuts (F8, Ctrl+S, F4, Delete)
  ...entryFormShortcuts(handlers),

  // Material Transfer specific
  'PAGEUP': handlers.focusSeries,
  'ESCAPE': handlers.contextualBack,
});
