// All current dates/times come from the server. performance.now() only measures
// elapsed time: changing the workstation clock cannot move this clock.
let anchorEpoch = null
let anchorTick = 0
let timezone = null
let pendingSync = null

/** Serialize a calendar Date's local fields, without converting to UTC. */
export function toLocalISO(date) {
  const d = date instanceof Date ? date : parseCalendarDate(date)
  if (isNaN(d.getTime())) return ''
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Date-only values are calendar fields, not UTC instants. Noon avoids DST gaps. */
export function parseCalendarDate(value) {
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return new Date(`${value}T12:00:00`)
  }
  return new Date(value)
}

/** Synchronize once per request; reject missing/invalid server data. No PC fallback. */
export function primeServerTime() {
  if (pendingSync) return pendingSync
  pendingSync = (async () => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 15000)
    try {
      const started = performance.now()
      const res = await fetch('/api/method/ssplbilling.api.dashboard_api.get_server_time', {
        cache: 'no-store', signal: controller.signal,
      })
      if (!res.ok) throw new Error(`Server time: HTTP ${res.status}`)
      const json = await res.json()
      const data = json.message || json
      const epoch = Number(data?.epoch_ms)
      if (!Number.isFinite(epoch) || epoch <= 0 || !data?.timezone) {
        throw new Error('Server time response is missing a valid epoch or timezone')
      }
      // Validate before replacing an existing good anchor.
      new Intl.DateTimeFormat('en', { timeZone: data.timezone }).format(new Date(epoch))
      const received = performance.now()
      anchorEpoch = epoch + (received - started) / 2
      anchorTick = received
      timezone = data.timezone
      return true
    } finally {
      clearTimeout(timeout)
    }
  })().finally(() => { pendingSync = null })
  return pendingSync
}

export function isServerTimePrimed() {
  return anchorEpoch !== null
}

export function serverNow() {
  if (!isServerTimePrimed()) throw new Error('Server time is not synchronized')
  return new Date(anchorEpoch + performance.now() - anchorTick)
}

export function serverTimezone() {
  if (!timezone) throw new Error('Server timezone is not synchronized')
  return timezone
}

export function serverToday() {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: serverTimezone(), year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(serverNow())
  const fields = Object.fromEntries(parts.map(p => [p.type, p.value]))
  return `${fields.year}-${fields.month}-${fields.day}`
}

/** Calendar-only carrier for date arithmetic. Do not use as an instant/time. */
export function serverCalendarDate() {
  return parseCalendarDate(serverToday())
}

export function serverNowTime() {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: serverTimezone(), hour: '2-digit', minute: '2-digit', second: '2-digit',
    hourCycle: 'h23',
  }).format(serverNow())
}

export function isServerToday(isoDate) {
  return String(isoDate || '') === serverToday()
}

/** Refresh long-running tabs and tabs returning from suspension. */
export function startServerTimeSync() {
  const refresh = () => primeServerTime().catch(error => {
    // Retain the last server anchor, never substitute workstation time.
    console.warn('[serverTime] Could not refresh server clock:', error)
  })
  const onVisible = () => { if (document.visibilityState === 'visible') refresh() }
  const timer = setInterval(refresh, 60000)
  window.addEventListener('focus', refresh)
  document.addEventListener('visibilitychange', onVisible)
  return () => {
    clearInterval(timer)
    window.removeEventListener('focus', refresh)
    document.removeEventListener('visibilitychange', onVisible)
  }
}
