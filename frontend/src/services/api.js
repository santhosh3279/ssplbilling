import { call } from 'frappe-ui'

export const api = {
  // Get active customers
  getCustomers: (searchText = '') => {
    return call('frappe.client.get_list', {
      doctype: 'Customer',
      filters: searchText ? [['name', 'like', `%${searchText}%`]] : [],
      fields: ['name', 'customer_name'],
      limit_page_length: 50
    })
  },

  // Get Naming Series for Sales Invoice
  getNamingSeries: async () => {
    const meta = await call('frappe.client.get_meta', { doctype: 'Sales Invoice' })
    const seriesField = meta.fields.find(f => f.fieldname === 'naming_series')
    return seriesField ? seriesField.options.split('\n').filter(Boolean) : []
  },

  // Search by Barcode (Checks Item Barcode)
  getItemByBarcode: async (barcode) => {
    // 1. Find Item
    const items = await call('frappe.client.get_list', {
      doctype: 'Item Barcode',
      filters: { barcode: barcode },
      fields: ['parent as item_code']
    })
    
    if (!items.length) return null
    const itemCode = items[0].item_code

    // Fetch Details in parallel
    const [itemDetails, priceDetails, stockDetails] = await Promise.all([
      call('frappe.client.get_value', {
        doctype: 'Item',
        filters: { name: itemCode },
        fieldname: ['item_code', 'item_name']
      }),
      call('frappe.client.get_value', {
        doctype: 'Item Price',
        filters: { item_code: itemCode, price_list: 'Standard Selling' },
        fieldname: ['price_list_rate']
      }),
      call('frappe.client.get_value', {
        doctype: 'Bin',
        filters: { item_code: itemCode },
        fieldname: ['actual_qty']
      })
    ])

    return {
      item_code: itemDetails.message.item_code,
      item_name: itemDetails.message.item_name,
      rate: priceDetails.message?.price_list_rate || 0,
      stock: stockDetails.message?.actual_qty || 0
    }
  },

  // Search items for modal
  searchItems: (query) => {
    return call('frappe.client.get_list', {
      doctype: 'Item',
      filters: [['item_name', 'like', `%${query}%`]],
      fields: ['name', 'item_name', 'standard_rate as rate'],
      limit_page_length: 20
    })
  },

  // Create Invoice
  createInvoice: (doc) => {
    return call('frappe.client.insert', { doc })
  }
}
