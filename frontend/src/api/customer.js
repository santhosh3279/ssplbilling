import { frappePost } from '../api.js'

/**
 * Creates an Address doctype linked to a specific entity.
 */
export async function createAddress(data, linkType, linkName) {
  const doc = {
    doctype: 'Address',
    address_title: data.customer_name,
    address_type: 'Billing',
    address_line1: data.address_line1,
    address_line2: data.address_line2,
    address_line3: data.address_line3,
    city: data.city,
    pincode: data.pincode,
    state: data.state,
    country: 'India', // Defaulting to India
    links: [
      {
        link_doctype: linkType,
        link_name: linkName
      }
    ]
  }
  return frappePost('frappe.client.insert', { doc })
}

/**
 * Creates a Contact doctype linked to a specific entity.
 */
export async function createContact(data, linkType, linkName) {
  const phoneNos = []
  if (data.mobile) {
    phoneNos.push({ phone: data.mobile, is_primary_mobile_no: 1, type: 'Mobile' })
  }
  if (data.whatsapp) {
    phoneNos.push({ phone: data.whatsapp, is_primary_mobile_no: 0, type: 'WhatsApp' })
  }

  const doc = {
    doctype: 'Contact',
    first_name: data.customer_name,
    email_id: data.email,
    mobile_no: data.mobile || data.whatsapp,
    phone_nos: phoneNos,
    links: [
      {
        link_doctype: linkType,
        link_name: linkName
      }
    ]
  }
  return frappePost('frappe.client.insert', { doc })
}

/**
 * Creates a Customer and its associated Contact and Address.
 */
export async function createCustomer(data) {
  // 1. Insert Customer
  const customerDoc = {
    doctype: 'Customer',
    customer_name: data.customer_name,
    customer_type: 'Individual', // Defaulting to Individual
    customer_group: 'All Customer Groups', // Standard ERPNext default
    territory: 'All Territories', // Standard ERPNext default
    mobile_no: data.mobile,
    email_id: data.email,
    gstin: data.gstin
  }
  
  const customer = await frappePost('frappe.client.insert', { doc: customerDoc })
  const customerName = customer.name

  // 2. Insert Address linked to Customer
  if (data.address_line1 || data.city) {
    await createAddress(data, 'Customer', customerName)
  }

  // 3. Insert Contact linked to Customer
  if (data.mobile || data.whatsapp || data.email) {
    await createContact(data, 'Customer', customerName)
  }

  return customer
}

/**
 * Updates an existing Customer and handles Address/Contact if needed.
 * (Keeping this simple for now, as updating linked docs is more complex)
 */
export async function updateCustomer(customerId, data) {
  const doc = {
    doctype: 'Customer',
    name: customerId,
    customer_name: data.customer_name,
    mobile_no: data.mobile,
    email_id: data.email,
    gstin: data.gstin
  }
  return frappePost('frappe.client.save', { doc })
}
