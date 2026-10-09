import { frappeGet, frappePost } from '../api.js'

/**
 * Fetches all non-group Customer Groups for selection.
 */
export async function fetchCustomerGroups() {
  const list = await frappeGet('frappe.client.get_list', {
    doctype: 'Customer Group',
    fields: ['name'],
    // Group nodes ('All Customer Groups') are tree parents; ERPNext rejects them on
    // Customer.validate, so they must never reach the dropdown
    filters: [['is_group', '=', 0]],
    order_by: 'name asc',
    limit_page_length: 100,
  })
  return list.map(d => d.name)
}

/** Create the customer and related records in one server transaction. */
export async function createCustomer(data) {
  return frappePost('ssplbilling.api.customersearch_api.create_customer_full', {
    data: JSON.stringify(data),
  }, { silent: true })
}

/**
 * Fetches full customer details using standard Frappe CRUD.
 * Avoids custom API 'ssplbilling.api.sales_api.get_customer_full' which may 500.
 */
export async function fetchCustomerDetails(customerId) {
  const result = {
    name: customerId,
    customer_name: '',
    customer_print_name: '',
    disabled: 0,
    mobile: '',
    whatsapp: '',
    email: '',
    gstin: '',
    address_name: '',
    address_line1: '',
    address_line2: '',
    address_line3: '',
    city: '',
    pincode: '',
    state: '',
    pricelist_multiplication_factor: null,
  }

  try {
    // 1. Fetch Customer basic info
    const cust = await frappeGet('frappe.client.get', {
      doctype: 'Customer',
      name: customerId,
    })
    result.customer_name = cust.customer_name || ''
    result.customer_print_name = cust.customer_print_name || ''
    result.customer_group = cust.customer_group || ''
    result.mobile = cust.mobile_no || ''
    result.email = cust.email_id || ''
    result.gstin = cust.gstin || ''
    result.disabled = cust.disabled || 0
    result.pricelist_multiplication_factor = cust.pricelist_multiplication_factor !== undefined ? cust.pricelist_multiplication_factor : null

    // 2. Fetch linked Address
    const addresses = await frappeGet('frappe.client.get_list', {
      doctype: 'Address',
      fields: ['name'],
      filters: [
        ['Dynamic Link', 'link_doctype', '=', 'Customer'],
        ['Dynamic Link', 'link_name', '=', customerId],
      ],
      limit_page_length: 1,
    })

    if (addresses.length) {
      const addr = await frappeGet('frappe.client.get', {
        doctype: 'Address',
        name: addresses[0].name,
      })
      result.address_name = addr.name
      result.address_line1 = addr.address_line1 || ''
      result.address_line2 = addr.address_line2 || ''
      result.address_line3 = addr.address_line3 || ''
      result.city = addr.city || ''
      result.pincode = addr.pincode || ''
      result.state = addr.state || ''
    }

    // 3. Fetch linked Contact for WhatsApp (Index 1)
    const contacts = await frappeGet('frappe.client.get_list', {
      doctype: 'Contact',
      fields: ['name'],
      filters: [
        ['Dynamic Link', 'link_doctype', '=', 'Customer'],
        ['Dynamic Link', 'link_name', '=', customerId],
      ],
      limit_page_length: 1,
    })

    if (contacts.length) {
      const contact = await frappeGet('frappe.client.get', {
        doctype: 'Contact',
        name: contacts[0].name,
      })
      if (contact.phone_nos && contact.phone_nos.length > 1) {
        result.whatsapp = contact.phone_nos[1].phone
      }
    }

    // 4. Fetch Primary Party link
    const links = await frappeGet('frappe.client.get_list', {
      doctype: 'Party Link',
      fields: ['primary_party', 'primary_role'],
      filters: [['secondary_party', '=', customerId]],
      limit_page_length: 1,
    })
    if (links.length) {
      result.primary_party = links[0].primary_party
      result.primary_party_role = links[0].primary_role
    }
  } catch (e) {
    console.error('[customer] fetchCustomerDetails (standard) failed:', e.message)
    throw e // Rethrow so caller knows it failed
  }

  return result
}

/**
 * Updates Customer + Address + Contact phones via a single server-side call.
 * Avoids partial-document save errors from frappe.client.save.
 */
export async function updateCustomer(customerId, data) {
  return frappePost('ssplbilling.api.customersearch_api.update_customer_full', {
    data: JSON.stringify({ ...data, name: customerId }),
  })
}
