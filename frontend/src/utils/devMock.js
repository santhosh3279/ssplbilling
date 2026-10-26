// Dev-only stand-ins, switched separately from the CashierDesk tester:
// - Paytm mock answers ssplbilling.api.paytm_api so the machine / QR / UPI-queue flows run without
//   reaching Paytm. Orders are kept in localStorage (today's only, like the server queue) so the
//   UPI queue survives closing the page, and carry MOCK- references, which processPayment refuses,
//   so nothing mocked can be posted.
// - WhatsApp mock answers the OpenWA sends (pay link, bill PDF) so nothing reaches a customer; what
//   would have gone is written to the console instead.
import { ref } from 'vue'
import { frappePost } from '../api.js'

const PAYTM_KEY = 'wb-paytm-mock'
const WHATSAPP_KEY = 'wb-whatsapp-mock'
const ORDERS_KEY = 'wb-paytm-mock-orders'

function readFlag(key) {
  try { return sessionStorage.getItem(key) === '1' } catch (e) { return false }
}
function writeFlag(key, on) {
  try { sessionStorage.setItem(key, on ? '1' : '0') } catch (e) { /* storage blocked */ }
}

export const paytmMockOn = ref(import.meta.env.DEV && readFlag(PAYTM_KEY))
export const whatsappMockOn = ref(import.meta.env.DEV && readFlag(WHATSAPP_KEY))

export function setPaytmMock(on) {
  paytmMockOn.value = import.meta.env.DEV && !!on
  writeFlag(PAYTM_KEY, paytmMockOn.value)
  if (!paytmMockOn.value) {
    orders.clear()
    saveOrders()
  }
}

export function setWhatsAppMock(on) {
  whatsappMockOn.value = import.meta.env.DEV && !!on
  writeFlag(WHATSAPP_KEY, whatsappMockOn.value)
}

const WHATSAPP_METHODS = new Set([
  'ssplbilling.api.whatsapp_api.send_receipt_pay_link',
  'ssplbilling.api.whatsapp_api.get_gateway_state',
  'ssplbilling.api.whatsapp_api.send_document',
  'ssplbilling.api.whatsapp_api.send_document_to_number',
  'ssplbilling.api.whatsapp_api.save_party_whatsapp',
])

// Whether the method is answered here rather than by the server, given the switches now on. A mock
// Paytm order exists only in this browser, so its pay link never goes to the real send: with the
// WhatsApp mock off it goes to send_mock_pay_link instead (see mockCall).
export function isMocked(method, args = {}) {
  if (!import.meta.env.DEV) return false
  if (method === 'ssplbilling.api.whatsapp_api.send_receipt_pay_link' && String(args.order_id || '').startsWith('MOCK-')) return true
  return (paytmMockOn.value && PAYTM_METHODS.has(method)) || (whatsappMockOn.value && WHATSAPP_METHODS.has(method))
}

// The mock answer when the method is mocked, else the real call
export function devCall(method, args, real, invoiceInfo) {
  return isMocked(method, args) ? mockCall(method, args, invoiceInfo) : real()
}

const PAYTM_METHODS = new Set([
  'ssplbilling.api.paytm_api.get_devices',
  'ssplbilling.api.paytm_api.send_to_device',
  'ssplbilling.api.paytm_api.create_qr',
  'ssplbilling.api.paytm_api.get_status',
  'ssplbilling.api.paytm_api.cancel',
  'ssplbilling.api.paytm_api.get_qr_queue',
  'ssplbilling.api.paytm_api.get_invoice_qr',
])

const DEVICE = { device_name: 'Mock Machine', tid: 'MOCKTID1', pos_id: 'MOCKPOS1' }
const orders = loadOrders()

function loadOrders() {
  const today = new Date().toDateString()
  try {
    const saved = JSON.parse(localStorage.getItem(ORDERS_KEY) || '[]')
    return new Map(saved.filter(o => new Date(o.created).toDateString() === today).map(o => [o.order_id, o]))
  } catch (e) {
    return new Map()
  }
}

function saveOrders() {
  try { localStorage.setItem(ORDERS_KEY, JSON.stringify([...orders.values()])) } catch (e) { /* storage blocked */ }
}

// Grey placeholder in place of Paytm's QR image
const QR_IMAGE = `data:image/svg+xml;utf8,${encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#e5e7eb"/>'
  + '<text x="50" y="47" font-size="14" text-anchor="middle" font-family="monospace" fill="#374151">MOCK</text>'
  + '<text x="50" y="64" font-size="14" text-anchor="middle" font-family="monospace" fill="#374151">QR</text></svg>',
)}`

