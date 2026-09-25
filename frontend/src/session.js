import { ref } from 'vue'
import { createResource } from 'frappe-ui'
import { destroyTabSession } from './services/tabSession'
import { primeServerTime } from './services/serverTime'
import { frappeGet, fetchAllowedTiles } from './api.js'

const isLoggedIn = ref(false)
const user = ref(null)
const fullName = ref('')
const isWebsiteUser = ref(false)
const isSystemUser = ref(false)
let initialized = false

export async function refreshTilePermissions(targetUser) {
  try {
    const res = await fetchAllowedTiles(targetUser)
    if (res) {
      const allowDateMod = res.allow_date_modification ? '1' : '0'
      localStorage.setItem('wb-allow-date-modification', allowDateMod)
      localStorage.setItem('wb-allowed-tiles-v3', JSON.stringify({
        user: targetUser || user.value,
        tiles: res.configured ? res.tiles : null,
        allow_date_modification: Boolean(res.allow_date_modification),
        ts: Date.now(),
      }))
    }
  } catch (e) {
    console.warn('[session] Could not refresh tile permissions:', e)
  }
}

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

async function refreshCsrfToken() {
  try {
    const res = await fetch('/api/method/ssplbilling.api.auth_api.get_csrf_token')
    if (res.ok) {
      const json = await res.json()
      if (json.message) window.csrf_token = json.message
    }
  } catch (e) {
    console.warn('[session] Could not refresh CSRF token:', e)
  }
}

async function init() {
  if (initialized) return
  initialized = true
  await userResource.fetch()
  if (isLoggedIn.value) {
    // primeServerTime must resolve before any page's setup() runs — every
    // transaction date is seeded from the server clock, not the workstation.
    const inheritedUser = localStorage.getItem('wb-inherited-user')
    const effectiveUser = inheritedUser && inheritedUser !== user.value ? inheritedUser : user.value
    await Promise.all([
      userInfoResource.fetch(),
      refreshCsrfToken(),
      primeServerTime(),
      refreshTilePermissions(effectiveUser),
    ])
  }
}

async function checkWebsiteUser() {
  await init()
  const type = isLoggedIn.value ? await frappeGet('ssplbilling.api.auth_api.get_current_user_type') : null
  isWebsiteUser.value = type === 'Website User'
  isSystemUser.value = type === 'System User'
  return isWebsiteUser.value
}

async function login(usr, pwd) {
  const res = await fetch('/api/method/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ usr, pwd }),
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.message || 'Login failed')
  }
  if (data.csrf_token) window.csrf_token = data.csrf_token
  // Refresh session
  isWebsiteUser.value = false
  isSystemUser.value = false
  initialized = false
  await init()
  return true
}

async function logout() {
  await destroyTabSession()

  const headers = {
    'Content-Type': 'application/json',
  }
  const token = typeof window !== 'undefined' ? window.csrf_token : null
  if (token) headers['X-Frappe-CSRF-Token'] = token

  try {
    await fetch('/api/method/ssplbilling.api.auth_api.logout', {
      method: 'POST',
      headers,
      credentials: 'include',
    })
  } catch (e) {
    console.warn('[session] logout via auth_api failed:', e)
  }

  try {
    await fetch('/api/method/logout', {
      method: 'POST',
      headers,
      credentials: 'include',
    })
  } catch (e) {
    console.warn('[session] standard logout failed:', e)
  }

  // Clear non-HttpOnly session cookies in browser
  const cookies = ['sid', 'user_id', 'full_name', 'system_user', 'user_image', 'user_lang']
  cookies.forEach((c) => {
    document.cookie = `${c}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT; Max-Age=0`
  })

  // Reset resources
  if (typeof userResource.reset === 'function') userResource.reset()
  if (typeof userInfoResource.reset === 'function') userInfoResource.reset()

  // Clear tokens & localStorage
  if (typeof window !== 'undefined') window.csrf_token = null
  localStorage.removeItem('wb-allow-date-modification')
  localStorage.removeItem('wb-allowed-tiles-v3')
  localStorage.removeItem('wb-inherited-user')

  isLoggedIn.value = false
  user.value = null
  fullName.value = ''
  isWebsiteUser.value = false
  isSystemUser.value = false
  initialized = false
}

export const session = {
  isLoggedIn,
  user,
  fullName,
  isWebsiteUser,
  isSystemUser,
  checkWebsiteUser,
  init,
  login,
  logout,
}