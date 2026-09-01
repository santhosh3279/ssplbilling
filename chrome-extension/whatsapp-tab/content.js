// Bridge between the SSPL Billing page and the extension. The page has no extension id to
// talk to, so it posts a window message and this script relays it to the service worker.

const REQUEST = 'SSPL_WHATSAPP_OPEN'
const RESULT = 'SSPL_WHATSAPP_RESULT'

// Read synchronously by the page inside the click handler to decide whether to open a tab
// itself: with the bridge present it must not, or the operator gets two tabs.
document.documentElement.dataset.ssplWhatsappBridge = '1'

const reply = (requestId, result) =>
  window.postMessage({ type: RESULT, requestId, ...result }, window.location.origin)

window.addEventListener('message', (event) => {
  if (event.source !== window) return

  const data = event.data
  if (!data || data.type !== REQUEST || !data.url) return

  try {
    // attachment carries the bill as base64 — chrome messaging is JSON, so no ArrayBuffer.
    chrome.runtime.sendMessage(
      { type: REQUEST, url: data.url, attachment: data.attachment || null },
      (response) => {
        reply(data.requestId, {
          ok: !chrome.runtime.lastError && !!response?.ok,
          reused: !!response?.reused,
          attached: !!response?.attached,
          method: response?.method || '',
          error: chrome.runtime.lastError?.message || response?.error || '',
        })
      },
    )
  } catch (e) {
    // Reloading the extension orphans this script: chrome.runtime still exists but its port is
    // dead, and sendMessage throws "Extension context invalidated". Answering here turns a share
    // that hung for the page's full 30s timeout into an immediate, accurate message.
    reply(data.requestId, {
      ok: false,
      reused: false,
      attached: false,
      method: '',
      error: `${e.message || e} — reload this page after updating the extension`,
    })
  }
})
