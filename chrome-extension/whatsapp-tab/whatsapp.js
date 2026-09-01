// Runs inside web.whatsapp.com. Opens the chat for a phone number through WhatsApp's own UI and
// drops the bill PDF into its attachment preview, so the tab never reloads and the operator never
// drags a file. Navigating to /send?phone=... would also open the chat, but it reboots the whole
// WhatsApp Web app and loses whatever was on screen.
//
// The one route, in order: New chat -> type the number -> click the first result row -> type the
// bill's message -> Attach -> Document -> hand WhatsApp the PDF. Any step that finds nothing stops
// the run there; there is no second route and, with ALLOW_RELOAD_FALLBACK off, no reload either.
//
// Injected both declaratively and, for tabs already open when the extension loaded, on demand by
// the service worker. The guard below keeps a second injection harmless.
//
// Every step logs under [sspl-wa] in this tab's console. WhatsApp ships obfuscated markup that
// changes without notice, so those lines are what identify a step that stopped working.

if (!window.__ssplWhatsAppChatOpener) {
  window.__ssplWhatsAppChatOpener = true

  const CHAT_OPEN = 'SSPL_WA_OPEN_CHAT'
  const ATTACH_NOW = 'SSPL_WA_ATTACH_NOW'
  const TYPE_FOR_ME = 'SSPL_WA_TYPE'
  const PENDING = 'SSPL_WA_PENDING'
  const log = (...args) => console.log('[sspl-wa]', ...args)

  // Only structural/ARIA hooks: WhatsApp's class names are obfuscated and rotate every build.
  const NEW_CHAT_BUTTON = [
    'button[aria-label*="New chat" i]',
    '[role="button"][aria-label*="New chat" i]',
    'div[title*="New chat" i]',
    'span[data-icon="new-chat-outline"]',
    'span[data-icon="chat"]',
  ]
  // Anything that can hold typed text. Deliberately wide: WhatsApp's search was a contenteditable
  // for years and is a real <input> on current builds, and matching only the old shape is what
  // left "New chat panel did not show a search box" in the log with the panel plainly open.
  const TEXT_ENTRY = [
    'input:not([type="hidden"]):not([type="file"]):not([type="checkbox"]):not([type="radio"]):not([type="submit"])',
    'textarea',
    '[contenteditable="true"]',
    '[role="textbox"]',
  ].join(', ')

  // Ranked, not required — the first entry that actually takes the number wins. A box naming the
  // search is tried before an unlabelled one, and that is the whole of the preference.
  const SEARCH_HINTS = /name or number|search|to:/i
  const RESULT_ROW = ['[role="listitem"]', '[role="row"]', '[role="gridcell"]']

  // Hidden file inputs behind WhatsApp's attachment menu. Setting one is far more reliable than a
  // synthetic drop, which is kept as the fallback.
  const FILE_INPUT = [
    'input[type="file"][accept*="pdf" i]',
    'input[type="file"][accept*="*/*"]',
    'input[type="file"]:not([accept*="image" i]):not([accept*="video" i])',
    'input[type="file"]',
  ]
  const ATTACH_BUTTON = [
    'button[aria-label*="Attach" i]',
    '[role="button"][aria-label*="Attach" i]',
    'span[data-icon="plus-rounded"]',
    'span[data-icon="clip"]',
    'span[data-icon="attach-menu-plus"]',
  ]
  // Items inside the attachment menu. It renders as a list of buttons whose only stable marker is
  // the visible word, so the Document entry is found by text and clicked on its interactive parent.
  const MENU_ITEM = '[role="menuitem"], [role="button"], li, button'
  const DOCUMENT_LABEL = /^document(s)?$/i
  const CHAT_PANE = ['#main', '[data-tab="10"]', 'footer']
  const CAPTION_HINTS = /caption|message/i
  // The composer at the bottom of the open chat, told apart from the search boxes by its own label.
  const COMPOSER_HINTS = /type a message|message|caption/i

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

  // Enough of an element to identify it in a bug report without dumping WhatsApp's markup.
  function describe(el) {
    if (!el) return 'none'
    const attrs = ['aria-label', 'data-tab', 'role', 'contenteditable', 'type', 'placeholder']
      .map((name) => (el.hasAttribute(name) ? `${name}="${el.getAttribute(name)}"` : ''))
      .filter(Boolean)
      .join(' ')
    return `<${el.tagName.toLowerCase()} ${attrs}>`
  }
  const digitsOf = (text) => (text || '').replace(/\D/g, '')

  function firstMatch(selectors, root = document) {
    for (const selector of selectors) {
      const el = root.querySelector(selector)
      if (el) return { el, selector }
    }
    return null
  }

  function rows(root = document) {
    for (const selector of RESULT_ROW) {
      const found = root.querySelectorAll(selector)
      if (found.length) return [...found]
    }
    return []
  }

  // What the list is showing right now, used to tell when it has stopped re-rendering.
  const listSignature = (root) =>
    rows(root)
      .slice(0, 3)
      .map((row) => row.textContent)
      .join('|')

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

  function clickEl(el) {
    for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }))
    }
  }

  // Rows and buttons need the click on the interactive ancestor, which is rarely the element the
  // selector matched. Never use this on a text box: the New chat search sits inside the panel's
  // list container, so the climb lands on a row and the box never gets focus.
  function press(el) {
    clickEl(el.closest('button, [role="button"], div[title], [role="listitem"], [role="row"]') || el)
  }

  const holdsFocus = (box) => document.activeElement === box || box.contains(document.activeElement)

  function focusBox(box) {
    box.focus()
    if (holdsFocus(box)) return true
    // Some builds only wire the box up once it has been clicked. Clicked exactly, not via press:
    // the box's ancestors include list rows, and clicking one of those dismisses the panel.
    clickEl(box)
    box.focus()
    return holdsFocus(box)
  }

  function clearBox(box) {
    if (box.value !== undefined) {
      setNativeValue(box, '')
      return
    }
    document.execCommand('selectAll', false, null)
    document.execCommand('delete', false, null)
  }

  // React tracks an input's value on the DOM node and ignores a plain `.value = x` as a no-op,
  // so the write has to go through the prototype's own setter before the event is fired.
  function setNativeValue(input, text) {
    const proto = input instanceof HTMLTextAreaElement ? HTMLTextAreaElement : HTMLInputElement
    Object.getOwnPropertyDescriptor(proto.prototype, 'value').set.call(input, text)
    input.dispatchEvent(new Event('input', { bubbles: true }))
  }

  // Every way a React field is known to accept text, tried in turn. WhatsApp's search box is a
  // contenteditable on some builds and a real input on others, and the build that refuses
  // execCommand still honours a paste.
  const TYPING_STRATEGIES = [
    ['native value setter', (box, text) => box.value !== undefined && setNativeValue(box, text)],
    ['execCommand', (box, text) => document.execCommand('insertText', false, text)],
    [
      'paste event',
      (box, text) => {
        const data = new DataTransfer()
        data.setData('text/plain', text)
        box.dispatchEvent(
          new ClipboardEvent('paste', { bubbles: true, cancelable: true, clipboardData: data }),
        )
      },
    ],
    [
      'beforeinput + text node',
      (box, text) => {
        box.dispatchEvent(
          new InputEvent('beforeinput', {
            inputType: 'insertText',
            data: text,
            bubbles: true,
            cancelable: true,
          }),
        )
        box.textContent = text
        box.dispatchEvent(new InputEvent('input', { inputType: 'insertText', data: text, bubbles: true }))
      },
    ],
  ]

  const took = (box, text) => digitsOf(boxText(box)).includes(digitsOf(text))

  async function typeInto(box, text) {
    if (!focusBox(box)) {
      log('box will not take focus:', describe(box))
      return false
    }

    clearBox(box)
    if (!text) return true

    for (const [name, apply] of TYPING_STRATEGIES) {
      try {
        apply(box, text)
      } catch (e) {
        log(`typing via ${name} threw:`, e)
        continue
      }
      if (took(box, text)) {
        log('typed via', name)
        return true
      }
      clearBox(box)
    }

    // Everything above is a synthetic event, which a build can ignore. This one is not: the
    // service worker attaches the debugger and has Chrome itself type into whatever has focus,
    // exactly as a keyboard would. Costs a "Chrome is being debugged" banner for a moment.
    focusBox(box)
    try {
      const typed = await chrome.runtime.sendMessage({ type: TYPE_FOR_ME, text })
      if (typed?.ok && took(box, text)) {
        log('typed via Chrome input (debugger)')
        return true
      }
      log('Chrome input did not land:', typed?.error || 'box still empty')
    } catch (e) {
      log('could not ask for Chrome input:', e)
    }

    log('FAIL: nothing could put text in that box —', describe(box))
    return false
  }

  // Waits until the result list stops re-rendering. Comparing against the pre-typing list is not
  // enough: when the party is already the most recent chat, the filtered result looks identical to
  // what was on screen, and calling that "no results" is what sent every share back to reloading.
  async function settledRows(root, maxMs = 4000, minMs = 700) {
    const start = Date.now()
    let previous = null
    let stable = 0
    for (;;) {
      const signature = listSignature(root)
      stable = signature === previous ? stable + 1 : 0
      previous = signature
      const elapsed = Date.now() - start
      if (elapsed >= maxMs || (stable >= 2 && elapsed >= minMs)) break
      await sleep(120)
    }
    return clickableRows(root)
  }

  // A row showing the number is proof of who it is. Otherwise the first row of a search for that
  // number is what the operator would click by hand — taken, but reported as unconfirmed.
  function pickRow(found, phone) {
    const tail = phone.slice(-10)
    const carrying = found.find((row) => digitsOf(row.textContent).includes(tail))
    if (carrying) return { row: carrying, confident: true, why: 'row carries the number' }
    if (found.length) return { row: found[0], confident: false, why: 'first result, number not shown' }
    return { row: null, confident: false, why: 'no rows' }
  }

  // Visible only: WhatsApp keeps offscreen inputs around, and typing into one looks like success
  // while nothing filters.
  function textEntries(root = document) {
    return [...root.querySelectorAll(TEXT_ENTRY)].filter((el) => {
      const box = el.getBoundingClientRect()
      return box.width > 0 && box.height > 0
    })
  }

  // Boxes that name themselves a search go first; everything else keeps document order.
  function rank(entries) {
    const label = (el) =>
      `${el.getAttribute('aria-label') || ''} ${el.getAttribute('placeholder') || ''} ${el.getAttribute('title') || ''}`
    return [...entries].sort((a, b) => Number(SEARCH_HINTS.test(label(b))) - Number(SEARCH_HINTS.test(label(a))))
  }

  const dumpEntries = () => textEntries().map(describe).join(' ') || '(none on screen)'

  const chatIsOpen = () => !!firstMatch(CHAT_PANE)

  // Which chat is on screen. Only #main's own header counts: falling back to any <header> matched
  // the left nav bar, whose text never changes, so every click looked like it had moved nothing.
  function openChatId() {
    const main = document.querySelector('#main, [data-tab="10"]')
    if (!main) return ''
    const title = main.querySelector('header span[title], header span[dir="auto"]')
    return (title?.getAttribute('title') || title?.textContent || main.textContent || '').slice(0, 120)
  }

  // The results belong to the panel that owns the search box, so the scope is found by climbing
  // from the box to the SMALLEST ancestor that contains rows. Matching a container by selector
  // instead is what returned the background chat list — 74 rows, and a click on the open chat.
  function scopeAround(box) {
    for (let node = box.parentElement; node && node !== document.body; node = node.parentElement) {
      if (rows(node).length) return node
    }
    return null
  }

  // Search results are grouped under headings, and those are rows in their own right. Clicking one
  // does nothing, which is exactly how a share ends up looking like it worked.
  const SECTION_HEADING =
    /^(chats|contacts|messages|groups|status|recent|frequently contacted|other contacts|not a contact)$/i

  const clickableRows = (root) =>
    rows(root).filter((row) => {
      const text = row.textContent.trim()
      return text && !SECTION_HEADING.test(text)
    })

  // Closes the New chat panel so a failed attempt does not leave it covering the chat list.
  function escape() {
    for (const type of ['keydown', 'keyup']) {
      document.activeElement?.dispatchEvent(
        new KeyboardEvent(type, { key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true }),
      )
    }
  }

  // ── route 1: New chat ────────────────────────────────────────────────────────────────────────
  // The number does not have to be a saved contact here, which is why this is tried first.
  async function openViaNewChat(phone) {
    const button = firstMatch(NEW_CHAT_BUTTON)
    if (!button) {
      log('no New chat button found')
      return null
    }

    // The panel's search box is a brand new element, which is how it is told apart from the
    // sidebar search that is already on screen.
    const existing = new Set(document.querySelectorAll(TEXT_ENTRY))
    log('clicking New chat via', button.selector)
    press(button.el)

    // Every text entry the panel added is a candidate: which one takes the number differs by
    // build, and picking the first one that merely exists is what left the field empty.
    let candidates = await waitFor(() => {
      const fresh = textEntries().filter((el) => !existing.has(el))
      return fresh.length ? rank(fresh) : null
    }, 5000)

    // Some builds reuse the sidebar's own box for the panel, so nothing is new. Fall back to
    // whatever is on screen rather than declaring the panel empty.
    if (!candidates) {
      candidates = rank(textEntries())
      log('no new text entry appeared; falling back to all', candidates.length, 'on screen')
    }

    if (!candidates.length) {
      log('New chat panel shows no text entry at all:', dumpEntries())
      escape()
      return null
    }
    log('New chat candidates:', candidates.map((el) => describe(el)).join(' '))

    let box = null
    for (const candidate of candidates) {
      if (await typeInto(candidate, phone)) {
        box = candidate
        break
      }
    }
    if (!box) {
      log('FAIL: none of the New chat entries accepted the number')
      escape()
      return null
    }
    log('number went into', describe(box))

    return await clickResultFor(box, phone, 'New chat')
  }

  // Shared by both routes: read the panel's own results, refuse anything that is plainly not a
  // filtered list, click, and then prove the chat actually changed.
  async function clickResultFor(box, phone, route) {
    const before = openChatId()
    const tail = phone.slice(-10)

    // A row displaying the number is unambiguous no matter which list it sits in, so it is worth
    // waiting for one before falling back to reading a panel and trusting its top row.
    const carrying = await waitFor(
      () => clickableRows(document).find((row) => digitsOf(row.textContent).includes(tail)),
      4000,
    )

    let row = carrying
    let confident = !!carrying
    let why = 'row carries the number'

    if (!row) {
      const scope = scopeAround(box)
      if (!scope) {
        log(`${route}: the box's panel has no result rows at all`)
        escape()
        return null
      }

      const found = await settledRows(scope)
      const picked = pickRow(found, phone)
      row = picked.row
      confident = picked.confident
      why = picked.why
      log(`${route} "${phone}": ${found.length} rows in ${describe(scope)}, ${why}`)
      if (found[0]) log('  top row:', found[0].textContent.slice(0, 80))
    } else {
      log(`${route} "${phone}": ${why} — ${row.textContent.trim().slice(0, 60)}`)
    }

    if (!row) {
      escape()
      return null
    }

    press(row)

    // Clicking the row that is already open changes nothing, and attaching then would put the
    // bill in whatever chat happened to be on screen. Require the chat to actually move — or the
    // search panel to close around us, which is WhatsApp acting on the click either way.
    const moved = await waitFor(
      () => chatIsOpen() && (openChatId() !== before || !document.contains(box)),
      5000,
    )
    if (!moved) {
      log(`FAIL: clicked the result but the open chat did not change (still "${before.slice(0, 40)}")`)
      return null
    }

    log(`OK: chat opened via ${route} (${why}) — now "${openChatId().slice(0, 40)}"`)
    return { ok: true, confident }
  }

  async function openChat(phone) {
    // On a cold load nothing is rendered yet; the service worker may ask before WhatsApp is up.
    await waitFor(() => firstMatch(NEW_CHAT_BUTTON) || textEntries().length, 15000)

    const opened = await openViaNewChat(phone)
    if (opened) return opened

    log('FAIL: New chat did not open a chat for that number; stopping here')
    return { ok: false, error: 'New chat found no result row for that number' }
  }

  // ── attaching the bill ───────────────────────────────────────────────────────────────────────
  // The worker parks the PDF in chrome.storage before the chat is ready and this side collects it.
  // That indirection is what lets the bill survive the navigation fallback, which reloads this page
  // and can have the service worker evicted mid-flight.

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

  // Visible menu entry whose own text is the word asked for.
  function menuItemNamed(label) {
    return [...document.querySelectorAll(MENU_ITEM)].find((el) => {
      const box = el.getBoundingClientRect()
      if (!box.width || !box.height) return false
      // Both read: an entry labelled anything else would otherwise never have its text tested.
      return label.test((el.getAttribute('aria-label') || '').trim()) ||
        label.test((el.textContent || '').trim())
    })
  }

  // Attach, then Document, then the input that entry owns. WhatsApp keeps hidden file inputs
  // mounted all the time, so reading one straight off the document would skip the menu the
  // operator was asked to see opened — the menu is walked first, and the global list is the
  // fallback for a build whose Document entry holds no input of its own.
  async function findFileInput() {
    const opener = firstMatch(ATTACH_BUTTON)
    if (!opener) {
      log('no Attach button found; taking any file input on the page')
      return firstMatch(FILE_INPUT)
    }

    log('clicking Attach via', opener.selector)
    press(opener.el)

    const item = await waitFor(() => menuItemNamed(DOCUMENT_LABEL), 4000)
    if (!item) {
      log('attachment menu never showed a Document entry')
    } else {
      log('clicking Document —', describe(item))
      press(item)
      const owned = item.querySelector('input[type="file"]') ||
        item.closest('li, [role="menuitem"]')?.querySelector('input[type="file"]')
      if (owned) return { el: owned, selector: "Document entry's own input[type=file]" }
    }

    return await waitFor(() => firstMatch(FILE_INPUT), 3000)
  }

  async function attach(attachment) {
    // Chat pane first: after the navigation fallback this runs while WhatsApp is still booting.
    const pane = await waitFor(() => firstMatch(CHAT_PANE), 20000)
    if (!pane) {
      log('FAIL: chat pane never appeared, nothing to attach to')
      return false
    }

    // The chat pane exists before the newly opened chat has finished rendering; attaching into
    // the half-swapped view is how a bill can end up looking like it went somewhere else.
    await sleep(400)

    // The message goes into the open chat's composer first, as asked. WhatsApp's preview screen
    // owns its own caption box and discards whatever the composer held, so the same text is
    // written again into the preview below — that second write is the one that survives to send.
    if (attachment.caption) {
      const composer = rank(textEntries(document.querySelector('footer') || document)).filter((el) =>
        COMPOSER_HINTS.test(
          `${el.getAttribute('aria-label') || ''} ${el.getAttribute('placeholder') || ''}`,
        ),
      )[0]
      if (composer) await typeInto(composer, attachment.caption)
      else log('composer box not found:', dumpEntries())
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

    // The preview screen owns its caption box and discards whatever the composer held, so the
    // bill's text has to be written there rather than passed as &text= in the URL.
    if (attachment.caption) {
      // Same shape problem as the search box: this is a contenteditable on older builds and an
      // input on current ones, so it is found by label rather than by tag.
      const box = await waitFor(() => {
        const labelled = textEntries().filter((el) =>
          CAPTION_HINTS.test(
            `${el.getAttribute('aria-label') || ''} ${el.getAttribute('placeholder') || ''}`,
          ),
        )
        return labelled[0] || null
      }, 8000)
      if (box) await typeInto(box, attachment.caption)
      else log('preview caption box not found:', dumpEntries())
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
      return false
    }
    if (!attachment) return false
    log('bill waiting:', attachment.name)
    return await attach(attachment)
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === ATTACH_NOW) {
      attachPending().then((ok) => sendResponse({ ok }))
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

  // Hand inspection without a debugger: run __ssplWaDump() in this tab's console after opening the
  // New chat panel and paste what it prints. It names every text entry and result row on screen,
  // which is what a WhatsApp redesign changes.
  window.__ssplWaDump = () => {
    const entries = [...document.querySelectorAll(TEXT_ENTRY)]
    console.log('[sspl-wa] text entries:', entries.length)
    entries.forEach((el, i) => console.log(`  [${i}]`, describe(el), '| focusable:', el.isContentEditable || el.tagName === 'INPUT'))
    const found = rows()
    console.log('[sspl-wa] result rows:', found.length)
    found.slice(0, 5).forEach((row, i) => console.log(`  [${i}]`, row.textContent.slice(0, 60)))
    console.log('[sspl-wa] new chat button:', describe(firstMatch(NEW_CHAT_BUTTON)?.el))
    console.log('[sspl-wa] chat pane open:', chatIsOpen())
    return entries
  }

  log('chat opener ready on', location.href, '— run __ssplWaDump() to inspect the panel')

  // Covers the navigation fallback: this script is fresh and the bill is already parked.
  attachPending()
}
