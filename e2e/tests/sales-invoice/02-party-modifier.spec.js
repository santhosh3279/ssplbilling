// Party modifier (Customer > Pricelist Multiplication Factor):
//   above 1  -> the row rate is multiplied and rounded to the whole rupee
//   below 1  -> rates stay at the price list; the difference becomes the bill discount %
const { test, expect, env, CUSTOMERS, ITEMS, near } = require('../../lib/fixtures')

test.describe('Sales Invoice: party modifier', () => {
  test('modifier above 1 marks the rate up and rounds it to the whole rupee', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.markup) // 1.05
    await invoice.addItem(ITEMS.A.code, 1)
    await invoice.addItem(ITEMS.B.code, 1)
    await invoice.addItem(ITEMS.C.code, 1)

    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(104) // 98.60 × 1.05 = 103.53
    expect((await invoice.rowValues(ITEMS.B.code)).rate).toBe(263) // 250 × 1.05 = 262.50
    expect((await invoice.rowValues(ITEMS.C.code)).rate).toBe(42) // 40 × 1.05 = 42.00
    expect(await invoice.discountPct()).toBeNull()
    expect((await invoice.totals()).total).toBe(104 + 263 + 42)

    const saved = await backend.getSalesInvoice(await invoice.save())
    expect(saved.items.map(i => i.rate)).toEqual([104, 263, 42])
    expect(saved.additional_discount_percentage).toBe(0)
    expect(saved.rounded_total || saved.grand_total).toBe(409)
  })

  test('modifier below 1 keeps the price list rate and becomes a bill discount', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.discount) // 0.9
    await invoice.addItem(ITEMS.A.code, 3)

    const row = await invoice.rowValues(ITEMS.A.code)
    expect(row.rate).toBe(ITEMS.A.wholesale)
    expect(row.discount).toBe(0) // not a row discount
    expect(await invoice.discountPct()).toBe(10)

    const gross = 3 * ITEMS.A.wholesale // 295.80
    const screen = await invoice.totals()
    expect(near(screen.discount, gross * 0.1)).toBeTruthy()
    expect(screen.total).toBe(Math.round(gross * 0.9)) // 266

    const saved = await backend.getSalesInvoice(await invoice.save())
    expect(saved.items[0].rate).toBe(ITEMS.A.wholesale)
    expect(saved.additional_discount_percentage).toBe(10)
    expect(saved.rounded_total || saved.grand_total).toBe(screen.total)
  })

  test('unticking the modifier removes the markup, ticking restores it', async ({ invoice }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.markup)
    await invoice.addItem(ITEMS.A.code, 1)
    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(104)

    await invoice.setApplyModifier(false)
    await expect.poll(async () => (await invoice.rowValues(ITEMS.A.code)).rate).toBe(ITEMS.A.wholesale)

    await invoice.setApplyModifier(true)
    await expect.poll(async () => (await invoice.rowValues(ITEMS.A.code)).rate).toBe(104)
  })

  test('unticking the modifier removes its bill discount, ticking restores it', async ({ invoice }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.discount)
    await invoice.addItem(ITEMS.B.code, 2)
    expect(await invoice.discountPct()).toBe(10)

    await invoice.setApplyModifier(false)
    await expect.poll(() => invoice.discountPct()).toBeNull()
    expect((await invoice.totals()).total).toBe(500)
    expect((await invoice.rowValues(ITEMS.B.code)).rate).toBe(ITEMS.B.wholesale)

    await invoice.setApplyModifier(true)
    await expect.poll(() => invoice.discountPct()).toBe(10)
    expect((await invoice.totals()).total).toBe(450)
  })
})
