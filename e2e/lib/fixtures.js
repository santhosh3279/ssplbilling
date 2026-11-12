// `test` with the bot's helpers wired in. Specs import { test, expect } from here.
const base = require('@playwright/test')
const { requireEnv } = require('./env')
const { Backend } = require('./backend')
const { SalesInvoicePage } = require('./SalesInvoicePage')

const env = requireEnv()

const CUSTOMERS = { plain: 'TESTBOT PLAIN', markup: 'TESTBOT MARKUP', discount: 'TESTBOT DISCOUNT' }
// Rates as seeded by scripts/seed.py: wholesale (W… price lists) and retail
const ITEMS = {
  A: { code: 'TESTBOT-A', wholesale: 98.6, retail: 110 },
  B: { code: 'TESTBOT-B', wholesale: 250, retail: 275 },
  C: { code: 'TESTBOT-C', wholesale: 40, retail: 45 },
}

const test = base.test.extend({
  env: async ({}, use) => use(env),
  backend: async ({ page }, use) => use(new Backend(page)),
  // Sales Invoice screen; every draft it saved is deleted when the test ends, pass or fail
  invoice: async ({ page, backend }, use) => {
    const invoice = new SalesInvoicePage(page)
    await use(invoice)
    for (const name of invoice.saved) {
      await backend.deleteDraft('Sales Invoice', name).catch(e => console.warn(`[cleanup] ${e.message}`))
    }
  },
})

/** Money comparison: equal to the paisa. */
const near = (actual, expected, tolerance = 0.011) => Math.abs(actual - expected) <= tolerance

module.exports = { test, expect: base.expect, env, CUSTOMERS, ITEMS, near }
