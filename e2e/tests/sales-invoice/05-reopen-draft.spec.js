// A saved draft must come back exactly as it was billed, and stay that way when updated.
const { test, expect, env, CUSTOMERS, ITEMS } = require('../../lib/fixtures')

test.describe('Sales Invoice: re-open a draft', () => {
  test('rates, bill discount and total are unchanged after re-open and update', async ({ invoice, backend }) => {
    await invoice.open(env.E2E_SERIES_EXEMPT)
    await invoice.pickCustomer(CUSTOMERS.discount)
    await invoice.addItem(ITEMS.A.code, 3)
    await invoice.addItem(ITEMS.C.code, 10)
    const before = await invoice.totals()
    const name = await invoice.save()

    await invoice.openSaved(name)
    expect(await invoice.rows().count()).toBe(2)
    expect((await invoice.rowValues(ITEMS.A.code)).rate).toBe(ITEMS.A.wholesale)
    expect((await invoice.rowValues(ITEMS.C.code)).rate).toBe(ITEMS.C.wholesale)
    expect(await invoice.discountPct()).toBe(10)
    expect((await invoice.totals()).total).toBe(before.total)

    await invoice.save() // Update Bill, nothing edited
    const saved = await backend.getSalesInvoice(name)
    expect(saved.items.map(i => [i.item_code, i.qty, i.rate])).toEqual([
      [ITEMS.A.code, 3, ITEMS.A.wholesale],
      [ITEMS.C.code, 10, ITEMS.C.wholesale],
    ])
    expect(saved.additional_discount_percentage).toBe(10)
    expect(saved.rounded_total || saved.grand_total).toBe(before.total)
  })
})
