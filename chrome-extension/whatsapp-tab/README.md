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
