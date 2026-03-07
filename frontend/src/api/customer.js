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
 * After ERPNext auto-creates a Contact for the Customer, find it and append
 * the WhatsApp number to its phone_nos child table.
 * Silently skips if the Contact isn't found or the call fails.
 */
async function addWhatsAppToContact(customerName, whatsapp) {
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

    const alreadyAdded = (contact.phone_nos || []).some(p => p.phone === whatsapp)
    if (alreadyAdded) return

    contact.phone_nos = contact.phone_nos || []
    contact.phone_nos.push({ phone: whatsapp, is_primary_mobile_no: 0, type: 'WhatsApp' })
    await frappePost('frappe.client.save', { doc: contact })
  } catch (e) {
    console.warn('[customer] addWhatsAppToContact failed:', e.message)
  }
}

/**
 * Creates a Customer with mobile_no and email_id set directly on the doc.
 * ERPNext automatically creates a linked Contact from these fields —
 * do NOT manually insert a Contact to avoid duplicates.
 *
 * If a WhatsApp number is provided, it is appended to the auto-created Contact.
 * Then creates a Billing Address if address data is provided.
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

  // Run address creation and WhatsApp update in parallel
  await Promise.all([
    (data.address_line1 || data.city) ? createAddress(data, customer.name) : Promise.resolve(),
    data.whatsapp ? addWhatsAppToContact(customer.name, data.whatsapp) : Promise.resolve(),
  ])

  return customer
}

/**
 * Fetches full customer details for the edit form via a single server-side call:
 * Customer fields + primary linked Address + WhatsApp from linked Contact.
 */
export async function fetchCustomerDetails(customerId) {
  return frappeGet('ssplbilling.api.sales_api.get_customer_full', { customer: customerId })
}

/**
 * Saves updated fields on an existing Customer.
 * mobile_no on the Customer doc is the source of truth for the auto-created Contact.
 */
export async function updateCustomer(customerId, data) {
  const doc = {
    doctype: 'Customer',
    name: customerId,
    customer_name: data.customer_name,
    mobile_no: data.mobile || '',
    email_id: data.email || '',
    gstin: data.gstin || '',
  }
  return frappePost('frappe.client.save', { doc })
}
