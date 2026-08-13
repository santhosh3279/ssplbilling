// Server-authoritative clock.
//
// Every transaction date (invoices, orders, quotations, payments, stock entries)
// must come from the Frappe server, not the workstation clock — a drifting or
// mis-zoned till PC would otherwise post documents on the wrong day.
//
// `primeServerTime()` is awaited inside `session.init()`, which the router guard
// runs before every non-public route. By the time any page's `setup()` executes,
// the offset is already in place, so `serverToday()` can stay synchronous.

let offsetMs = 0
let timezone = null
let primed = false

/** Local calendar date of a Date object as `yyyy-mm-dd` (never UTC). */
export function toLocalISO(date) {
  const d = date instanceof Date ? date : new Date(date)
  if (isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Fetch the server clock once and remember the offset (not the date itself,
 *  so a session left open past midnight still rolls over correctly). */
export async function primeServerTime() {
  try {
    const res = await fetch('/api/method/ssplbilling.api.dashboard_api.get_server_time')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    const data = json.message || json
    // epoch_ms is timezone-independent; the naive `datetime` string is only a
    // fallback for an older backend and assumes the browser shares the site tz.
    const serverEpoch = Number(data?.epoch_ms) ||
      (data?.datetime ? new Date(String(data.datetime).replace(' ', 'T')).getTime() : NaN)
    if (!isNaN(serverEpoch) && serverEpoch > 0) offsetMs = serverEpoch - Date.now()
    timezone = data?.timezone || null
    primed = true
  } catch (e) {
    // Leave offsetMs at 0 — the client clock is the fallback, and every
    // transaction endpoint also defaults to the server date when the payload
    // date is missing, so a bad clock still cannot corrupt a posting date.
    console.warn('[serverTime] Could not prime server clock:', e)
  }
  return primed
}

/** Current instant according to the server. */
export function serverNow() {
  return new Date(Date.now() + offsetMs)
}

/** Server "today" as `yyyy-mm-dd`, in the site timezone when known. */
export function serverToday() {
  const now = serverNow()
  if (timezone) {
    try {
      return new Intl.DateTimeFormat('en-CA', {
        timeZone: timezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      }).format(now)
    } catch (e) {
      // Unknown timezone id — fall through to local formatting.
    }
  }
  return toLocalISO(now)
}

/** Server clock time as `HH:MM:SS`. */
export function serverNowTime() {
  const d = serverNow()
  if (timezone) {
    try {
      return new Intl.DateTimeFormat('en-GB', {
        timeZone: timezone,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      }).format(d)
    } catch (e) {
      // Unknown timezone id — fall through to local formatting.
    }
  }
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
}

/** True when the given `yyyy-mm-dd` string is the server's current date. */
export function isServerToday(isoDate) {
  return String(isoDate || '') === serverToday()
}

export function isServerTimePrimed() {
  return primed
}
