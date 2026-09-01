# SSPL WhatsApp Tab

Sends a bill from SSPL Billing to the **WhatsApp Web tab that is already open**, instead of
opening a new one every time.

## Why an extension is needed

`web.whatsapp.com` responds with `Cross-Origin-Opener-Policy: same-origin`. That header
severs the opener relationship and clears the window name, so a web page can never
re-target a WhatsApp tab with `window.open(url, 'name')` — not even one it opened itself.
Only an extension holding the `tabs` permission can find that tab and focus it.

Without this extension the billing app still works: it opens/reuses its own tab as before.

## Install (once per till machine, Chrome or Edge)

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked** and pick this folder
   (`apps/ssplbilling/chrome-extension/whatsapp-tab`).
4. Reload the billing tab.

To confirm it is live, run in the billing page's console:

```js
document.documentElement.dataset.ssplWhatsappBridge  // "1" when the bridge is loaded
```

## What it does on a share

1. `chrome.tabs.query` for `*://web.whatsapp.com/*`.
2. A tab already on the right chat is just focused; any other WhatsApp tab is focused and
   navigated to the chat; if no WhatsApp tab exists at all, one is created.
3. The window holding that tab is raised.

## Scope

- Content script runs only on the billing SPA (`*://*/frontend/*` and the Vite dev server
  on `localhost:8080`). It reads nothing from the page — it only listens for the app's own
  `SSPL_WHATSAPP_OPEN` message and relays the chat URL.
- No host permission on the billing site, no page content access on WhatsApp, no network
  calls of its own.

## Which pages the bridge runs on

`manifest.json` → `content_scripts[0].matches` decides where the extension announces itself.
Two rules of Chrome match patterns matter here:

- **Port numbers are not allowed.** `http://localhost:8080/*` is rejected, and a single invalid
  pattern makes Chrome refuse to load the whole extension (`chrome://extensions` shows an
  **Errors** button: `Invalid value for 'content_scripts[0].matches[…]'`). Drop the port —
  `http://localhost/*` already matches every port on that host.
- **Wildcards do not work inside IP addresses.** `http://192.168.*/*` is invalid. Each dev
  machine reached by LAN IP has to be listed in full.

`*://*/frontend/*` covers every production deployment on any host and port, because Frappe serves
the SPA under `/frontend`. The Vite dev server uses base `/`, so dev hosts need their own entry —
add one per machine:

```json
"http://192.168.1.50/*"
```

## After loading or changing the extension

Chrome does not inject a content script into tabs that are already open. Reload the billing tab
(Ctrl+Shift+R) after **Load unpacked** or after **Reload** on the extension card, or the badge in
SSPL Billing Settings stays grey and the WhatsApp button falls back to opening a new tab.

## How the chat is opened without a reload

Pointing the tab at `https://web.whatsapp.com/send?phone=…` opens the right chat but reboots the
whole WhatsApp Web app every time. Instead `whatsapp.js` runs inside the WhatsApp tab and clicks
through WhatsApp's own UI, exactly as an operator would:

1. **New chat**, then type the number, then click the first result row — the only route, because it
   also works for numbers that are not saved as contacts. A step that finds nothing (no New chat
   button, no box that takes the number, no result row) stops the run there; there is no second
   search. The sidebar-search route, and with it the retry on the last 10 digits for contacts stored
   without a country code, was removed.
2. **Navigate** — the last resort, and the only path that reloads. Currently **off**
   (`ALLOW_RELOAD_FALLBACK = false` in `background.js`): a share that cannot open the chat reports
   `not-opened` and leaves the bill in Downloads rather than rebooting WhatsApp Web. Flip the flag
   to bring it back.

Getting text into the search box is the step that breaks most often, because WhatsApp's box is a
contenteditable on some builds and a real `<input>` on others, and React ignores a plain
`.value = x`. Nothing is matched on tag or class, then: any visible element that can hold text
counts as a candidate (`input`, `textarea`, `[contenteditable]`, `[role="textbox"]`), ranked so a
box labelled like a search is tried first. Each candidate is tried in turn, with four strategies — the prototype's native value setter, `execCommand('insertText')`, a synthetic paste,
and `beforeinput` plus a text node — and the field is read back after each to see which one stuck.
The console line `typed via …` names the winner.

Text goes in through `document.execCommand('insertText', …)`, the only way React sees a real `input`
event in a contenteditable, with a synthetic paste as backup. Results are read once the list stops
re-rendering: comparing against the pre-typing list is not enough, because when the party is already
the most recent chat the filtered result looks identical to what was on screen.

The service worker remembers `tabId → phone`, so a second bill to the same party skips the search
entirely and just focuses the tab. That memory is dropped whenever the tab is merely focused or
navigated, since neither proves which chat ended up on screen.