function newOrder(channel, args) {
  const order = {
    order_id: `MOCK-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
    channel,
    sales_invoice: args.invoice_name,
    amount: Number(args.amount) || 0,
    status: 'Pending',
    mode: args.pay_mode === 'CARD' ? 'card' : 'upi',
    customer_mobile: args.mobile || args.phone || '',
    created: Date.now(),
  }
  orders.set(order.order_id, order)
  saveOrders()
  return order
}

function result(o) {
  return {
    order_id: o.order_id,
    channel: o.channel,
    sales_invoice: o.sales_invoice,
    status: o.status,
    amount: o.amount,
    mode: o.mode,
    reference_no: o.order_id,
    message: o.status === 'Success' ? 'Mock payment' : o.status === 'Pending' ? 'Waiting (mock)' : `Mock ${o.status.toLowerCase()}`,
  }
}

const wait = (ms) => new Promise(r => setTimeout(r, ms))

function mockWhatsApp(method, args) {
  const { pdf_base64, ...shown } = args
  console.info(`[WhatsApp mock] ${method.split('.').pop()}`, shown)
  switch (method) {
    case 'ssplbilling.api.whatsapp_api.get_gateway_state':
      return { ready: true }
    case 'ssplbilling.api.whatsapp_api.save_party_whatsapp':
      return {}
    case 'ssplbilling.api.whatsapp_api.send_receipt_pay_link': {
      const o = orders.get(args.order_id)
      return { phone: o?.customer_mobile ? `91${o.customer_mobile} (mock)` : '(mock)', message_id: 'MOCK' }
    }
    default:
      return { phone: args.phone ? `${args.phone} (mock)` : '(mock)', message_id: 'MOCK' }
  }
}

// WhatsApp mock off: really send the mock order's pay link (placeholder link)
function sendMockPayLink(args) {
  const o = orders.get(args.order_id)
  if (!o) return Promise.reject(new Error(`Mock order ${args.order_id} not found`))
  return frappePost('ssplbilling.api.whatsapp_api.send_mock_pay_link', {
    invoice_name: o.sales_invoice,
    mobile: o.customer_mobile,
    amount: o.amount,
    order_id: o.order_id,
    with_bill: args.with_bill,
    print_template: args.print_template,
    session_id: args.session_id,
  }, { silent: true })
}

export async function mockCall(method, args = {}, invoiceInfo = () => ({})) {
  if (method === 'ssplbilling.api.whatsapp_api.send_receipt_pay_link' && !whatsappMockOn.value) return sendMockPayLink(args)
  await wait(300)
  if (WHATSAPP_METHODS.has(method)) return mockWhatsApp(method, args)
  return mockPaytm(method, args, invoiceInfo)
}

async function mockPaytm(method, args, invoiceInfo) {
  switch (method) {
    case 'ssplbilling.api.paytm_api.get_devices':
      return { enabled: true, qr_enabled: true, devices: [DEVICE] }
    case 'ssplbilling.api.paytm_api.send_to_device':
      return { order_id: newOrder('EDC', args).order_id, device_name: DEVICE.device_name, status: 'Pending' }
    case 'ssplbilling.api.paytm_api.create_qr': {
      const o = newOrder('QR', args)
      return { order_id: o.order_id, status: 'Pending', qr_image: QR_IMAGE, pos_id: DEVICE.pos_id, tid: DEVICE.tid }
    }
    case 'ssplbilling.api.paytm_api.get_status':
    case 'ssplbilling.api.paytm_api.cancel': {
      const o = orders.get(args.order_id)
      if (!o) throw new Error(`Mock order ${args.order_id} not found`)
      if (method.endsWith('cancel') && o.status === 'Pending') {
        o.status = 'Cancelled'
        saveOrders()
      }
      return result(o)
    }
    case 'ssplbilling.api.paytm_api.get_invoice_qr': {
      const o = orders.get(args.order_id)
      if (!o || o.channel !== 'QR') throw new Error(`No mock QR for ${args.order_id}`)
      return { ...result(o), qr_image: QR_IMAGE, pos_id: DEVICE.pos_id, tid: DEVICE.tid }
    }
    case 'ssplbilling.api.paytm_api.get_qr_queue':
      return [...orders.values()]
        .filter(o => ['Pending', 'Success'].includes(o.status))
        .map(o => ({ ...result(o), customer_mobile: o.customer_mobile, device_name: DEVICE.device_name, tid: DEVICE.tid, ...invoiceInfo(o.sales_invoice) }))
  }
  throw new Error(`No mock for ${method}`)
}

// Settle the newest pending mock order (or the given one); returns its result, or null if none waits
export function settleMockOrder(status = 'Success', orderId = null) {
  const pending = [...orders.values()].filter(o => o.status === 'Pending' && (!orderId || o.order_id === orderId))
  const o = pending.sort((a, b) => b.created - a.created)[0]
  if (!o) return null
  o.status = status
  saveOrders()
  return result(o)
}
