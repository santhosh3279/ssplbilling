// Runs inside web.whatsapp.com. Opens the chat for a phone number through WhatsApp's own UI and
// drops the bill PDF into its attachment preview, so the tab never reloads and the operator never
// drags a file. Navigating to /send?phone=... would also open the chat, but it reboots the whole
// WhatsApp Web app and loses whatever was on screen.
//
// Route taken, in order:
//   1. New chat -> type the number -> click the first result. Works for numbers that are not
//      saved as contacts, which is why it comes first.
//   2. The sidebar search, for builds where the New chat panel cannot be found.
//   3. Nothing — the service worker then falls back to navigating, which reloads.
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
  const TEXT_ENTRY = 'div[contenteditable="true"], input[type="text"]'
  const NEW_CHAT_SEARCH = [
    'div[contenteditable="true"][aria-label*="name or number" i]',
    'div[role="textbox"][aria-label*="name or number" i]',
    'input[type="text"][aria-label*="name or number" i]',
    'div[contenteditable="true"][data-tab="3"]',
    'div[contenteditable="true"]',
  ]
  const SIDEBAR_SEARCH = [
    'div[contenteditable="true"][data-tab="3"]',
    '#side div[contenteditable="true"][role="textbox"]',
    'div[role="textbox"][aria-label*="Search" i]',
    '#side div[contenteditable="true"]',
  ]
  const RESULT_ROW = ['[role="listitem"]', '[role="row"]', '[role="gridcell"]']
  const RESULT_SCOPE = ['#pane-side', '[role="grid"]', '[data-animate-modal-body]', '[role="dialog"]']

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
  const CHAT_PANE = ['#main', '[data-tab="10"]', 'footer']
  const CAPTION_BOX = [
    'div[contenteditable="true"][data-tab="10"]',
    'div[contenteditable="true"][aria-label*="caption" i]',
    'div[role="textbox"][aria-label*="caption" i]',
  ]

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
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

  function press(el) {
    const target = el.closest('button, [role="button"], div[title], [role="listitem"], [role="row"]') || el
    for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      target.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }))
    }
  }

  const holdsFocus = (box) => document.activeElement === box || box.contains(document.activeElement)

  function focusBox(box) {
    box.focus()
    if (holdsFocus(box)) return true
    // Some builds only wire the box up once it has been clicked.
    press(box)
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

  function typeInto(box, text) {
    if (!focusBox(box)) {
      log('box will not take focus:', box.tagName, box.getAttribute('aria-label') || '')
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
      if (digitsOf(boxText(box)).includes(digitsOf(text))) {
        log('typed via', name)
        return true
      }
      clearBox(box)
    }

    log('FAIL: nothing could put text in that box')
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
    return rows(root).filter((row) => row.textContent.trim())
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

  const chatIsOpen = () => !!firstMatch(CHAT_PANE)

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
    const candidates = await waitFor(() => {
      const fresh = []
      for (const selector of NEW_CHAT_SEARCH) {
        for (const el of document.querySelectorAll(selector)) {
          if (!existing.has(el) && !fresh.some((c) => c.el === el)) fresh.push({ el, selector })
        }
      }
      return fresh.length ? fresh : null
    }, 5000)

    if (!candidates) {
      log('New chat panel did not show a search box')
      escape()
      return null
    }
    log('New chat text entries:', candidates.map((c) => c.selector).join(' | '))

    const box = candidates.find((candidate) => typeInto(candidate.el, phone))
    if (!box) {
      log('FAIL: none of the New chat entries accepted the number')
      escape()
      return null
    }
    log('number went into', box.selector)

    const scope = box.el.closest(RESULT_SCOPE.join(',')) || document
    const found = await settledRows(scope)
    const { row, confident, why } = pickRow(found, phone)
    log(`New chat "${phone}": ${found.length} rows, ${why}`)
    if (found[0]) log('  top row:', found[0].textContent.slice(0, 80))
    if (!row) {
      escape()
      return null
    }

    press(row)
    const opened = await waitFor(chatIsOpen, 5000)
    if (!opened) {
      log('clicked the result but no chat opened')
      return null
    }
    log(`OK: chat opened via New chat (${why})`)
    return { ok: true, confident }
  }

  // ── route 2: sidebar search ──────────────────────────────────────────────────────────────────
  async function openViaSidebarSearch(phone) {
    const box = firstMatch(SIDEBAR_SEARCH)
    if (!box) {
      log('no sidebar search box either')
      return null
    }

    // WhatsApp matches against the digits it stored, which may or may not carry the country code.
    const terms = phone.length > 10 ? [phone, phone.slice(-10)] : [phone]
    const scope = document.querySelector('#pane-side') || document

    for (const term of terms) {
      if (!typeInto(box.el, term)) return null
      const found = await settledRows(scope)
      const { row, confident, why } = pickRow(found, phone)
      log(`sidebar "${term}": box now "${boxText(box.el)}", ${found.length} rows, ${why}`)
      if (found[0]) log('  top row:', found[0].textContent.slice(0, 80))

      if (row) {
        press(row)
        await sleep(200)
        typeInto(box.el, '')
        if (await waitFor(chatIsOpen, 5000)) {
          log(`OK: chat opened via sidebar search (${why})`)
          return { ok: true, confident }
        }
      }
    }

    typeInto(box.el, '')
    return null
  }

  async function openChat(phone) {
    // On a cold load nothing is rendered yet; the service worker may ask before WhatsApp is up.
    await waitFor(() => firstMatch(NEW_CHAT_BUTTON) || firstMatch(SIDEBAR_SEARCH), 15000)

    const opened = (await openViaNewChat(phone)) || (await openViaSidebarSearch(phone))
    if (opened) return opened

    log('FAIL: could not open the chat in place, falling back to a reload')
    return { ok: false, error: 'New chat and sidebar search both failed to open the chat' }
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

  async function findFileInput() {
    let hit = firstMatch(FILE_INPUT)
    if (hit) return hit

    const opener = firstMatch(ATTACH_BUTTON)
    if (opener) {
      log('no file input yet, clicking', opener.selector)
      press(opener.el)
      hit = await waitFor(() => firstMatch(FILE_INPUT), 3000)
    }
    return hit
  }

  async function attach(attachment) {
    // Chat pane first: after the navigation fallback this runs while WhatsApp is still booting.
    const pane = await waitFor(() => firstMatch(CHAT_PANE), 20000)
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

    // The preview screen owns its caption box and discards whatever the composer held, so the
    // bill's text has to be written there rather than passed as &text= in the URL.
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

  log('chat opener ready on', location.href)

  // Covers the navigation fallback: this script is fresh and the bill is already parked.
  attachPending()
}