**Check the contact before you send.** A row showing the number is proof of who it is; otherwise the
first search result is taken, the same one the operator would click by hand. The bill is attached but
never sent, so the contact name is on screen in the preview before anything leaves.

The selectors are structural and ARIA-based because WhatsApp's class names are obfuscated and change
constantly. If shares start reloading again, the `[sspl-wa]` console lines name the step that failed,
and `NEW_CHAT_BUTTON`, `TEXT_ENTRY`, `RESULT_ROW`, `ATTACH_BUTTON` and `DOCUMENT_LABEL` at the top of `whatsapp.js` are the lists
to re-check.

## Attaching the bill

The share also hands the PDF to the WhatsApp tab, so the operator does not drag anything:

1. The billing page fetches the bill, saves it to Downloads as before, and passes the bytes to the
   extension as base64 (chrome messaging is JSON — an ArrayBuffer arrives as `{}`).
2. The service worker parks it in `chrome.storage.local` under `attach:<tabId>` before touching the
   tab. That is deliberate: the navigation fallback reloads the page and the worker can be evicted
   while the load runs, so the bill has to outlive both.
3. `whatsapp.js` collects it — on an `SSPL_WA_ATTACH_NOW` message, and again on every load, which is
   what covers the reload path — and waits up to 20s for the chat pane.
4. The bill's message is typed into the open chat's composer.
5. **Attach** is clicked, then **Document** in the menu it opens, and the file input that entry owns
   is set through a `DataTransfer` with a `change` event. WhatsApp keeps hidden file inputs mounted
   at all times, so the menu is always walked rather than reading an input straight off the page;
   the global `FILE_INPUT` list and then a synthetic drop on the chat pane are the fallbacks.
6. Older builds discard whatever was in the composer, so the same text is typed again into the
   preview's own caption box. Current builds carry the composer's text across by themselves, so the
   preview box is read first and left alone when it already holds the message — writing it a second
   time is what repeated the bill line in the caption.

**Nothing is ever sent automatically.** The operator sees the preview with the file and caption and
presses send.

**The first result row is clicked and the bill is attached to it.** A row carrying the number is
preferred, but a row taken merely because it was first is used just the same — the operator confirms
the contact in the preview before sending, since nothing is sent automatically. The click still has
to actually change the open chat, or nothing is attached. A stashed bill expires after two minutes,
so an abandoned share cannot surface in a later chat.

## When the number does not go into the box

The console names the strategy that worked (`typed via …`). If every one fails, the log ends with
`FAIL: nothing could put text in that box` followed by the elements that were tried.

To inspect by hand: open the New chat panel in WhatsApp, then run `__ssplWaDump()` in that tab's
console. It prints every text entry and result row on screen with their ARIA attributes — that is
what a WhatsApp redesign changes, and it is enough to fix the selector lists at the top of
`whatsapp.js` without guessing.

### Why the `debugger` permission

Chrome warns about it at install, and the tab shows a "Chrome is being debugged" banner for a
moment during a share. It is the only way to produce input that a page cannot ignore: every event a
content script fires is synthetic and a build is free to drop it, while `Input.insertText` over the
debugger protocol is handled by Chrome itself and is indistinguishable from a keystroke. It is only
reached after all four in-page strategies have failed, and the debugger is detached immediately.

## Why the results are read from the panel, never by selector

An earlier build matched the result container with a selector list, which happily returned
`#pane-side` — the background chat list. Searching a number then reported 74 rows, "clicked" the
first one, and the bill was attached to whatever chat was already open.

The scope is now found by climbing from the search box to the **smallest** ancestor that contains
rows, so it can only ever be the panel that owns the box. Two checks sit on top of that:

- The chat header is read before and after the click, and the chat only counts as opened if it
  actually changed. Clicking the row for the chat already on screen changes nothing, and attaching
  then would put the bill wherever the operator happened to be.
- The bill is only handed over after that check passes, with a short settle so the newly opened
  chat has finished rendering.

## Picking the right row

Three things make a search result list hard to read:

- **Section headings are rows.** "Chats", "Contacts", "Messages" all match `[role="listitem"]`, and
  clicking one does nothing while looking like a successful click. They are filtered out by name.
- **The panel's top row is not always the party.** Before a search resolves, New chat leads with
  "Message yourself". A row carrying the number is waited for first and wins outright; only when
  none appears is the panel's top row clicked, which is what was asked for — so check the contact in
  the preview before sending.
- **A row showing the number is unambiguous wherever it sits**, so it is looked for across the page
  first, before any attempt to work out which container the results are in.

The click is then confirmed against `#main`'s own header. An earlier build fell back to any
`<header>`, which matched the left nav bar — text that never changes, so every click was reported as
having moved nothing and the whole share failed even when it had worked.
