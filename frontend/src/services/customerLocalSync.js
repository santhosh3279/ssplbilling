import { frappeGet } from '../api.js'
import { dashboardApi } from './dashboard.js'

const DB_NAME = 'sspl_db'
const STORE_NAME = 'customers'
const DB_VERSION = 1

const BILLING_SETTINGS_CACHE_KEY = 'wb-billing-settings-v2'

/**
 * Deletes existing sspl_db and old customer storage if any, 
 * then initializes a fresh sspl_db.
 */
async function initDB() {
  // Delete old database if exists
  await new Promise((resolve) => {
    const deleteRequest = indexedDB.deleteDatabase(DB_NAME)
    deleteRequest.onsuccess = () => resolve()
    deleteRequest.onerror = () => resolve() // Continue even if delete fails
    deleteRequest.onblocked = () => resolve()
  })

  // Open/Create fresh database
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = (event) => {
      const db = event.target.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'name' })
      }
    }

    request.onsuccess = (event) => resolve(event.target.result)
    request.onerror = (event) => reject(event.target.error)
  })
}

/**
 * Main sync function to be called during login.
 * Fetches all customer details and global settings from ERPNext and stores them locally.
 */
export async function syncCustomersToLocalDB() {
  console.log('[customerLocalSync] Starting sync...')

  try {
    // 1. Initialize DB (Deletes old and creates fresh)
    const db = await initDB()

    // 2. Fetch all data and settings from ERPNext in parallel for performance
    const [customers, contacts, addresses, settings] = await Promise.all([
      frappeGet('frappe.client.get_list', {
        doctype: 'Customer',
        fields: ['name', 'customer_name', 'email_id', 'mobile_no', 'gstin'],
        limit_page_length: 5000,
      }),
      frappeGet('frappe.client.get_list', {
        doctype: 'Contact',
        fields: ['name', 'phone_nos'],
        filters: [['Dynamic Link', 'link_doctype', '=', 'Customer']],
        limit_page_length: 10000,
      }),
      frappeGet('frappe.client.get_list', {
        doctype: 'Address',
        fields: [
          'name', 'address_line1', 'address_line2', 'address_line3', 
          'city', 'pincode', 'state'
        ],
        filters: [['Dynamic Link', 'link_doctype', '=', 'Customer']],
        limit_page_length: 10000,
      }),
      dashboardApi.getBillingSettings()
    ])

    // 3. Sync Settings to localStorage
    if (settings) {
      localStorage.setItem(BILLING_SETTINGS_CACHE_KEY, JSON.stringify({ 
        data: settings, 
        ts: Date.now() 
      }))
      // Also sync user zoom specifically if it exists
      if (settings.user_zoom) {
        localStorage.setItem('wb-zoom', settings.user_zoom)
      }
      console.log('[customerLocalSync] Settings synced to localStorage.')
    }
    
    // 4. Combine data into a single object per customer
    const combinedData = customers.map(cust => {
      // Find primary address
      const addr = addresses.find(a => a.name.includes(cust.name)) || {}
      
      // Find contact for mobile numbers
      const contact = contacts.find(c => c.name.includes(cust.name)) || {}
      const phoneNos = contact.phone_nos || []

      return {
        name: cust.name,
        mobile_number_1: cust.mobile_no || (phoneNos[0] ? phoneNos[0].phone : ''),
        mobile_number_2: phoneNos[1] ? phoneNos[1].phone : '',
        email: cust.email_id || '',
        gst: cust.gstin || '',
        address_line_1: addr.address_line1 || '',
        address_line_2: addr.address_line2 || '',
        address_line_3: addr.address_line3 || '',
        city: addr.city || '',
        pincode: addr.pincode || '',
        state: addr.state || ''
      }
    })

    // 5. Bulk insert into IndexedDB
    await new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)

      combinedData.forEach(item => {
        store.put(item)
      })

      transaction.oncomplete = () => {
        db.close()
        resolve()
      }
      transaction.onerror = (event) => reject(event.target.error)
    })

    console.log(`[customerLocalSync] Successfully synced ${combinedData.length} customers.`)
  } catch (error) {
    console.error('[customerLocalSync] Sync failed:', error)
    throw error
  }
}
