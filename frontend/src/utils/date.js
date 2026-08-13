// Canonical display date formatting for the whole app: dd/mm/yyyy
// Machine-readable values (API params, <input type="date">, filenames, localStorage)
// must stay ISO yyyy-mm-dd — do not use these helpers for those.

function pad(n) {
  return String(n).padStart(2, '0')
}

function fromDateObject(d) {
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`
}

/**
 * Format any date-ish value as dd/mm/yyyy.
 * Strings in `YYYY-MM-DD` / `YYYY-MM-DD HH:MM:SS` / ISO form are split textually
 * (no Date construction) so UTC-midnight never shifts the day.
 * Unparseable input is returned unchanged; empty input returns `fallback`.
 */
export function formatDMY(value, fallback = '') {
  if (value === null || value === undefined || value === '') return fallback

  if (value instanceof Date) {
    return isNaN(value.getTime()) ? fallback : fromDateObject(value)
  }

  const str = String(value).trim()
  if (!str) return fallback

  const datePart = str.split(/[ T]/)[0]
  const m = datePart.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/)
  if (m) return `${pad(m[3])}/${pad(m[2])}/${m[1]}`

  const d = new Date(str)
  return isNaN(d.getTime()) ? str : fromDateObject(d)
}

/** dd/mm/yyyy hh:mm — for values carrying a time component. */
export function formatDMYTime(value, fallback = '') {
  if (value === null || value === undefined || value === '') return fallback
  const str = String(value).trim()
  const [datePart, timePart] = str.split(/[ T]/)
  const date = formatDMY(datePart, fallback)
  if (!timePart) return date
  return `${date} ${timePart.slice(0, 5)}`
}

/** dd/mm — for compact table cells that deliberately omit the year. */
export function formatDM(value, fallback = '') {
  const full = formatDMY(value, '')
  if (!full) return fallback
  const parts = full.split('/')
  return parts.length === 3 ? `${parts[0]}/${parts[1]}` : full
}
