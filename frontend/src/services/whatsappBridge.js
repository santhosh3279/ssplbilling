/**
 * whatsappBridge.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Talks to the "SSPL WhatsApp Tab" Chrome extension (chrome-extension/whatsapp-tab)
 * so a shared bill lands in the WhatsApp Web tab the operator already has open.
 *
 * A page cannot do this on its own: web.whatsapp.com sends
 * `Cross-Origin-Opener-Policy: same-origin`, which severs the opener link and clears the
 * window name, so `window.open(url, 'name')` always ends up on a fresh tab. The extension
 * holds the `tabs` permission and can focus the real one.
 *
 * With no extension installed every call reports false and the caller falls back to
 * opening a tab itself.
 * ─────────────────────────────────────────────────────────────────────────────
 */

const REQUEST = 'SSPL_WHATSAPP_OPEN'
const RESULT = 'SSPL_WHATSAPP_RESULT'

// The extension's content script gives up after the service worker replies; 3s covers a
// cold worker start without leaving the operator staring at a dead button.
const BRIDGE_TIMEOUT_MS = 3000

let requestCounter = 0

/**
 * Whether the extension's content script is present. Synchronous on purpose: the caller
 * has to decide inside the click handler whether to open a tab itself, and a tab opened
 * after an await is blocked as an unsolicited popup.
 */
export function hasWhatsAppBridge() {
  return document.documentElement.dataset.ssplWhatsappBridge === '1'
}

/**
 * Ask the extension to focus the WhatsApp tab and point it at `url`.
 * @returns {Promise<{ok: boolean, reused: boolean, error: string}>}
 */
export function openWhatsAppTab(url) {
  if (!hasWhatsAppBridge()) {
    return Promise.resolve({ ok: false, reused: false, error: 'extension not installed' })
  }

  const requestId = `wa-${Date.now()}-${++requestCounter}`

  return new Promise((resolve) => {
    let settled = false

    const finish = (result) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      window.removeEventListener('message', onMessage)
      resolve(result)
    }

    const onMessage = (event) => {
      if (event.source !== window) return
      const data = event.data
      if (!data || data.type !== RESULT || data.requestId !== requestId) return
      finish({ ok: !!data.ok, reused: !!data.reused, error: data.error || '' })
    }

    const timer = setTimeout(
      () => finish({ ok: false, reused: false, error: 'extension did not answer' }),
      BRIDGE_TIMEOUT_MS,
    )

    window.addEventListener('message', onMessage)
    window.postMessage({ type: REQUEST, requestId, url }, window.location.origin)
  })
}
