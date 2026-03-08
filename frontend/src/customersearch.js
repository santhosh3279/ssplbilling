import { frappeGet } from './api.js';

/**
 * Search customers by name or ID (partial match) via custom API.
 * Returns customer info including mobile_no, balance, city, whatsapp, and last invoice date.
 *
 * PYTHON CALL: ssplbilling.api.customersearch_api.search_customers
 *
 * @returns {Promise<Array<{name: string, customer_name: string, mobile_no: string, balance: number, city: string, whatsapp: string, last_invoice_date: string}>>}
 */
export async function searchCustomers(query = "") {
  return frappeGet("ssplbilling.api.customersearch_api.search_customers", { query });
}
