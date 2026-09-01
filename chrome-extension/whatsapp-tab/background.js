// Focuses the WhatsApp Web tab the operator already has open, shows the chat for the bill being
// shared, and hands the bill PDF to that tab so it lands in WhatsApp's own attachment preview.
// A page cannot do any of this itself: web.whatsapp.com sends
// Cross-Origin-Opener-Policy: same-origin, which severs the opener link and clears the window
// name, so window.open() can never re-target that tab. chrome.tabs can.
//
// The chat is switched from inside the page (whatsapp.js drives WhatsApp's own search box) so
// the tab is never navigated and never reloads. Navigation is kept only as a fallback for when
// that fails — a WhatsApp UI change, a logged-out tab, a number with no matching chat.

// Navigating an existing WhatsApp tab to /send?phone= always opens the right chat, but it reboots
// WhatsApp Web. Turned off while the in-place route is being made reliable: a share that cannot
// open the chat now says so instead of reloading. Flip to true to bring the fallback back.
const ALLOW_RELOAD_FALLBACK = false

const WHATSAPP_TAB_PATTERNS = ['*://web.whatsapp.com/*']
const CHAT_OPEN = 'SSPL_WA_OPEN_CHAT'
const ATTACH_NOW = 'SSPL_WA_ATTACH_NOW'
const PENDING = 'SSPL_WA_PENDING'
const TYPE_FOR_ME = 'SSPL_WA_TYPE'

// How long a stashed bill stays attachable. Long enough for a cold WhatsApp Web boot, short
// enough that a bill abandoned mid-share never turns up in a later chat.
const ATTACH_TTL_MS = 120000

const stashKey = (tabId) => `attach:${tabId}`

// tabId -> phone whose chat that tab is showing. WhatsApp strips ?phone= from its URL moments
// after loading, so the tab's own URL cannot answer this question.
const openChats = new Map()
chrome.tabs.onRemoved.addListener((tabId) => {
  openChats.delete(tabId)
  chrome.storage.local.remove(stashKey(tabId))
})

function phoneOf(url) {
  try {
    return new URL(url).searchParams.get('phone') || ''
  } catch {
    return ''
  }
}

// The bill is parked in storage rather than held in a variable: the navigation fallback reloads
// the tab, and this service worker can be evicted while that load runs.
async function stash(tabId, attachment) {
  if (!attachment) return
  await chrome.storage.local.set({ [stashKey(tabId)]: { ...attachment, at: Date.now() } })
}

async function askPage(tabId, message) {
  try {
    return await chrome.tabs.sendMessage(tabId, message)
  } catch {
    // No content script in there: the tab was open before the extension was loaded or reloaded.
    try {
      await chrome.scripting.executeScript({ target: { tabId }, files: ['whatsapp.js'] })
      return await chrome.tabs.sendMessage(tabId, message)
    } catch (e) {
      return { ok: false, error: String(e) }
    }
  }
}

