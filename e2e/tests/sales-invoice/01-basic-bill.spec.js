const { test, expect, env, CUSTOMERS, ITEMS, near } = require('../../lib/fixtures')

test.describe('Sales Invoice: basic bill', () => {
  test('three items for a plain customer save as a draft with matching totals', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.plain)
    await invoice.addItem(ITEMS.A.code, 3)
    await invoice.addItem(ITEMS.B.code, 2)
    await invoice.addItem(ITEMS.C.code, 5)

    // Price list rates, no modifier, no discount
    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(ITEMS.A.wholesale)
    expect((await invoice.rowValues(ITEMS.B.code)).rate).toBe(ITEMS.B.wholesale)
    expect((await invoice.rowValues(ITEMS.C.code)).amount).toBe(200)
    expect(await invoice.discountPct()).toBeNull()

    const gross = 3 * ITEMS.A.wholesale + 2 * ITEMS.B.wholesale + 5 * ITEMS.C.wholesale // 995.80
    const screen = await invoice.totals()
    expect(near(screen.subtotal, gross)).toBeTruthy()
    expect(screen.tax).toBe(0) // exempt series
    expect(screen.total).toBe(Math.round(gross))

    const name = await invoice.save()
    const saved = await backend.getSalesInvoice(name)
    expect(saved.docstatus).toBe(0)
    expect(saved.customer).toBe(CUSTOMERS.plain)
    expect(saved.items.map(i => [i.item_code, i.qty, i.rate])).toEqual([
      [ITEMS.A.code, 3, ITEMS.A.wholesale],
      [ITEMS.B.code, 2, ITEMS.B.wholesale],
      [ITEMS.C.code, 5, ITEMS.C.wholesale],
    ])
    expect(saved.rounded_total || saved.grand_total).toBe(screen.total)
  })

  test('saving a bill with no items is refused', async ({ invoice }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.plain)
    expect(await invoice.saveExpectingRefusal()).toMatch(/no items/i)
    expect(invoice.saved).toEqual([])
  })
})
