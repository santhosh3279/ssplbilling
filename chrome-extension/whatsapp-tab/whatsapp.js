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

  // Identifies what the list is currently showing, used to tell when it has stopped re-rendering.
  function listSignature() {
    return rows()
      .slice(0, 3)
      .map((row) => row.textContent)
      .join('|')
  }

  const digitsOf = (text) => (text || '').replace(/\D/g, '')

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
    // selectAll acts on whatever has focus. If the click already moved focus into the chat,
    // clearing here would delete text somewhere else in the page.
    if (document.activeElement !== box) return false
    document.execCommand('selectAll', false, null)
    if (text) document.execCommand('insertText', false, text)
    else document.execCommand('delete', false, null)
    return true
  }

  function clickRow(row) {
    const target = row.querySelector('[role="gridcell"]') || row
    for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      target.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }))
    }
  }

  // Waits until the list stops re-rendering. Comparing against the pre-typing list is not enough:
  // when the party is already the operator's most recent chat, the filtered result looks exactly
  // like what was on screen, and treating that as "no results" would send us back to reloading.
  async function settledRows(maxMs = 3000, minMs = 600) {
    const start = Date.now()
    let previous = null
    let stable = 0
    for (;;) {
      const signature = listSignature()
      stable = signature === previous ? stable + 1 : 0
      previous = signature
      const elapsed = Date.now() - start
      if (elapsed >= maxMs) break
      if (stable >= 2 && elapsed >= minMs) break
      await sleep(120)
    }
    return rows()
  }

  // Only click a row we can vouch for. A row carrying the number is proof; a search that filtered
  // down to a single chat is good enough. Anything else means we do not know which chat is which,
  // and reloading into the right chat beats opening the wrong one.
  function pickRow(found, phone) {
    const tail = phone.slice(-10)
    const corroborated = found.find((row) => digitsOf(row.textContent).includes(tail))
    if (corroborated) return corroborated
    return found.length === 1 ? found[0] : null
  }

  async function resultsFor(box, term, phone) {
    if (!typeInto(box, term)) return null
    return pickRow(await settledRows(), phone)
  }

  async function openChat(phone) {
    const box = await waitFor(() => firstMatch(SEARCH_BOX), 6000)
    if (!box) return { ok: false, error: 'search box not found (logged out, or still loading)' }

    // WhatsApp matches against the digits it has stored, which may or may not carry the country
    // code, so try the full number first and then the local 10-digit form.
    const terms = [phone]
    if (phone.length > 10) terms.push(phone.slice(-10))

    for (const term of terms) {
      const row = await resultsFor(box, term, phone)
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
    return { ok: false, error: 'no chat could be matched to that number with confidence' }
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type !== CHAT_OPEN || !message.phone) return

    openChat(String(message.phone))
      .then(sendResponse)
      .catch((e) => sendResponse({ ok: false, error: String(e) }))

    return true
  })
}
