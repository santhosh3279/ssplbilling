import { ref } from 'vue'
import { createResource } from 'frappe-ui'

const isLoggedIn = ref(false)
const user = ref(null)
const fullName = ref('')
let initialized = false

const userResource = createResource({
  url: '/api/method/frappe.auth.get_logged_user',
  onSuccess(data) {
    // data could be string or { message: "user@example.com" }
    const usr = typeof data === 'string' ? data : (data?.message || data)
    if (usr && usr !== 'Guest') {
      isLoggedIn.value = true
      user.value = String(usr)
    } else {
      isLoggedIn.value = false
      user.value = null
    }
  },
  onError() {
    isLoggedIn.value = false
    user.value = null
  },
})

const userInfoResource = createResource({
  url: '/api/method/frappe.client.get_value',
  makeParams() {
    return {
      doctype: 'User',
      filters: { name: user.value },
      fieldname: 'full_name',
    }
  },
  onSuccess(data) {
    // data could be { message: { full_name: "..." } } or { full_name: "..." }
    const info = data?.message || data
    fullName.value = String(info?.full_name || user.value || '')
  },
})

async function init() {
  if (initialized) return
  initialized = true
  await userResource.fetch()
  if (isLoggedIn.value) {
    await userInfoResource.fetch()
  }
}

async function login(usr, pwd) {
  const res = await fetch('/api/method/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ usr, pwd }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.message || 'Login failed')
  }
  // Refresh session
  initialized = false
  await init()
  return true
}

async function logout() {
  await fetch('/api/method/logout', { method: 'POST' })
  isLoggedIn.value = false
  user.value = null
  fullName.value = ''
  initialized = false
}

export const session = {
  isLoggedIn,
  user,
  fullName,
  init,
  login,
  logout,
}