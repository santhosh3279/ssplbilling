// Switching party on a bill that already has rows asks: keep the rates, or reprice?
const { test, expect, env, CUSTOMERS, ITEMS } = require('../../lib/fixtures')

test.describe('Sales Invoice: party change with rows', () => {
  test('Retain Prices leaves rates and discount untouched', async ({ invoice }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.A.code, 2)

    await invoice.changeCustomer(CUSTOMERS.markup)
    await invoice.answerReprice('retain')

    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(ITEMS.A.wholesale)
    expect(await invoice.discountPct()).toBeNull()
  })

  test('Reprice applies the new party modifier', async ({ invoice }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.A.code, 2)

    await invoice.changeCustomer(CUSTOMERS.markup)
    await invoice.answerReprice('reprice')
    await expect.poll(async () => (await invoice.rowValues(ITEMS.A.code)).rate).toBe(104)

    await invoice.changeCustomer(CUSTOMERS.discount)
    await invoice.answerReprice('reprice')
    await expect.poll(async () => (await invoice.rowValues(ITEMS.A.code)).rate).toBe(ITEMS.A.wholesale)
    await expect.poll(() => invoice.discountPct()).toBe(10)
  })
})
