// Dev-only stand-in for ssplbilling.api.paytm_api (and the WhatsApp pay-link send) so CashierDesk's
// Paytm machine / QR / link-queue flows can be tried without reaching Paytm. Orders live in memory
// and carry MOCK- references, which processPayment refuses, so nothing mocked can be posted.
import { ref } from 'vue'

const STORAGE_KEY = 'wb-paytm-mock'

function readFlag() {
  try { return sessionStorage.getItem(STORAGE_KEY) === '1' } catch (e) { return false }
}

export const paytmMockOn = ref(import.meta.env.DEV && readFlag())

export function setPaytmMock(on) {
  paytmMockOn.value = import.meta.env.DEV && !!on
  try { sessionStorage.setItem(STORAGE_KEY, paytmMockOn.value ? '1' : '0') } catch (e) { /* storage blocked */ }
  if (!paytmMockOn.value) orders.clear()
}

// Methods answered here while mock mode is on; anything else still goes to the server
export const MOCKED_METHODS = new Set([
  'ssplbilling.api.paytm_api.get_devices',
  'ssplbilling.api.paytm_api.send_to_device',
  'ssplbilling.api.paytm_api.create_qr',
  'ssplbilling.api.paytm_api.get_status',
  'ssplbilling.api.paytm_api.cancel',
  'ssplbilling.api.paytm_api.get_qr_queue',
  'ssplbilling.api.paytm_api.get_invoice_qr',
  'ssplbilling.api.whatsapp_api.send_receipt_pay_link',
])

const DEVICE = { device_name: 'Mock Machine', tid: 'MOCKTID1', pos_id: 'MOCKPOS1' }
const orders = new Map()

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

export async function paytmMockCall(method, args = {}, invoiceInfo = () => ({})) {
  await wait(300)
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
      if (method.endsWith('cancel') && o.status === 'Pending') o.status = 'Cancelled'
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
    case 'ssplbilling.api.whatsapp_api.send_receipt_pay_link': {
      const o = orders.get(args.order_id)
      return { phone: `91${o?.customer_mobile || '0000000000'}` }
    }
  }
  throw new Error(`No mock for ${method}`)
}

// Settle the newest pending mock order (or the given one); returns its result, or null if none waits
export function settleMockOrder(status = 'Success', orderId = null) {
  const pending = [...orders.values()].filter(o => o.status === 'Pending' && (!orderId || o.order_id === orderId))
  const o = pending.sort((a, b) => b.created - a.created)[0]
  if (!o) return null
  o.status = status
  return result(o)
}
