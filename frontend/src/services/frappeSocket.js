import { io } from 'socket.io-client'

// import.meta.env.DEV is true during `yarn dev`, false after `yarn build`
const _isDev = import.meta.env.DEV

let _socket = null
let _initPromise = null

/**
 * Initialise the shared Frappe socket.io connection. Await this once in App.vue
 * before calling getFrappeSocket().
 *
 * Dev:  connect directly to hostname:socketio_port/<siteName> — same as Frappe desk.
 *       Going through the Vite proxy causes an "Invalid origin" error because
 *       changeOrigin:true rewrites the host header, breaking the middleware check.
 * Prod: connect through origin/<siteName>; nginx proxies /socket.io → socket.io server.
 */
export function initFrappeSocket() {
  if (_initPromise) return _initPromise

  _initPromise = fetch('/api/method/ssplbilling.api.dashboard_api.get_frappe_site_name', {
    credentials: 'include',
  })
    .then((res) => res.json())
    .then(({ message }) => _connect(message?.site, message?.socketio_port))
    .catch((err) => {
      console.warn('[frappeSocket] site info fetch failed, using fallback:', err)
      return _connect(null, null)
    })

  return _initPromise
}

function _connect(siteName, socketioPort) {
  siteName = siteName || window.location.hostname
  socketioPort = socketioPort || 9000

  const baseUrl = _isDev
    ? `${window.location.protocol}//${window.location.hostname}:${socketioPort}`
    : window.location.origin

  // extraHeaders are sent with the initial HTTP polling request where auth runs.
  // X-Frappe-Site-Name tells the middleware the actual site name so the namespace
  // check passes even when the connection comes from a non-localhost IP.
  _socket = io(`${baseUrl}/${siteName}`, {
    withCredentials: true,
    extraHeaders: { 'X-Frappe-Site-Name': siteName },
  })
  _socket.on('connect', () => console.log(`[frappeSocket] connected → ${baseUrl}/${siteName}`))
  _socket.on('disconnect', () => console.log('[frappeSocket] disconnected'))
  _socket.on('connect_error', (err) => console.warn('[frappeSocket] error:', err.message))
  return _socket
}

/** Returns the socket synchronously after initFrappeSocket() has resolved. */
export function getFrappeSocket() {
  return _socket
}
