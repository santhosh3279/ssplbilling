import { computed, ref } from 'vue'

export const cartItems = ref([])
export const cartCount = computed(() => cartItems.value.reduce((count, item) => count + item.qty, 0))
let activeUser = null

function storageKey() {
  return `catalogue-cart:${activeUser}`
}

export function setCartUser(user) {
  if (activeUser === user) return
  activeUser = user || null
  cartItems.value = []
  if (!activeUser) return
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey()) || '[]')
    if (Array.isArray(saved)) {
      cartItems.value = saved.filter(item =>
        typeof item.pageaddress === 'string' && typeof item.item_code === 'string' &&
        Number.isInteger(item.qty) && item.qty > 0 && item.qty <= 10000
      ).slice(0, 100)
    }
  } catch {
    localStorage.removeItem(storageKey())
  }
}

function save() {
  if (activeUser) localStorage.setItem(storageKey(), JSON.stringify(cartItems.value))
}

export function getQuantity(pageaddress, itemCode) {
  return cartItems.value.find(item => item.pageaddress === pageaddress && item.item_code === itemCode)?.qty || 0
}

export function setQuantity(pageaddress, itemCode, qty) {
  if (!activeUser || !Number.isInteger(qty) || qty < 0 || qty > 10000) return
  const index = cartItems.value.findIndex(item => item.pageaddress === pageaddress && item.item_code === itemCode)
  if (qty === 0) {
    if (index !== -1) cartItems.value.splice(index, 1)
  } else if (index !== -1) {
    cartItems.value[index].qty = qty
  } else if (cartItems.value.length < 100) {
    cartItems.value.push({ pageaddress, item_code: itemCode, qty })
  }
  save()
}

export function clearCart() {
  cartItems.value = []
  save()
}
