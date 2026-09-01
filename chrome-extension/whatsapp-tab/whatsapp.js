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
  const ATTACH_NOW = 'SSPL_WA_ATTACH_NOW'
  const PENDING = 'SSPL_WA_PENDING'
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
  // WhatsApp keeps hidden file inputs for its attachment menu. Setting one of them is far more
  // reliable than a synthetic drop, which is kept as the fallback.
  const FILE_INPUT = [
    'input[type="file"][accept*="pdf" i]',
    'input[type="file"][accept*="*/*"]',
    'input[type="file"]:not([accept*="image" i]):not([accept*="video" i])',
    'input[type="file"]',
  ]
  // Clicked when no usable input exists yet: the menu renders its inputs on demand.
  const ATTACH_BUTTON = [
    'button[aria-label*="Attach" i]',
    '[role="button"][aria-label*="Attach" i]',
    'span[data-icon="plus-rounded"]',
    'span[data-icon="clip"]',
    'span[data-icon="attach-menu-plus"]',
  ]
  // The chat pane, used as the drop target by the fallback.
  const DROP_TARGET = ['#main', '[data-tab="10"]', 'footer']
  // Caption box on WhatsApp's file preview screen.
  const CAPTION_BOX = [
    'div[contenteditable="true"][data-tab="10"]',
    'div[contenteditable="true"][aria-label*="caption" i]',
    'div[role="textbox"][aria-label*="caption" i]',
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
        const confident = why === 'row carries the number'
        log(`OK: chat opened without reloading (${why})`)
        return { ok: true, confident }
      }
    }

    typeInto(hit.el, '')
    log('FAIL: no confident match, falling back to a reload')
    return { ok: false, error: 'no chat could be matched to that number with confidence' }
  }

  // ── attaching the bill ─────────────────────────────────────────────────────────────────────
  // The worker parks the PDF in chrome.storage before the chat is ready, and this side collects
  // it. That indirection is what lets the bill survive the navigation fallback, which reloads
  // this page and can have the service worker evicted mid-flight.

  function fileFrom(attachment) {
    const binary = atob(attachment.data)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
    return new File([bytes], attachment.name, { type: attachment.type || 'application/pdf' })
  }

  function transferOf(file) {
    const data = new DataTransfer()
    data.items.add(file)
    return data
  }

  async function findFileInput() {
    let hit = firstMatch(FILE_INPUT)
    if (hit) return hit

    const opener = firstMatch(ATTACH_BUTTON)
    if (opener) {
      log('no file input yet, clicking', opener.selector)
      ;(opener.el.closest('button,[role="button"]') || opener.el).click()
      hit = await waitFor(() => firstMatch(FILE_INPUT), 3000)
    }
    return hit
  }

  async function attach(attachment) {
    // Composer first: on the navigation fallback this runs while WhatsApp is still booting.
    const pane = await waitFor(() => firstMatch(DROP_TARGET), 20000)
    if (!pane) {
      log('FAIL: chat pane never appeared, nothing to attach to')
      return false
    }

    const file = fileFrom(attachment)
    const input = await findFileInput()

    if (input) {
      input.el.files = transferOf(file).files
      input.el.dispatchEvent(new Event('change', { bubbles: true }))
      log('attached via', input.selector)
    } else {
      log('no file input found, dropping onto', pane.selector)
      for (const type of ['dragenter', 'dragover', 'drop']) {
        pane.el.dispatchEvent(
          new DragEvent(type, { bubbles: true, cancelable: true, dataTransfer: transferOf(file) }),
        )
      }
    }

    // The preview screen owns its own caption box, and whatever was typed in the composer is
    // dropped when it opens — so the bill's text has to be written here instead.
    if (attachment.caption) {
      const box = await waitFor(() => firstMatch(CAPTION_BOX), 8000)
      if (box) typeInto(box.el, attachment.caption)
      else log('preview caption box not found; sending without a caption')
    }

    log('OK: bill attached — operator still presses send')
    return true
  }

  async function attachPending() {
    let attachment = null
    try {
      attachment = await chrome.runtime.sendMessage({ type: PENDING })
    } catch (e) {
      log('could not ask for a pending bill:', e)
      return
    }
    if (!attachment) return
    log('bill waiting:', attachment.name)
    await attach(attachment)
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === ATTACH_NOW) {
      attachPending().then(() => sendResponse({ ok: true }))
      return true
    }

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

  // Covers the navigation fallback: this script is fresh, and the bill is already parked.
  attachPending()
}
