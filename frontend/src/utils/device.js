// Phone detection for routing (not width-based, so a narrow desktop window stays on the desktop UI).
// Same UA test as composables/useDevice.js; tablets are not phones.
export function isMobileDevice() {
  if (typeof navigator === 'undefined') return false
  if (typeof navigator.userAgentData?.mobile === 'boolean') return navigator.userAgentData.mobile
  return /mobile|iphone|ipod|android.*mobile/i.test(navigator.userAgent)
}

// sessionStorage flag set by the mobile dashboard's "Desktop view" link
export const DESKTOP_VIEW_KEY = 'wb-desktop-view'
