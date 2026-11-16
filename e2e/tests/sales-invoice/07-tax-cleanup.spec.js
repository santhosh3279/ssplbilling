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

  test('Rate Edit: positive % lowers every rate, negative raises it, 0 puts them back', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.setSameCompanyBilling(true, env.E2E_COMPANY)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.A.code, 1) // 98.60
    await invoice.addItem(ITEMS.B.code, 2) // 250.00

    expect(await invoice.setRateEdit(10)).toBe('−10%')
    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(88.74)
    expect((await invoice.rowValues(ITEMS.B.code)).rate).toBe(225)

    // Not compounded: −10 % works from the original rates
    expect(await invoice.setRateEdit(-10)).toBe('+10%')
    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(108.46)
    expect((await invoice.rowValues(ITEMS.B.code)).amount).toBe(550)

    expect(await invoice.setRateEdit(0)).toBe('0%')
    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(ITEMS.A.wholesale)
    expect((await invoice.rowValues(ITEMS.B.code)).rate).toBe(ITEMS.B.wholesale)

    await invoice.setRateEdit(10)
    await expect.poll(async () => (await invoice.totals()).total).toBe(539) // 88.74 + 450 = 538.74
    const saved = await backend.getSalesInvoice(await invoice.save())
    expect(saved.items.find(i => i.item_code === ITEMS.A.code).rate).toBe(88.74)
    expect(saved.items.find(i => i.item_code === ITEMS.B.code).rate).toBe(225)
    expect(saved.rounded_total || saved.grand_total).toBe(539)
  })

  test('Rate Edit by valuation: rate = valuation + %, rows without valuation keep their rate', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.setSameCompanyBilling(true, env.E2E_COMPANY)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.A.code, 1) // valuation 50
    await invoice.addItem(ITEMS.B.code, 2) // valuation 100
    await invoice.addItem(ITEMS.C.code, 1) // no valuation

    expect(await invoice.setRateEdit(20, 'valuation')).toBe('Val +20%')
    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(60)
    expect((await invoice.rowValues(ITEMS.B.code)).rate).toBe(120)
    expect((await invoice.rowValues(ITEMS.C.code)).rate).toBe(ITEMS.C.wholesale)

    // Below cost is flagged before applying
    expect(await invoice.rateEditLossPreview(-10, 'valuation')).toBe(2)

    // Back to the current-rate base works from the original rates, not the valuation ones
    expect(await invoice.setRateEdit(10)).toBe('−10%')
    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(88.74)
    expect((await invoice.rowValues(ITEMS.C.code)).rate).toBe(36)

    expect(await invoice.setRateEdit(0, 'valuation')).toBe('Val +0%')
    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(ITEMS.A.valuation)
    expect((await invoice.rowValues(ITEMS.C.code)).rate).toBe(ITEMS.C.wholesale)

    await invoice.setRateEdit(20, 'valuation')
    await expect.poll(async () => (await invoice.totals()).total).toBe(340) // 60 + 240 + 40
    const saved = await backend.getSalesInvoice(await invoice.save())
    expect(saved.items.find(i => i.item_code === ITEMS.A.code).rate).toBe(60)
    expect(saved.items.find(i => i.item_code === ITEMS.B.code).rate).toBe(120)
    expect(saved.items.find(i => i.item_code === ITEMS.C.code).rate).toBe(ITEMS.C.wholesale)
  })
})
