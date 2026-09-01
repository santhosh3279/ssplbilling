// Runs inside web.whatsapp.com. Opens the chat for a phone number by driving WhatsApp's own
// search box, so the tab never reloads. Navigating the tab to /send?phone=... would work too,
// but that reboots the whole WhatsApp Web app and loses whatever the operator was doing.
//
// Injected both declaratively and, for tabs that were already open when the extension loaded,
// on demand by the service worker. The guard below keeps a second injection harmless.
//
// Every step logs to this tab's console under [sspl-wa]. WhatsApp ships obfuscated markup that
// changes without notice, so when the share starts reloading again those lines say which step
// stopped working.

if (!window.__ssplWhatsAppChatOpener) {
  window.__ssplWhatsAppChatOpener = true

  const CHAT_OPEN = 'SSPL_WA_OPEN_CHAT'
  const log = (...args) => console.log('[sspl-wa]', ...args)

  // Only structural/ARIA hooks: WhatsApp's class names are obfuscated and rotate on every build.
  // Ordered most specific first; the rest are there to survive markup churn.
  const SEARCH_BOX = [
    'div[contenteditable="true"][data-tab="3"]',
    '#side div[contenteditable="true"][role="textbox"]',
    'div[role="textbox"][aria-label*="Search" i]',
    'div[contenteditable="true"][aria-label*="Search" i]',
    '#side input[type="text"]',
    '#side div[contenteditable="true"]',
  ]
  // Clicked when no search box is on screen — newer builds hide it behind a search button.
  const SEARCH_OPENER = [
    'button[aria-label*="Search" i]',
    '[role="button"][aria-label*="Search" i]',
    'span[data-icon="search"]',
  ]
  const RESULT_ROW = [
    '#pane-side [role="listitem"]',
    '#pane-side [role="row"]',
    '[role="grid"] [role="listitem"]',
    '[role="grid"] [role="row"]',
    '[aria-label*="Search results" i] [role="listitem"]',
  ]

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
  const digitsOf = (text) => (text || '').replace(/\D/g, '')

  function firstMatch(selectors) {
    for (const selector of selectors) {
      const el = document.querySelector(selector)
      if (el) return { el, selector }
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

  // Identifies what the list is currently showing, used to tell when it stopped re-rendering.
  function listSignature() {
    return rows()
      .slice(0, 3)
      .map((row) => row.textContent)
      .join('|')
  }

  const boxText = (box) => (box.value !== undefined ? box.value : box.textContent) || ''

  async function waitFor(check, timeoutMs, stepMs = 120) {
    const deadline = Date.now() + timeoutMs
    for (;;) {
      const value = check()
      if (value) return value
      if (Date.now() > deadline) return null
      await sleep(stepMs)
    }
  }

  async function findSearchBox() {
    let hit = firstMatch(SEARCH_BOX)
    if (hit) return hit

    // Nothing on screen: try the search button, then look again.
    const opener = firstMatch(SEARCH_OPENER)
    if (opener) {
      log('no search box yet, clicking', opener.selector)
      opener.el.click()
      hit = await waitFor(() => firstMatch(SEARCH_BOX), 2000)
      if (hit) return hit
    }
    return await waitFor(() => firstMatch(SEARCH_BOX), 5000)
  }

  // React only registers text that arrives with real input events. execCommand produces them;
  // when a build refuses it, a synthetic paste is the other route React honours.
  function typeInto(box, text) {
    box.focus()
    if (document.activeElement !== box) {
      // selectAll acts on whatever has focus, so bail rather than edit some other element.
      log('search box will not take focus; skipping')
      return false
    }

    document.execCommand('selectAll', false, null)
    document.execCommand('delete', false, null)
    if (!text) return true

    document.execCommand('insertText', false, text)
    if (digitsOf(boxText(box)).includes(digitsOf(text))) return true

    log('execCommand did not stick, trying paste')
    const data = new DataTransfer()
    data.setData('text/plain', text)
    box.dispatchEvent(
      new ClipboardEvent('paste', { bubbles: true, cancelable: true, clipboardData: data }),
    )
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
  // like what was on screen, and treating that as "no results" sends us back to reloading.
  async function settledRows(maxMs = 4000, minMs = 700) {
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
  // down to a single chat is good enough. Anything else means we cannot tell the chats apart, and
  // reloading into the right chat beats opening the wrong one.
  function pickRow(found, phone) {
    const tail = phone.slice(-10)
    const corroborated = found.find((row) => digitsOf(row.textContent).includes(tail))
    if (corroborated) return { row: corroborated, why: 'row carries the number' }
    if (found.length === 1) return { row: found[0], why: 'only one result' }
    return { row: null, why: `${found.length} rows, none carrying ${tail}` }
  }

  async function openChat(phone) {
    const hit = await findSearchBox()
    if (!hit) {
      log('FAIL: no search box (logged out, or still loading)')
      return { ok: false, error: 'search box not found (logged out, or still loading)' }
    }
    log('search box:', hit.selector)

    // WhatsApp matches against the digits it has stored, which may or may not carry the country
    // code, so try the full number first and then the local 10-digit form.
    const terms = phone.length > 10 ? [phone, phone.slice(-10)] : [phone]

    for (const term of terms) {
      if (!typeInto(hit.el, term)) {
        return { ok: false, error: 'could not type into the search box' }
      }
      const found = await settledRows()
      const { row, why } = pickRow(found, phone)
      log(`term "${term}": box now "${boxText(hit.el)}", ${found.length} rows, ${why}`)
      if (found[0]) log('  top row:', found[0].textContent.slice(0, 80))

      if (row) {
        clickRow(row)
        await sleep(200)
        typeInto(hit.el, '')
        log('OK: chat opened without reloading')
        return { ok: true }
      }
    }

    typeInto(hit.el, '')
    log('FAIL: no confident match, falling back to a reload')
    return { ok: false, error: 'no chat could be matched to that number with confidence' }
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type !== CHAT_OPEN || !message.phone) return

    log('asked to open', message.phone)
    openChat(String(message.phone))
      .then(sendResponse)
      .catch((e) => {
        log('FAIL: threw', e)
        sendResponse({ ok: false, error: String(e) })
      })

    return true
  })

  log('chat opener ready on', location.href)
}
