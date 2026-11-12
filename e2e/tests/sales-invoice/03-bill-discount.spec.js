const { test, expect, env, CUSTOMERS, ITEMS, near } = require('../../lib/fixtures')

test.describe('Sales Invoice: bill discount', () => {
  test('a typed discount % reduces the total and is saved', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.B.code, 4) // 1000.00
    await invoice.setDiscountPct(5)

    const screen = await invoice.totals()
    expect(near(screen.discount, 50)).toBeTruthy()
    expect(screen.total).toBe(950)

    const saved = await backend.getSalesInvoice(await invoice.save())
    expect(saved.additional_discount_percentage).toBe(5)
    expect(near(saved.discount_amount, 50)).toBeTruthy()
    expect(saved.rounded_total || saved.grand_total).toBe(950)
  })

  test('a typed discount amount reduces the total and is saved', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.B.code, 4)
    await invoice.setDiscountAmount(75)

    const screen = await invoice.totals()
    expect(near(screen.discount, 75)).toBeTruthy()
    expect(screen.total).toBe(925)

    const saved = await backend.getSalesInvoice(await invoice.save())
    expect(near(saved.discount_amount, 75)).toBeTruthy()
    expect(saved.rounded_total || saved.grand_total).toBe(925)
  })

  test('a hand-typed discount survives switching to a customer without a modifier', async ({ invoice }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.setDiscountPct(7)
    await invoice.changeCustomer(CUSTOMERS.markup) // no rows yet: no reprice prompt
    expect(await invoice.discountPct()).toBe(7)
  })
})
