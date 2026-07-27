import { ref } from 'vue'
import { registerTab, releaseTab } from '../api'

const HEARTBEAT_MS = 20000

export const tabLimitBlocked = ref(false)
export const tabLimitInfo = ref({ active_tabs: 0, max_tabs: null })

let tabId = null
let heartbeatTimer = null
let initPromise = null

function getTabId() {
  if (tabId) return tabId
  tabId = sessionStorage.getItem('wb_tab_id')
  if (!tabId) {
    tabId = `tab_${Date.now()}_${Math.random().toString(36).slice(2)}`
    sessionStorage.setItem('wb_tab_id', tabId)
  }
  return tabId
}

async function heartbeat() {
  try {
    const res = await registerTab(getTabId())
    tabLimitInfo.value = { active_tabs: res.active_tabs, max_tabs: res.max_tabs }
    tabLimitBlocked.value = res.status === 'limit_reached'
  } catch (e) {
    console.warn('[tabSession] heartbeat failed:', e)
  }
}

function releaseOnUnload() {
  // fetch + keepalive (not sendBeacon) so the CSRF header still goes out on tab close.
  fetch('/api/method/ssplbilling.api.tab_session_api.release_tab', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': window.csrf_token ?? 'fetch',
    },
    body: JSON.stringify({ tab_id: getTabId() }),
    keepalive: true,
  }).catch(() => {})
}

/**
 * Idempotent: safe to call on every router navigation once logged in.
 * Returns a promise that resolves once the *first* heartbeat completes, so the
 * router guard can await tab-limit state before rendering the route — avoids a
 * flash of full app content before the blocked overlay lands.
 */
export function initTabSession() {
  if (!initPromise) {
    initPromise = heartbeat().then(() => {
      heartbeatTimer = setInterval(heartbeat, HEARTBEAT_MS)
      window.addEventListener('beforeunload', releaseOnUnload)
    })
  }
  return initPromise
}

export async function destroyTabSession() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
  initPromise = null
  window.removeEventListener('beforeunload', releaseOnUnload)
  tabLimitBlocked.value = false
  try {
    await releaseTab(getTabId())
  } catch (e) {
    console.warn('[tabSession] release failed:', e)
  }
}
