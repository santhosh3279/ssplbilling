const { test, expect, env, CUSTOMERS, ITEMS } = require('../../lib/fixtures')

// Seeded: TESTBOT-C is a GST item, A and B are not; all three carry the same tax rate.
test.describe('Sales Invoice: Multi Edit (tax cleanup)', () => {
  test.afterEach(async ({ invoice }) => {
    await invoice.setSameCompanyBilling(false)
  })

  test('hidden unless billing into the AE alternative company', async ({ invoice }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.setSameCompanyBilling(false)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.A.code, 1)
    await expect(invoice.taxCleanup()).toHaveCount(0)
  })

  test('Multi Edit: ticking Non-GST removes those rows, unticking brings them back', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.setSameCompanyBilling(true, env.E2E_COMPANY)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.A.code, 1) // 98.60
    await invoice.addItem(ITEMS.B.code, 2) // 500.00
    await invoice.addItem(ITEMS.C.code, 5) // 200.00
    await expect(invoice.taxCleanup()).toBeVisible()

    const options = await invoice.taxCleanupOptions()
    expect(options.gst).toBe(1)
    expect(options.nongst).toBe(2)
    const rateKeys = Object.keys(options).filter(k => k.startsWith('rate:'))
    expect(rateKeys.length).toBe(1) // all three rows share one rate
    expect(options[rateKeys[0]]).toBe(3)

    await invoice.removeByTax('nongst')
    expect(await invoice.isRowDeleted(ITEMS.A.code)).toBe(true)
    expect(await invoice.isRowDeleted(ITEMS.B.code)).toBe(true)
    expect(await invoice.isRowDeleted(ITEMS.C.code)).toBe(false)
    await expect.poll(async () => (await invoice.totals()).total).toBe(200)
    // Categories stay listed with the same counts; the ticked one is shown removed
    expect(await invoice.taxCleanupOptions()).toEqual(options)
    expect(await invoice.taxRemovedKeys()).toEqual(['nongst'])

    // A row comes back only when no ticked category matches it
    await invoice.removeByTax(rateKeys[0])
    await expect.poll(async () => (await invoice.totals()).total).toBe(0)
    await invoice.restoreByTax('nongst')
    expect(await invoice.isRowDeleted(ITEMS.A.code)).toBe(true) // still under the ticked rate
    await invoice.restoreByTax(rateKeys[0])
    expect(await invoice.isRowDeleted(ITEMS.A.code)).toBe(false)
    expect(await invoice.isRowDeleted(ITEMS.C.code)).toBe(false)
    await expect.poll(async () => (await invoice.totals()).total).toBe(799) // 798.60 rounded

    await invoice.removeByTax('nongst')
    const saved = await backend.getSalesInvoice(await invoice.save())
    expect(saved.items.map(i => i.item_code)).toEqual([ITEMS.C.code])
    expect(saved.rounded_total || saved.grand_total).toBe(200)
  })
})
