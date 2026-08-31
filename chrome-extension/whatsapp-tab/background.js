// Focuses the WhatsApp Web tab the operator already has open and points it at the chat
// for the bill being shared. A page cannot do this itself: web.whatsapp.com sends
// Cross-Origin-Opener-Policy: same-origin, which severs the opener link and clears the
// window name, so window.open() can never re-target that tab. chrome.tabs can.

const WHATSAPP_TAB_PATTERNS = ['*://web.whatsapp.com/*']

// Phone the tab is already showing, so an operator sending a second bill to the same
// party gets a focus instead of a full WhatsApp Web reload.
function phoneOf(url) {
  try {
    return new URL(url).searchParams.get('phone') || ''
  } catch {
    return ''
  }
}

async function openChat(url) {
  const tabs = await chrome.tabs.query({ url: WHATSAPP_TAB_PATTERNS })

  if (!tabs.length) {
    const created = await chrome.tabs.create({ url, active: true })
    return { ok: true, reused: false, tabId: created.id }
  }

  // Prefer a tab already on the right chat, else the most recently used one.
  const wanted = phoneOf(url)
  const target =
    (wanted && tabs.find((t) => phoneOf(t.url || '') === wanted)) ||
    tabs.sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0))[0]

  const alreadyOnChat = wanted && phoneOf(target.url || '') === wanted
  await chrome.tabs.update(target.id, alreadyOnChat ? { active: true } : { active: true, url })
  await chrome.windows.update(target.windowId, { focused: true })

  return { ok: true, reused: true, renavigated: !alreadyOnChat, tabId: target.id }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== 'SSPL_WHATSAPP_OPEN' || !message.url) return

  openChat(message.url)
    .then(sendResponse)
    .catch((e) => sendResponse({ ok: false, error: String(e) }))

  // Keeps the message channel open for the async reply above.
  return true
})
