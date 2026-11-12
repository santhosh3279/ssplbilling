// Talks to Frappe with the bot's own browser session: reads what was really saved, and cleans up.
class Backend {
  constructor(page) {
    this.page = page
  }

  /** The saved document, straight from ERPNext. */
  async getDoc(doctype, name) {
    // frappe.client.get, not /api/resource/<name>: draft names here can end in "/" (e.g. "RGN00031/")
    const res = await this.page.request.get('/api/method/frappe.client.get', { params: { doctype, name } })
    if (!res.ok()) throw new Error(`Could not read ${doctype} ${name}: ${res.status()} ${(await res.text()).slice(0, 300)}`)
    return (await res.json()).message
  }

  async getSalesInvoice(name) {
    return this.getDoc('Sales Invoice', name)
  }

  /** Delete a draft the bot created. Refuses anything submitted or not owned by a TESTBOT customer. */
  async deleteDraft(doctype, name) {
    let doc
    try {
      doc = await this.getDoc(doctype, name)
    } catch (e) {
      if (/DoesNotExistError|404/.test(e.message)) return false // already gone
      throw e
    }
    const party = doc.customer || doc.party_name || ''
    if (doc.docstatus !== 0 || !party.startsWith('TESTBOT')) {
      throw new Error(`Refusing to delete ${doctype} ${name}: docstatus ${doc.docstatus}, party "${party}"`)
    }
    const result = await this.page.evaluate(async ({ doctype, name }) => {
      const res = await fetch('/api/method/frappe.client.delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.csrf_token ?? 'fetch' },
        body: JSON.stringify({ doctype, name }),
      })
      return { ok: res.ok, text: res.ok ? '' : await res.text() }
    }, { doctype, name })
    if (!result.ok) throw new Error(`Could not delete ${doctype} ${name}: ${result.text.slice(0, 300)}`)
    return true
  }
}

module.exports = { Backend }
