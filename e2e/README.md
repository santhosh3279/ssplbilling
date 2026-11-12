# Tester bot (end-to-end tests)

A robot operator: it opens a real browser, logs in to the billing app, bills like a counter user
(series → customer → items → save) and then checks two things: what the **screen** shows, and what
was really **saved in ERPNext**.

It lives here, with its own `package.json`, so nothing in it reaches the production build
(the image only installs `frontend/`).

## Safety

- Runs only against a local dev site (`localhost`, `*.localhost`, `*.local`). Anything else is
  refused unless `E2E_ALLOW_REMOTE=1` is set. `npm run seed` refuses sites not in developer mode.
- Uses its own user (`testbot@sspl.local`), customers (`TESTBOT …`) and items (`TESTBOT-…`).
- Saves **drafts only**, and deletes each one when its test ends. Nothing is submitted, so no stock
  or ledger entry is ever posted. It will not delete a document that is submitted or belongs to a
  non-TESTBOT customer.
- Each saved draft uses up one number of the dev site's naming series.

## One-time setup

```bash
cd e2e
npm install                 # Playwright (dev only)
npx playwright install chromium
npm run seed                # creates the bot user + test data on the dev site, writes e2e/.env
```

`npm run seed` uses the bench's Python (`../../../env/bin/python`). It copies roles and billing
defaults (warehouse, cost center, accounts) from the first biller in SSPL Billing Settings → User
Series, and gives the bot one tax-exempt and one GST-inclusive Sales Invoice series. `.env` holds
the bot's password and is never committed.

If Chromium will not start ("Host system is missing dependencies"): `sudo npx playwright install-deps chromium`.
Without root, unpack the missing libraries under `~/.cache/playwright-libs/root` (or point
`E2E_EXTRA_LIB_PATH` at them); the config adds that folder to the library path.

## Running

The dev site must be up (`bench start`) and the frontend built (`yarn build` in `frontend/`) —
the bot tests what `/frontend` serves, not your unsaved source.

```bash
npm test                                   # everything, headless
npm test -- tests/sales-invoice            # one folder
npm test -- -g "modifier below 1"          # tests whose name matches
npm run test:headed                        # watch the bot work
npm run report                             # open the HTML report of the last run
npm run clean                              # delete any drafts a crashed run left behind
```

A failed test keeps a screenshot, a video and a trace in `test-results/`
(`npx playwright show-trace <trace.zip>` replays it step by step).

To remove the bot user and all its test data from the site:
`../../../env/bin/python scripts/seed.py --purge`.

## What is covered (Sales Invoice)

| File | Checks |
|---|---|
| `01-basic-bill` | 3 items, totals, draft saved with same rates and total; save with no items refused |
| `02-party-modifier` | modifier > 1 marks up and rounds to whole rupee; modifier < 1 becomes bill discount; tick / untick |
| `03-bill-discount` | typed discount % and amount; hand-typed discount kept on customer change |
| `04-party-change` | "Party Changed" prompt: Retain Prices vs Reprice |
| `05-reopen-draft` | saved draft re-opens and updates with unchanged rates, discount, total |
| `06-inclusive-tax` | GST-inclusive series: total, tax inside it, same as ERPNext |

Not covered yet: sale return, discount rules / free items, row-level discount entry, additional
charges, batches, submit + payment (cashier), keyboard shortcuts.

## Layout

```
playwright.config.js      site, timeouts, one worker (one bot = one operator)
scripts/seed.py           create / clean / purge the bot's user and test data
lib/env.js                reads .env, blocks non-local sites
lib/global-setup.js       logs in once, saves the session
lib/fixtures.js           `test` with `invoice` and `backend`; test customers and items
lib/SalesInvoicePage.js   what the bot can do on the Sales Invoice screen
lib/backend.js            read saved documents, delete the bot's drafts
tests/<page>/*.spec.js    scenarios
```

## Adding a test

```js
const { test, expect, env, CUSTOMERS, ITEMS } = require('../../lib/fixtures')

test('two of item A for a plain customer total 197', async ({ invoice, backend }) => {
  await invoice.open(env.E2E_SERIES_EXEMPT)
  await invoice.pickCustomer(CUSTOMERS.plain)
  await invoice.addItem(ITEMS.A.code, 2)
  expect((await invoice.totals()).total).toBe(197)

  const saved = await backend.getSalesInvoice(await invoice.save())   // deleted after the test
  expect(saved.rounded_total).toBe(197)
})
```

The bot finds things on screen by `data-testid` attributes (e.g. `total-amount`, `item-row`,
`discount-pct`). When a test needs a new element, add a `data-testid` to it in the Vue file and a
helper in `lib/SalesInvoicePage.js`; do not select by CSS class or position.

Rule for every bug fixed: add one test that fails before the fix and passes after.
