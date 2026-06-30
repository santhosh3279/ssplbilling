import { io } from 'socket.io-client'

let _socket = null

/**
 * Returns the single shared Frappe socket.io connection.
 * Dev: Vite proxies /socket.io → socketio_port (vite.config.js).
 * Production: nginx proxies /socket.io → Frappe's socket.io server.
 */
export function getFrappeSocket() {
  if (!_socket) {
    _socket = io(window.location.origin, { withCredentials: true })
    _socket.on('connect', () => console.log('[frappeSocket] connected'))
    _socket.on('disconnect', () => console.log('[frappeSocket] disconnected'))
    _socket.on('connect_error', (err) => console.warn('[frappeSocket] error:', err.message))
  }
  return _socket
}
