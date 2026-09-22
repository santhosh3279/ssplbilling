import { ref } from 'vue'
import { session } from '../session.js'

export const orderContext = ref({ customer: '', customer_name: '', price_list: '' })
let contextUser = null

export function setOrderUser(user) {
  if (contextUser === user) return
  contextUser = user || null
  orderContext.value = { customer: '', customer_name: '', price_list: '' }
  if (!contextUser) return
  try {
    const saved = JSON.parse(sessionStorage.getItem(`catalogue-order:${contextUser}`) || '{}')
    if (typeof saved.customer === 'string' && typeof saved.price_list === 'string') orderContext.value = saved
  } catch { /* A missing or invalid saved selection needs a fresh choice. */ }
}

export function setOrderContext(value) {
  orderContext.value = value
  if (contextUser) sessionStorage.setItem(`catalogue-order:${contextUser}`, JSON.stringify(value))
}

export function orderParams() {
  return session.isSystemUser.value
    ? { customer: orderContext.value.customer, price_list: orderContext.value.price_list }
    : {}
}
