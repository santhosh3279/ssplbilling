// Everything the bot can do on the Sales Invoice screen (/frontend/sales), as an operator would.
const { expect } = require('@playwright/test')

/** "-29.580", "+0.000", "1,234.50" -> number */
const num = text => parseFloat(String(text).replace(/[^0-9.-]/g, '')) || 0

class SalesInvoicePage {
  constructor(page) {
    this.page = page
    /** Native confirm()/prompt() texts, in order; accepted automatically. (alert() is the app's own
     *  error window: see alertText / dismissAlert.) */
    this.dialogs = []
    /** Names of the invoices this page saved; the fixture deletes them after the test. */
    this.saved = []
    page.on('dialog', dialog => {
      this.dialogs.push(dialog.message())
      dialog.accept().catch(() => {})
    })
  }

  id(testId) {
    return this.page.getByTestId(testId)
  }

  // ------------------------------------------------------------------ opening

  /** Open a blank bill and pick the billing series (e.g. "EOW.#####"). */
  async open(series) {
    // The page pulls the item list into the browser on load; item entry needs it
    const itemsSynced = this.page
      .waitForResponse(r => r.url().includes('get_items_sync'), { timeout: 20_000 })
      .catch(() => null)
    await this.page.goto('/frontend/sales')
    await this.page.locator(`[data-testid="series-option"][data-series="${series}"]`).click()
    await expect(this.id('party-search-input')).toBeVisible()
    await itemsSynced
  }

  /** Open a saved draft straight into modify mode. */
  async openSaved(name) {
    const itemsSynced = this.page
      .waitForResponse(r => r.url().includes('get_items_sync'), { timeout: 20_000 })
      .catch(() => null)
    await this.page.goto(`/frontend/sales?invoice=${encodeURIComponent(name)}`)
    await expect(this.id('doc-number')).toContainText(name, { timeout: 20_000 })
    await expect(this.id('btn-save')).toContainText(/update/i, { timeout: 20_000 })
    await itemsSynced
  }

  // ------------------------------------------------------------------ party

  /** Search the open party picker and choose the customer by exact name. */
  async pickCustomer(name) {
    const search = this.id('party-search-input')
    await expect(search).toBeVisible()
    await search.fill(name)
    await this.page.locator(`[data-testid="party-result"][data-name="${name}"]`).first().click()
    await expect(search).toBeHidden()
    await expect(this.id('party-name')).toHaveText(name)
  }

  /** Click the party on the bill header to switch to another customer. */
  async changeCustomer(name) {
    await this.id('party-name').click()
    await this.pickCustomer(name)
  }

  /** Answer the "Party Changed" prompt shown when the bill already has rows. */
  async answerReprice(choice) {
    await this.id(choice === 'reprice' ? 'warning-confirm' : 'warning-cancel').click()
    await expect(this.id('warning-confirm')).toBeHidden()
  }

  async setApplyModifier(apply) {
    await this.id('modifier-toggle').setChecked(apply)
  }

  // ------------------------------------------------------------------ items

  row(itemCode, nth = 0) {
    return this.page.locator(`[data-testid="item-row"][data-item-code="${itemCode}"]`).nth(nth)
  }

  rows() {
    return this.page.getByTestId('item-row')
  }

  /** Type an item code, Enter, type the qty, Enter — the operator's keystrokes. */
  async addItem(itemCode, qty) {
    const before = await this.rows().count()
    const code = this.id('item-code-input')
    await code.click()
    await code.fill(itemCode)
    await code.press('Enter')
    const pendingQty = this.id('pending-qty')
    await expect(pendingQty, `${itemCode} was not found by the item entry`).toBeVisible()
    await pendingQty.fill(String(qty))
    await pendingQty.press('Enter')
    await expect(this.rows()).toHaveCount(before + 1)
  }

  /** One row's numbers as shown on screen. */
  async rowValues(itemCode, nth = 0) {
    const row = this.row(itemCode, nth)
    const read = async testId => num(await row.getByTestId(testId).innerText())
    return {
      qty: await read('row-qty'),
      rate: await read('row-rate'),
      discount: await read('row-disc'),
      netRate: await read('row-net-rate'),
      taxRate: await read('row-tax'),
      amount: await read('row-amount'),
      free: (await row.getAttribute('data-free')) === '1',
    }
  }

  // ------------------------------------------------------------------ footer

  async setDiscountPct(value) {
    await this.id('discount-pct').fill(String(value))
  }

  async setDiscountAmount(value) {
    await this.id('discount-amt').fill(String(value))
  }

  /** The bill discount % box: number, or null when empty. */
  async discountPct() {
    const value = await this.id('discount-pct').inputValue()
    return value === '' ? null : parseFloat(value)
  }

  /** The totals panel as shown on screen. */
  async totals() {
    const read = async testId => num(await this.id(testId).innerText())
    return {
      itemDiscount: Math.abs(await read('item-discount-total')),
      discount: Math.abs(await read('discount-total')),
      subtotal: await read('subtotal'),
      tax: await read('total-tax'),
      roundOff: await read('round-off'),
      total: await read('total-amount'),
    }
  }

  // ------------------------------------------------------------------ saving

  /** Press Save and return the name ERPNext gave the invoice. Closes the print prompt. */
  async save() {
    const response = this.page.waitForResponse(
      r => /ssplbilling\.api\.sales\.(post|update)_sales_invoice/.test(r.url()) && r.request().method() === 'POST'
    )
    await this.id('btn-save').click()
    const res = await response
    const body = await res.json().catch(() => ({}))
    expect(res.ok(), `Save failed: ${JSON.stringify(body).slice(0, 400)}`).toBeTruthy()
    const name = body.message?.name
    expect(name, `Save returned no document name: ${JSON.stringify(body).slice(0, 400)}`).toBeTruthy()
    if (!this.saved.includes(name)) this.saved.push(name)
    // The print prompt opens after every save; the bot never prints
    await this.page.keyboard.press('Escape')
    return name
  }

  /** Click Save expecting the page to refuse; returns the error window's text and dismisses it. */
  async saveExpectingRefusal() {
    let posted = false
    const watch = r => { if (/sales\.(post|update)_sales_invoice/.test(r.url())) posted = true }
    this.page.on('request', watch)
    await this.id('btn-save').click()
    const text = await this.alertText()
    await this.dismissAlert()
    this.page.off('request', watch)
    expect(posted, 'the refused save must not reach the server').toBe(false)
    return text
  }

  // ------------------------------------------------------------------ app error window

  /** Text of the app's error window (the SPA replaces alert() with it). Waits for it to show. */
  async alertText() {
    const message = this.id('app-alert-message')
    await expect(message, 'expected the error window').toBeVisible()
    return (await message.innerText()).trim()
  }

  async dismissAlert() {
    await this.id('app-alert-dismiss').click()
    await expect(this.id('app-alert-message')).toBeHidden()
  }
}

module.exports = { SalesInvoicePage, num }
