import { frappeGet, frappePost } from '../api.js'

/**
 * Creates a Billing Address linked to a Customer.
 * Only called when at least address_line1 or city is provided.
 */
async function createAddress(data, customerName) {
  const doc = {
    doctype: 'Address',
    address_title: data.customer_name,
    address_type: 'Billing',
    address_line1: data.address_line1 || '',
    address_line2: data.address_line2 || '',
    address_line3: data.address_line3 || '',
    city: data.city || '',
    pincode: data.pincode || '',
    state: data.state || '',
    country: 'India',
    links: [{ link_doctype: 'Customer', link_name: customerName }],
  }
  return frappePost('frappe.client.insert', { doc })
}

/**
 * Updates or appends WhatsApp number to a Contact linked to the Customer.
 * WhatsApp is treated as the Second Mobile Number (Index 1) in the phone_nos table.
 */
async function syncContactPhones(customerName, mobile, whatsapp) {
  try {
    const contacts = await frappeGet('frappe.client.get_list', {
      doctype: 'Contact',
      fields: ['name'],
      filters: [
        ['Dynamic Link', 'link_doctype', '=', 'Customer'],
        ['Dynamic Link', 'link_name', '=', customerName],
      ],
      limit_page_length: 1,
    })
    if (!contacts.length) return

    const contact = await frappeGet('frappe.client.get', {
      doctype: 'Contact',
      name: contacts[0].name,
    })

    contact.phone_nos = contact.phone_nos || []

    // Update or add Primary Mobile (Index 0)
    if (mobile || mobile === '') {
      if (contact.phone_nos.length > 0) {
        contact.phone_nos[0].phone = mobile
        contact.phone_nos[0].is_primary_mobile_no = 1
      } else {
        contact.phone_nos.push({ phone: mobile, is_primary_mobile_no: 1, type: 'Mobile' })
      }
    }

    // Update or add WhatsApp as the Second Mobile Number (Index 1)
    if (whatsapp || whatsapp === '') {
      if (contact.phone_nos.length > 1) {
        contact.phone_nos[1].phone = whatsapp
        contact.phone_nos[1].is_primary_mobile_no = 0
      } else {
        // Ensure there's at least one entry before adding the second
        if (contact.phone_nos.length === 0) {
          contact.phone_nos.push({ phone: mobile || '', is_primary_mobile_no: 1, type: 'Mobile' })
        }
        contact.phone_nos.push({ phone: whatsapp, is_primary_mobile_no: 0, type: 'Mobile' })
      }
    }

    await frappePost('frappe.client.save', { doc: contact })
  } catch (e) {
    console.warn('[customer] syncContactPhones failed:', e.message)
  }
}

/**
 * After ERPNext auto-creates a Contact for the Customer, find it and append
 * the WhatsApp number to its phone_nos child table.
 */
async function addWhatsAppToContact(customerName, whatsapp) {
  return syncContactPhones(customerName, null, whatsapp)
}

/**
 * Creates a Customer with mobile_no and email_id set directly on the doc.
 */
export async function createCustomer(data) {
  const customerDoc = {
    doctype: 'Customer',
    customer_name: data.customer_name,
    customer_type: 'Individual',
    customer_group: 'All Customer Groups',
    territory: 'All Territories',
    mobile_no: data.mobile || '',
    email_id: data.email || '',
    gstin: data.gstin || '',
  }

  const customer = await frappePost('frappe.client.insert', { doc: customerDoc })

  await Promise.all([
    (data.address_line1 || data.city) ? createAddress(data, customer.name) : Promise.resolve(),
    data.whatsapp ? addWhatsAppToContact(customer.name, data.whatsapp) : Promise.resolve(),
  ])

  return customer
}

/**
 * Fetches full customer details using standard Frappe CRUD.
 * Avoids custom API 'ssplbilling.api.sales_api.get_customer_full' which may 500.
 */
export async function fetchCustomerDetails(customerId) {
  const result = {
    name: customerId,
    customer_name: '',
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
  }

  try {
    // 1. Fetch Customer basic info
    const cust = await frappeGet('frappe.client.get', {
      doctype: 'Customer',
      name: customerId,
    })
    result.customer_name = cust.customer_name || ''
    result.mobile = cust.mobile_no || ''
    result.email = cust.email_id || ''
    result.gstin = cust.gstin || ''

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
