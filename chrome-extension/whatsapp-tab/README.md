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

## How the chat is switched without a reload

Pointing the tab at `https://web.whatsapp.com/send?phone=…` opens the right chat but reboots the
whole WhatsApp Web app every time. Instead `whatsapp.js` runs inside the WhatsApp tab and drives
WhatsApp's own UI:

1. Focus the search box (`div[contenteditable="true"][data-tab="3"]`).
2. Type the number with `document.execCommand('insertText', …)` — the only way React sees a real
   `input` event in a contenteditable.
3. Wait for the list to stop re-rendering, then pick a row we can vouch for: one whose visible
   digits contain the last 10 of the number, or — failing that — the only row left after filtering.
   Any other outcome counts as no match, because opening the wrong chat is worse than a reload.
4. If the full number finds nothing, retry with the last 10 digits — WhatsApp may have stored the
   contact without the country code.

The service worker remembers `tabId → phone` for chats it opened by search, so sending a second bill
to the same party does not even search: it just focuses the tab. That memory is dropped whenever the
tab is merely focused or navigated, since neither proves which chat ended up on screen.

**Fallbacks.** If the search box never appears (tab logged out or still loading), or no chat matches
the number, the worker falls back to navigating the tab — that reloads WhatsApp, but the chat does
open. So a future WhatsApp UI change degrades to the old behavior instead of breaking the button.

The selectors are structural and ARIA-based because WhatsApp's class names are obfuscated and change
constantly. If a WhatsApp update makes every share reload again, `SEARCH_BOX` and `RESULT_ROW` at the
top of `whatsapp.js` are the two lists to re-check.

**Check the chat before you send.** The extension clicks the top search result; the operator still
drags the PDF in and presses send by hand, so glance at the contact name in the header first.

## Attaching the bill

The share also hands the PDF to the WhatsApp tab, so the operator does not drag anything:

1. The billing page fetches the bill, saves it to Downloads as before, and passes the bytes to the
   extension as base64 (chrome messaging is JSON — an ArrayBuffer arrives as `{}`).
2. The service worker parks it in `chrome.storage.local` under `attach:<tabId>` before touching the
   tab. That is deliberate: the navigation fallback reloads the page and the worker can be evicted
   while the load runs, so the bill has to outlive both.
3. `whatsapp.js` collects it — on an `SSPL_WA_ATTACH_NOW` message, and again on every load, which is
   what covers the reload path — waits up to 20s for the chat pane, then sets WhatsApp's own hidden
   `input[type="file"]` through a `DataTransfer` and fires `change`. A synthetic drop on the chat
   pane is the fallback.
4. WhatsApp's preview screen discards whatever was in the composer, so the bill's caption is typed
   into the preview's own caption box rather than passed as `&text=` in the URL.

**Nothing is ever sent automatically.** The operator sees the preview with the file and caption and
presses send.

**The bill is only attached when the chat is certain.** A chat found by search counts only if the
clicked row carried the number; a row accepted merely because it was the only result opens the chat
but is not trusted with a bill, and the share falls through to the reload path, where WhatsApp itself
resolves `?phone=`. A stashed bill also expires after two minutes, so an abandoned share cannot
surface in a later chat.
