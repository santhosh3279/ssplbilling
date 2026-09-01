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

// The extension replies once the chat is resolved. That can mean waiting on a cold WhatsApp Web
// boot, then the New chat panel, then its search results — 30s covers the slow end without
// leaving the operator staring at a dead button.
const BRIDGE_TIMEOUT_MS = 30000

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
 * Ask the extension to focus the WhatsApp tab, open the party's chat and — when `attachment` is
 * given — drop the bill into WhatsApp's attachment preview, leaving the operator only to press
 * send. The bill travels as base64 because chrome's messaging is JSON: an ArrayBuffer would
 * arrive as `{}`.
 *
 * @param {string} url
 * @param {{name: string, type: string, data: string, caption: string}} [attachment]
 * @returns {Promise<{ok: boolean, reused: boolean, attached: boolean, method: string, error: string}>}
 */
export function openWhatsAppTab(url, attachment = null) {
  if (!hasWhatsAppBridge()) {
    return Promise.resolve({
      ok: false,
      reused: false,
      attached: false,
      method: '',
      error: 'extension not installed',
    })
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
      finish({
        ok: !!data.ok,
        reused: !!data.reused,
        attached: !!data.attached,
        method: data.method || '',
        error: data.error || '',
      })
    }

    const timer = setTimeout(
      () =>
        finish({
          ok: false,
          reused: false,
          attached: false,
          method: '',
          error: 'extension did not answer',
        }),
      BRIDGE_TIMEOUT_MS,
    )

    window.addEventListener('message', onMessage)
    window.postMessage({ type: REQUEST, requestId, url, attachment }, window.location.origin)
  })
}