async function openChat(url, attachment) {
  const wanted = phoneOf(url)
  const tabs = await chrome.tabs.query({ url: WHATSAPP_TAB_PATTERNS })

  // A brand new tab and the navigation fallback both land on /send?phone=, where WhatsApp itself
  // resolves the number, so the chat on screen is the right one and the bill can be attached.
  if (!tabs.length) {
    const created = await chrome.tabs.create({ url, active: true })
    await stash(created.id, attachment)
    if (wanted) openChats.set(created.id, wanted)
    return { ok: true, reused: false, attached: !!attachment, method: 'new-tab' }
  }

  const target = tabs.sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0))[0]
  await chrome.tabs.update(target.id, { active: true })
  await chrome.windows.update(target.windowId, { focused: true })

  if (!wanted) {
    // No number to open, so the tab keeps whatever chat it had. Forget what we thought it was
    // showing: a stale entry here would later skip a search and leave a bill pointed at the
    // wrong party. Nothing is attached either — we cannot tell whose chat is on screen.
    openChats.delete(target.id)
    return { ok: true, reused: true, attached: false, method: 'focus' }
  }

  const alreadyThere = openChats.get(target.id) === wanted
  const searched = alreadyThere ? 'confident' : await trySearch(target.id, wanted)

  // Any chat opened in place is used, including one picked as the first result without the number
  // visible on the row. Reloading to be certain costs the operator a full WhatsApp Web boot on
  // every single bill, and they still see the contact in the attachment preview before sending.
  if (searched) {
    openChats.set(target.id, wanted)
    if (attachment) {
      await stash(target.id, attachment)
      await askPage(target.id, { type: ATTACH_NOW })
    }
    return {
      ok: true,
      reused: true,
      attached: !!attachment,
      method: alreadyThere ? 'already-open' : 'search',
    }
  }

  // Nothing is remembered about the chat: we could not open it, and claiming otherwise would make
  // the next share skip straight to focusing whatever is on screen.
  openChats.delete(target.id)

  if (!ALLOW_RELOAD_FALLBACK) {
    // The tab is focused and the bill is in Downloads; the operator opens the chat by hand.
    await chrome.storage.local.remove(stashKey(target.id))
    return {
      ok: true,
      reused: true,
      attached: false,
      method: 'not-opened',
      error: lastSearchError,
    }
  }

  // Opens the right chat, at the cost of the reload. The bill is stashed first so the reloaded
  // page can pick it up on its own — the worker may be evicted while that load runs.
  await stash(target.id, attachment)
  await chrome.tabs.update(target.id, { url })
  return { ok: true, reused: true, attached: !!attachment, method: 'navigate', error: lastSearchError }
}

// Returns 'confident' when the clicked row carried the number itself, 'weak' when the chat was
// found only by elimination, '' when nothing was opened.
let lastSearchError = ''
async function trySearch(tabId, phone) {
  const searched = await askPage(tabId, { type: CHAT_OPEN, phone })
  console.log('[sspl-wa] in-page search for', phone, '->', JSON.stringify(searched))
  lastSearchError = searched?.ok ? '' : searched?.error || ''
  if (!searched?.ok) return ''
  return searched.confident ? 'confident' : 'weak'
}

// Last-resort typing. Every synthetic event a page can fire is ignorable; a debugger-driven
// Input.insertText is the real thing, handled by Chrome before any page code sees it, so React
// cannot tell it from a keystroke. Only reached when the page's own attempts all failed, because
// attaching flashes the "Chrome is being debugged" banner on the tab.
async function typeViaDebugger(tabId, text) {
  const target = { tabId }
  try {
    await chrome.debugger.attach(target, '1.3')
  } catch (e) {
    // Already attached is fine — a previous share may still be detaching.
    if (!String(e).includes('already attached')) return { ok: false, error: String(e) }
  }

  try {
    await chrome.debugger.sendCommand(target, 'Input.insertText', { text })
    return { ok: true }
  } catch (e) {
    return { ok: false, error: String(e) }
  } finally {
    try {
      await chrome.debugger.detach(target)
    } catch {
      // Detached already, or the tab is gone.
    }
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === TYPE_FOR_ME) {
    const tabId = sender.tab?.id
    if (!tabId) return
    typeViaDebugger(tabId, String(message.text || '')).then(sendResponse)
    return true
  }

  // The WhatsApp tab asking, on load, whether a bill is waiting for it.
  if (message?.type === PENDING) {
    const tabId = sender.tab?.id
    if (!tabId) return
    const key = stashKey(tabId)
    chrome.storage.local.get(key).then(({ [key]: found }) => {
      chrome.storage.local.remove(key)
      const fresh = found && Date.now() - found.at < ATTACH_TTL_MS
      sendResponse(fresh ? found : null)
    })
    return true
  }

  if (message?.type !== 'SSPL_WHATSAPP_OPEN' || !message.url) return

  openChat(message.url, message.attachment)
    .then(sendResponse)
    .catch((e) => sendResponse({ ok: false, error: String(e) }))

  // Keeps the message channel open for the async reply above.
  return true
})
