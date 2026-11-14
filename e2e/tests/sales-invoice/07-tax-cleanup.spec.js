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

  test('Multi Edit: ticking Non-GST and Delete soft-deletes only the non-GST rows, Undo restores them', async ({ invoice, backend }) => {
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
    expect(rateKeys.length).toBeGreaterThan(0)
    expect(rateKeys.reduce((sum, k) => sum + options[k], 0)).toBe(3) // every row has one rate

    await invoice.removeByTax('nongst')
    expect(await invoice.isRowDeleted(ITEMS.A.code)).toBe(true)
    expect(await invoice.isRowDeleted(ITEMS.B.code)).toBe(true)
    expect(await invoice.isRowDeleted(ITEMS.C.code)).toBe(false)
    await expect.poll(async () => (await invoice.totals()).total).toBe(200)
    // Only the GST row is left: Non-GST is no longer offered
    expect(await invoice.taxCleanupOptions()).toEqual({ gst: 1, [rateKeys[0]]: 1 })

    // Undo brings the Non-GST rows back; delete them again before saving
    await invoice.undoRemoveByTax()
    expect(await invoice.isRowDeleted(ITEMS.A.code)).toBe(false)
    expect(await invoice.isRowDeleted(ITEMS.B.code)).toBe(false)
    await expect.poll(async () => (await invoice.totals()).total).toBe(799) // 798.60 rounded
    await invoice.removeByTax('nongst')
    await expect.poll(async () => (await invoice.totals()).total).toBe(200)

    const saved = await backend.getSalesInvoice(await invoice.save())
    expect(saved.items.map(i => i.item_code)).toEqual([ITEMS.C.code])
    expect(saved.rounded_total || saved.grand_total).toBe(200)
  })
})
