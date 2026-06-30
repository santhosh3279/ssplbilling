import { io } from 'socket.io-client'

let _socket = null
let _initPromise = null

/**
 * Initialise the shared Frappe socket.io connection.
 * Must be awaited once (in App.vue onMounted) before getFrappeSocket() is called.
 *
 * Frappe's socket.io server uses per-site namespaces: io.of('/sitename').
 * We fetch the site name from the API so this works for any environment
 * without hardcoding — dev (Vite proxy → socketio_port) and production (nginx proxy).
 */
export function initFrappeSocket() {
  if (_initPromise) return _initPromise

  _initPromise = fetch('/api/method/ssplbilling.api.dashboard_api.get_frappe_site_name', {
    credentials: 'include',
  })
    .then((res) => res.json())
    .then(({ message: siteName }) => _connect(siteName || window.location.hostname))
    .catch((err) => {
      console.warn('[frappeSocket] site name fetch failed, falling back to hostname:', err)
      return _connect(window.location.hostname)
    })

  return _initPromise
}

function _connect(siteName) {
  // socket.io interprets 'origin/siteName' as: connect to origin, namespace = /siteName
  _socket = io(`${window.location.origin}/${siteName}`, { withCredentials: true })
  _socket.on('connect', () => console.log(`[frappeSocket] connected (/${siteName})`))
  _socket.on('disconnect', () => console.log('[frappeSocket] disconnected'))
  _socket.on('connect_error', (err) => console.warn('[frappeSocket] error:', err.message))
  return _socket
}

/** Returns the socket after initFrappeSocket() has resolved. */
export function getFrappeSocket() {
  return _socket
}
