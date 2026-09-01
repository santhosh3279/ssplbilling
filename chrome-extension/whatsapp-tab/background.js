// Focuses the WhatsApp Web tab the operator already has open and shows the chat for the bill
// being shared. A page cannot do this itself: web.whatsapp.com sends
// Cross-Origin-Opener-Policy: same-origin, which severs the opener link and clears the window
// name, so window.open() can never re-target that tab. chrome.tabs can.
//
// The chat is switched from inside the page (whatsapp.js drives WhatsApp's own search box) so
// the tab is never navigated and never reloads. Navigation is kept only as a fallback for when
// that fails — a WhatsApp UI change, a logged-out tab, a number with no matching chat.

const WHATSAPP_TAB_PATTERNS = ['*://web.whatsapp.com/*']
const CHAT_OPEN = 'SSPL_WA_OPEN_CHAT'

// tabId -> phone whose chat that tab is showing. WhatsApp strips ?phone= from its URL moments
// after loading, so the tab's own URL cannot answer this question.
const openChats = new Map()
chrome.tabs.onRemoved.addListener((tabId) => openChats.delete(tabId))

function phoneOf(url) {
  try {
    return new URL(url).searchParams.get('phone') || ''
  } catch {
    return ''
  }
}

async function askPage(tabId, phone) {
  try {
    return await chrome.tabs.sendMessage(tabId, { type: CHAT_OPEN, phone })
  } catch {
    // No content script in there: the tab was open before the extension was loaded or reloaded.
    try {
      await chrome.scripting.executeScript({ target: { tabId }, files: ['whatsapp.js'] })
      return await chrome.tabs.sendMessage(tabId, { type: CHAT_OPEN, phone })
    } catch (e) {
      return { ok: false, error: String(e) }
    }
  }
}

async function openChat(url) {
  const wanted = phoneOf(url)
  const tabs = await chrome.tabs.query({ url: WHATSAPP_TAB_PATTERNS })

  if (!tabs.length) {
    const created = await chrome.tabs.create({ url, active: true })
    if (wanted) openChats.set(created.id, wanted)
    return { ok: true, reused: false, method: 'new-tab' }
  }

  const target = tabs.sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0))[0]
  await chrome.tabs.update(target.id, { active: true })
  await chrome.windows.update(target.windowId, { focused: true })

  if (!wanted) return { ok: true, reused: true, method: 'focus' }
  if (openChats.get(target.id) === wanted) return { ok: true, reused: true, method: 'already-open' }

  const searched = await askPage(target.id, wanted)
  if (searched?.ok) {
    openChats.set(target.id, wanted)
    return { ok: true, reused: true, method: 'search' }
  }

  // Last resort. Opens the right chat, at the cost of the reload we are trying to avoid.
  await chrome.tabs.update(target.id, { url })
  openChats.set(target.id, wanted)
  return { ok: true, reused: true, method: 'navigate', error: searched?.error || '' }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== 'SSPL_WHATSAPP_OPEN' || !message.url) return

  openChat(message.url)
    .then(sendResponse)
    .catch((e) => sendResponse({ ok: false, error: String(e) }))

  // Keeps the message channel open for the async reply above.
  return true
})
