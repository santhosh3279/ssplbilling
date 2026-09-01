// Runs inside web.whatsapp.com. Opens the chat for a phone number by driving WhatsApp's own
// search box, so the tab never reloads. Navigating the tab to /send?phone=... would work too,
// but that reboots the whole WhatsApp Web app and loses whatever the operator was doing.
//
// Injected both declaratively and, for tabs that were already open when the extension loaded,
// on demand by the service worker. The guard below keeps a second injection harmless.

if (!window.__ssplWhatsAppChatOpener) {
  window.__ssplWhatsAppChatOpener = true

  const CHAT_OPEN = 'SSPL_WA_OPEN_CHAT'

  // WhatsApp ships obfuscated class names, so only structural/ARIA hooks are used. Ordered
  // most specific first; the later ones are there to survive small markup changes.
  const SEARCH_BOX = [
    'div[contenteditable="true"][data-tab="3"]',
    '#side div[contenteditable="true"][role="textbox"]',
    '#side div[contenteditable="true"]',
  ]
  const RESULT_ROW = ['#pane-side [role="listitem"]', '#pane-side [role="row"]']

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

  function firstMatch(selectors) {
    for (const selector of selectors) {
      const el = document.querySelector(selector)
      if (el) return el
    }
    return null
  }

  function rows() {
    for (const selector of RESULT_ROW) {
      const found = document.querySelectorAll(selector)
      if (found.length) return [...found]
    }
    return []
  }

  // Identifies what the list is currently showing, so we can tell the search results apart from
  // the chat list that was on screen before we typed.
  function listSignature() {
    return rows()
      .slice(0, 3)
      .map((row) => row.textContent)
      .join('|')
  }

  async function waitFor(check, timeoutMs, stepMs = 120) {
    const deadline = Date.now() + timeoutMs
    for (;;) {
      const value = check()
      if (value) return value
      if (Date.now() > deadline) return null
      await sleep(stepMs)
    }
  }

  // execCommand is the only way to put text in a contenteditable that React actually notices:
  // it fires real beforeinput/input events, which setting textContent does not.
  function typeInto(box, text) {
    box.focus()
    document.execCommand('selectAll', false, null)
    if (text) document.execCommand('insertText', false, text)
    else document.execCommand('delete', false, null)
  }

  function clickRow(row) {
    const target = row.querySelector('[role="gridcell"]') || row
    for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      target.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }))
    }
  }

  async function resultsFor(box, term, before) {
    typeInto(box, term)
    // Wait for the list to actually become the search result, not the chat list we started from.
    const changed = await waitFor(() => listSignature() !== before, 3000)
    if (!changed) return null
    await sleep(350) // let the list settle before reading the top row
    return rows()[0] || null
  }

  async function openChat(phone) {
    const box = await waitFor(() => firstMatch(SEARCH_BOX), 6000)
    if (!box) return { ok: false, error: 'search box not found (logged out, or still loading)' }

    const before = listSignature()

    // WhatsApp matches against the digits it has stored, which may or may not carry the country
    // code, so try the full number first and then the local 10-digit form.
    const terms = [phone]
    if (phone.length > 10) terms.push(phone.slice(-10))

    for (const term of terms) {
      const row = await resultsFor(box, term, before)
      if (row) {
        clickRow(row)
        await sleep(200)
        try {
          typeInto(box, '')
        } catch {
          // Search box is gone once the chat opens on some builds; nothing to clean up.
        }
        return { ok: true }
      }
    }

    typeInto(box, '')
    return { ok: false, error: 'no chat matched that number' }
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type !== CHAT_OPEN || !message.phone) return

    openChat(String(message.phone))
      .then(sendResponse)
      .catch((e) => sendResponse({ ok: false, error: String(e) }))

    return true
  })
}
