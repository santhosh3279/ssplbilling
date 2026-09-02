// Bridge between the SSPL Billing page and the extension. The page has no extension id to
// talk to, so it posts a window message and this script relays it to the service worker.

const REQUEST = 'SSPL_WHATSAPP_OPEN'
const RESULT = 'SSPL_WHATSAPP_RESULT'

// Read synchronously by the page inside the click handler to decide whether to open a tab
// itself: with the bridge present it must not, or the operator gets two tabs.
document.documentElement.dataset.ssplWhatsappBridge = '1'

window.addEventListener('message', (event) => {
  if (event.source !== window) return

  const data = event.data
  if (!data || data.type !== REQUEST || !data.url) return

  // attachment carries the bill as base64 — chrome messaging is JSON, so no ArrayBuffer.
  chrome.runtime.sendMessage(
    { type: REQUEST, url: data.url, attachment: data.attachment || null },
    (response) => {
      window.postMessage(
        {
          type: RESULT,
          requestId: data.requestId,
          ok: !chrome.runtime.lastError && !!response?.ok,
          reused: !!response?.reused,
          attached: !!response?.attached,
          method: response?.method || '',
          error: chrome.runtime.lastError?.message || response?.error || '',
        },
        window.location.origin,
      )
    },
  )
})
