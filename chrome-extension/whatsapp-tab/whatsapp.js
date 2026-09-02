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
  // The preview's own box says "caption" on current builds; older ones label it like the composer,
  // hence the second word — but a box matching only that is taken solely from inside the preview.
  const CAPTION_HINTS = /caption|message/i
  const CAPTION_ONLY = /caption/i
  // The attachment preview is a modal over the chat. Its box has to be told apart from the chat's
  // own composer, which also answers to "Type a message" — writing there sends a plain text message
  // beside the bill instead of captioning it.
  const PREVIEW_SCOPE = '[data-animate-modal-body], [role="dialog"], [data-animate-drawer-body]'
  // How long the attachment preview is given to appear. Generous: WhatsApp encrypts and uploads
  // the file before showing it, so a big bill on a slow uplink is the case this has to cover.
  const CAPTION_WAIT_MS = 30000

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

  // Stage timings, so a share that feels slow says which step ate the seconds rather than leaving
  // it a guess between our polling and WhatsApp's own search round trip.
  function stopwatch() {
    let mark = performance.now()
    return (label) => {
      const ms = Math.round(performance.now() - mark)
      mark = performance.now()
      log(`${label} took ${ms}ms`)
      return ms
    }
  }

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

  async function waitFor(check, timeoutMs, stepMs = 60) {
    const deadline = Date.now() + timeoutMs
    for (;;) {
      const value = check()
      if (value) return value
      if (Date.now() > deadline) return null
      await sleep(stepMs)
    }
  }

  function clickEl(el, point) {
    const at = point || { clientX: 0, clientY: 0 }
    for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      el.dispatchEvent(
        new MouseEvent(type, {
          bubbles: true,
          cancelable: true,
          view: window,
          button: 0,
          buttons: type === 'pointerdown' || type === 'mousedown' ? 1 : 0,
          ...at,
        }),
      )
    }
  }

  // Clicks a result row the way the mouse would: at the row's own centre, on whatever element is
  // actually painted there. Dispatching on the row itself is not equivalent — React resolves a
  // handler from the event's target, so an event fired on the row never reaches the handler that
  // WhatsApp bound to the element inside it, which is why a click on a saved contact's row looked
  // like it did nothing at all.
  function clickRow(row) {
    row.scrollIntoView({ block: 'nearest' })
    const rect = row.getBoundingClientRect()
    const point = {
      clientX: Math.round(rect.left + rect.width / 2),
      clientY: Math.round(rect.top + rect.height / 2),
    }
    const painted = document.elementFromPoint(point.clientX, point.clientY)
    const target = row.contains(painted) ? painted : row
    log('clicking row at its centre —', describe(target))
    clickEl(target, point)
    return target
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

  // Must leave the box empty, not merely try to. A contenteditable that has lost the selection
  // ignores execCommand and keeps its text, and the next typing strategy then appends to it —
  // which is how one caption ended up in the box four times over.
  function clearBox(box) {
    if (box.value !== undefined) {
      setNativeValue(box, '')
      return boxText(box) === ''
    }

    focusBox(box)
    document.execCommand('selectAll', false, null)
    document.execCommand('delete', false, null)
    if (!boxText(box).trim()) return true

    // Nothing took: wipe the node itself and tell the editor its content changed.
    box.textContent = ''
    box.dispatchEvent(new InputEvent('input', { inputType: 'deleteContentBackward', bubbles: true }))
    return !boxText(box).trim()
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

  const occurrences = (haystack, needle) => (needle ? haystack.split(needle).length - 1 : 0)

  // The text has to be in the box exactly once. `includes` alone called a doubled insert a
  // success, and reading straight after the keystroke called a working insert a failure — React
  // and WhatsApp's editor both commit on a later tick — so this waits for the box to settle.
  async function took(box, text) {
    const wanted = digitsOf(text)
    const seen = await waitFor(() => {
      const count = wanted
        ? occurrences(digitsOf(boxText(box)), wanted)
        : Number(boxText(box).includes(text))
      return count > 0 ? count : null
    }, 700, 50)
    if (!seen) return false
    if (seen > 1) {
      log(`text landed ${seen} times over; clearing and retrying`)
      return false
    }
    return true
  }

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
      if (await took(box, text)) {
        log('typed via', name)
        return true
      }
      if (!clearBox(box)) log(`could not empty the box after ${name}; text may stack`)
    }

    // Everything above is a synthetic event, which a build can ignore. This one is not: the
    // service worker attaches the debugger and has Chrome itself type into whatever has focus,
    // exactly as a keyboard would. Costs a "Chrome is being debugged" banner for a moment.
    focusBox(box)
    try {
      const typed = await chrome.runtime.sendMessage({ type: TYPE_FOR_ME, text })
      if (typed?.ok && (await took(box, text))) {
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
  async function settledRows(root, maxMs = 2500, minMs = 350) {
    const start = Date.now()
    let previous = null
    let stable = 0
    for (;;) {
      const signature = listSignature(root)
      stable = signature === previous ? stable + 1 : 0
      previous = signature
      const elapsed = Date.now() - start
      if (elapsed >= maxMs || (stable >= 2 && elapsed >= minMs)) break
      await sleep(80)
    }
    return clickableRows(root)
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

  // What is typed into the search: the country code is dropped, since WhatsApp stores Indian
  // contacts as the bare 10 digits and searching the 91-prefixed form can miss them. Matching a
  // result row still uses the last 10 digits, so it is the same number either way.
  const searchTerm = (phone) => {
    const digits = digitsOf(phone)
    return digits.length > 10 ? digits.slice(-10) : digits
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

    const term = searchTerm(phone)
    if (term !== phone) log('searching without the country code:', term)

    let box = null
    for (const candidate of candidates) {
      if (await typeInto(candidate, term)) {
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

  // Reads the panel's own results, clicks the first row whatever it is, and then proves the chat
  // actually changed.
  async function clickResultFor(box, phone, route) {
    const before = openChatId()
    const tail = phone.slice(-10)
    const lap = stopwatch()

    // The first row is taken, saved contact or not — a contact shows a name and never the number,
    // so waiting for the number to appear only costs seconds on every share to a contact. The
    // panel that owns the search box is preferred as the source, since a document-wide read can
    // pick up the background chat list.
    await waitFor(() => clickableRows(scopeAround(box) || document).length, 4000)
    const scope = scopeAround(box) || document
    const found = await settledRows(scope)
    lap('waiting for the result rows')

    const row = found[0]
    if (!row) {
      log(`${route} "${phone}": no result row for that number — stopping here`)
      escape()
      return null
    }

    const confident = digitsOf(row.textContent).includes(tail)
    const why = confident ? 'first row, carries the number' : 'first row, number not shown'
    log(`${route} "${phone}": ${found.length} rows in ${describe(scope)}, ${why}`)
    log('  clicking:', row.textContent.trim().slice(0, 60))

    lap('reading the result list')

    // Clicking the row that is already open changes nothing, and attaching then would put the
    // bill in whatever chat happened to be on screen. Require the chat to actually move — or the
    // search panel to close around us, which is WhatsApp acting on the click either way.
    const opened = () => chatIsOpen() && (openChatId() !== before || !document.contains(box))

    // Three ways of saying "open this row", tried in turn. The first is what a mouse does and
    // normally settles it; the rest cover a row whose handler sits somewhere the centre click
    // does not reach.
    const attempts = [
      ['centre click', () => clickRow(row)],
      ['click on the row itself', () => clickEl(row)],
      [
        'Enter in the search box',
        () => {
          focusBox(box)
          for (const type of ['keydown', 'keypress', 'keyup']) {
            box.dispatchEvent(
              new KeyboardEvent(type, { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }),
            )
          }
        },
      ],
    ]

    let moved = null
    for (const [name, attempt] of attempts) {
      attempt()
      moved = await waitFor(opened, 2500)
      if (moved) {
        if (name !== 'centre click') log('opened by falling back to', name)
        break
      }
      log(`${name} did not move the chat; trying the next way in`)
      if (!document.contains(row)) break
    }
    lap('WhatsApp opening the clicked chat')
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

  // Attach, then Document, then the input that entry owns. Reading a mounted input straight off the
  // document instead is what broke the share: on this build the only one standing is the photos and
  // videos input, and handing it a PDF gets "1 file you tried adding is not supported" back. The
  // document input exists only once Document has been clicked.
  //
  // Chrome refuses to raise the picker the click asks for and logs "File chooser dialog can only be
  // shown with a user activation" — that line is expected and harmless, since the input mounts
  // either way and the file goes in without the picker.
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

  const labelOf = (el) =>
    `${el.getAttribute('aria-label') || ''} ${el.getAttribute('placeholder') || ''} ${el.getAttribute('title') || ''}`

  // The preview's caption box and nothing else: a box inside the preview modal, or one that names
  // itself a caption. There is deliberately no wider fallback — every other text box on screen is
  // the chat composer, and writing the bill line there posts it as a message of its own instead of
  // captioning the file.
  function captionBox() {
    for (const scope of document.querySelectorAll(PREVIEW_SCOPE)) {
      const inside = textEntries(scope).filter((el) => CAPTION_HINTS.test(labelOf(el)))
      if (inside.length) return inside[0]
    }
    return textEntries().find((el) => CAPTION_ONLY.test(labelOf(el))) || null
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
    await sleep(250)

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

    // The message is typed only after the bill is in, and only into the preview's own caption box.
    // Waited for rather than slept on: the preview appears when WhatsApp has finished reading and
    // uploading the file, which is anywhere from under a second to a slow uplink's worth, and a
    // fixed delay is either dead time or too early.
    if (attachment.caption) {
      log('bill handed over; waiting for the preview caption box')
      // Same shape problem as the search box: this is a contenteditable on older builds and an
      // input on current ones, so it is found by label rather than by tag.
      const box = await waitFor(captionBox, CAPTION_WAIT_MS)
      if (!box) {
        log('FAIL: no caption box in the preview; not typing into the chat composer instead')
        log('  boxes on screen:', dumpEntries())
      } else if (boxText(box).trim() === attachment.caption.trim()) {
        // Nothing to do when WhatsApp has already carried the text across by itself; writing it
        // again is what repeated the bill line.
        log('preview already carries the message; leaving it alone')
      } else {
        log('caption box:', describe(box))
        await typeInto(box, attachment.caption)
      }
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
