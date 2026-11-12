// GST-inclusive series: the rate on screen already contains the tax.
const { test, expect, env, CUSTOMERS, ITEMS, near } = require('../../lib/fixtures')

test.describe('Sales Invoice: tax-inclusive series', () => {
  test.skip(!env.E2E_SERIES_INCLUSIVE, 'the bot user has no GST-inclusive Sales Invoice series')

  test('total equals the inclusive rate and the tax inside it matches ERPNext', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_INCLUSIVE)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.B.code, 2) // retail 275 × 2 = 550, tax included

    const row = await invoice.rowValues(ITEMS.B.code)
    expect(row.rate).toBe(ITEMS.B.retail)
    expect(row.taxRate).toBeGreaterThan(0)

    const screen = await invoice.totals()
    expect(screen.total).toBe(550)
    const expectedTax = 550 - 550 / (1 + row.taxRate / 100)
    expect(near(screen.tax, expectedTax, 0.02)).toBeTruthy()
    expect(near(screen.subtotal + screen.tax, 550, 0.02)).toBeTruthy()

    const saved = await backend.getSalesInvoice(await invoice.save())
    expect(saved.rounded_total || saved.grand_total).toBe(550)
    expect(near(saved.total_taxes_and_charges, screen.tax, 0.05)).toBeTruthy()
  })
})
