// Settings / tile-access sync shared by Dashboard.vue and mobiledashboard.vue.
// Writes the wb-* / ae-* localStorage keys every page (and usePermission) reads,
// so any landing page must run it — not only the desktop Dashboard.
import { serverToday, serverNow } from './serverTime'
import { session } from '../session'
import { dashboardApi } from './dashboard'
import { fetchAllowedTiles, frappeGet } from '../api.js'
import { useItemCache } from './itemCache.js'
import { syncNamingSeries } from './seriesCache.js'
import { warmPrintCache, clearPrintCache } from './printCache.js'

const SETTINGS_CACHE_KEY = 'wb-settings-v2'
const BILLING_SETTINGS_TTL = 30 * 60 * 1000 // 30 mins
const ALLOWED_SERIES_CACHE_KEY = 'wb-allowed-series-v1'
const OPENING_CASH_DATE_KEY = 'wb-opening-box-cash-date'
const GENERIC_CACHE_TTL = 30 * 60 * 1000 // 30 mins — series / naming series
const LICENSE_CACHE_KEY = 'wb-license-checked-v1'
const EWAY_CACHE_KEY = 'wb-eway-threshold-ts'

// Per-user/group tile selection from SSPL Dashboard Tile Access.
// null = no record configured → fall back to role-based canAccessTile.
// Cached in localStorage with TTL (same policy as billing settings) so login /
// dashboard reloads within the window don't refetch. Cache is keyed to the
// resolved user, so switching the inherited user invalidates it automatically.
// v3: v2 caches hold the pre-ordering (alphabetical) tile list — key bump forces a refetch
export const TILE_CACHE_KEY = 'wb-allowed-tiles-v3'
const TILE_CACHE_TTL = 30 * 60 * 1000 // 30 mins

export function readTileCache() {
  try { return JSON.parse(localStorage.getItem(TILE_CACHE_KEY) || 'null') } catch { return null }
}

localStorage.removeItem('wb-allowed-tiles')    // drop pre-TTL cache key
localStorage.removeItem('wb-allowed-tiles-v2') // drop pre-ordering cache key

// Returns the configured tile ids, or null (no record → role-based fallback).
// On a failed fetch returns undefined so callers keep what they already show.
export async function loadAllowedTiles(user = null, force = false) {
  const cacheUser = user || session.user.value
  const cached = readTileCache()
  if (!force && cached && cached.user === cacheUser && (serverNow().getTime() - cached.ts) < TILE_CACHE_TTL) {
    if (typeof cached.allow_date_modification !== 'undefined') {
      localStorage.setItem('wb-allow-date-modification', cached.allow_date_modification ? '1' : '0')
    }
    return cached.tiles
  }
  try {
    // Resolve for the inherited user; server falls back to the logged-in user
    const res = await fetchAllowedTiles(user)
    const tiles = res?.configured ? res.tiles : null
    const allowDateMod = res?.allow_date_modification ? '1' : '0'
    localStorage.setItem('wb-allow-date-modification', allowDateMod)
    localStorage.setItem(TILE_CACHE_KEY, JSON.stringify({
      user: cacheUser,
      tiles,
      allow_date_modification: Boolean(res?.allow_date_modification),
      ts: serverNow().getTime(),
    }))
    return tiles
  } catch (e) {
    console.warn('[Dashboard] fetchAllowedTiles failed:', e)
  }
}

// 1. Fetch allowed series for this user — cached per user with TTL.
async function syncAllowedSeries(targetUser, force) {
  try {
    let d = null
    const cached = JSON.parse(localStorage.getItem(ALLOWED_SERIES_CACHE_KEY) || 'null')
    const cacheValid = !force && cached && cached.user === targetUser &&
      (serverNow().getTime() - cached.ts) < GENERIC_CACHE_TTL
    if (cacheValid) {
      d = cached.data
    } else {
      d = await dashboardApi.getAllowedSeries(targetUser)
      localStorage.setItem(ALLOWED_SERIES_CACHE_KEY, JSON.stringify({ data: d, user: targetUser, ts: serverNow().getTime() }))
    }
  } catch (e) {
    console.warn('[Dashboard] getAllowedSeries failed:', e)
  }
}

// 2. Fetch global settings
async function syncBillingSettings(targetUser, force) {
  try {
    // Check cache first
    let settings = null
    const cached = JSON.parse(localStorage.getItem(SETTINGS_CACHE_KEY) || 'null')
    const cacheValid = !force && cached &&
      (serverNow().getTime() - cached.ts) < BILLING_SETTINGS_TTL &&
      cached.data?._current_user === targetUser &&
      // Payload written before SSPL Printer Setting existed: refetch instead of
      // leaving wb-printer-records unwritten until the TTL expires
      cached.data?.printer_records !== undefined &&
      // Older settings payloads must be refreshed to populate wb-gst.
      cached.data?.company_gstin !== undefined
    if (cacheValid) {
      settings = cached.data
    } else {
      settings = await dashboardApi.getBillingSettings(targetUser)
      if (settings) {
        const settingsWithUser = { ...settings, _current_user: targetUser }
        localStorage.setItem(SETTINGS_CACHE_KEY, JSON.stringify({ data: settingsWithUser, ts: serverNow().getTime() }))
      }
    }

    if (settings) {
      localStorage.setItem('wb-gst', settings.company_gstin || '')
    }
    if (settings && settings.currency_precision !== undefined && settings.currency_precision !== null) {
      localStorage.setItem('wb-prcision', String(settings.currency_precision))
    }
    // Sync user's zoom to localStorage so Sales Invoice can use it
    if (settings && settings.user_zoom) {
      localStorage.setItem('wb-zoom', settings.user_zoom)
    }
    if (settings && settings.wb_theme) {
      const t = settings.wb_theme.toLowerCase() === 'dark' ? 'dark' : 'light'
      localStorage.setItem('wb-theme', t)
      // Do not call applyTheme() here to avoid overwriting Session_Theme once logged in
    }
    if (settings) {
      // Write unconditionally: a blank cipher_map means encryption is off, so
      // the stale key has to be cleared rather than left behind.
      const cipher = (settings.cipher_map || '').trim()
      if (cipher) {
        localStorage.setItem('wb-cipher', cipher)
      } else {
        localStorage.removeItem('wb-cipher')
      }
    }
    if (settings && settings.tax_paid_on_purchase) {
      localStorage.setItem('wb-tax-paid-on-purchase', settings.tax_paid_on_purchase)
    }
    if (settings && settings.discount_account) {
      localStorage.setItem('wb-discount-account', settings.discount_account)
    }
    if (settings && settings.short_or_excess_account) {
      localStorage.setItem('wb-short-or-excess-account', settings.short_or_excess_account)
    }
    if (settings && settings.float_precision !== undefined && settings.float_precision !== null) {
      localStorage.setItem('wb-precision', String(settings.float_precision))
    }

    // Sync roles to localStorage for permission inherited
    if (settings && settings.user_role) {
      const roles = settings.user_role
      localStorage.setItem('wb-role-admin', roles.admin ? '1' : '0')
      localStorage.setItem('wb-role-cashier', roles.cashier ? '1' : '0')
      localStorage.setItem('wb-role-biller', roles.biller ? '1' : '0')
      localStorage.setItem('wb-role-accounts', roles.accounts ? '1' : '0')
    }

    // Set billing defaults from the first visible series row
    const firstSeries = (settings?.billing_series || [])[0]
    if (firstSeries) {
      localStorage.setItem('wb-tax-type-incl', firstSeries.tax_type_incl ? '1' : '0')
    }

    // Sync printer settings to localStorage
    if (settings && settings.user_defaults) {
      const defaults = settings.user_defaults
      if (defaults.default_printer) localStorage.setItem('wb-printer', defaults.default_printer)
      // Cleared when the user's row leaves them blank, so the previous user's never carry over
      ;[
        ['wb-warehouse', defaults.warehouse],
        ['wb-cost-center', defaults.cost_center],
        ['wb-income-account', defaults.income_account],
        ['wb-company', defaults.company],
      ].forEach(([k, v]) => (v ? localStorage.setItem(k, v) : localStorage.removeItem(k)))
      // Paytm card machine assigned to this user; cleared when the assignment is removed
      ;[['wb-tid', defaults.paytm_tid], ['wb-posid', defaults.paytm_pos_id]]
        .forEach(([k, v]) => (v ? localStorage.setItem(k, v) : localStorage.removeItem(k)))
    }

    // Printer & Template mapping from settings
    if (settings && settings.printer_settings) {
       localStorage.setItem('wb-printer-templates', JSON.stringify(settings.printer_settings))
    }

    // SSPL Printer Setting records (printer -> allowed users + default format).
    // Takes precedence over the legacy wb-printer-templates rows in PrintOptionsModal.
    if (settings && settings.printer_records) {
       localStorage.setItem('wb-printer-records', JSON.stringify(settings.printer_records))
    }

    // Warm the Print Template / Printer lists so PrintOptionsModal opens with no round
    // trip. One bucket per doctype the print dialogs actually ask for:
    //   ''                 → GeneralLedger's ledger print (the Customer
    //                        Ledger templates are stored with an empty document_type)
    //   'Sales Invoice' / 'Purchase Invoice' → the invoice pages and GeneralLedger's
    //                        voucher print
    warmPrintCache(['Sales Invoice', 'Purchase Invoice', ''])

    // Sync Automatic Entries (single doctype) values to localStorage under ae-* keys
    if (settings && settings.automatic_entries) {
      const ae = settings.automatic_entries
      localStorage.setItem('ae-alternative_company', ae.alternative_company || '')
      localStorage.setItem('ae-warehouse', ae.warehouse || '')
      localStorage.setItem('ae_payment_series', ae.payment_entry_naming_settings || '')
      localStorage.setItem('ae_journal_series', ae.journal_entry_naming_settings || '')
      localStorage.setItem('ae-series', JSON.stringify(ae.series || []))
      localStorage.setItem('ae-accounts', JSON.stringify(ae.accounts || []))
    }

  } catch (e) {
    console.warn('[Dashboard] getBillingSettings failed:', e)
  }
}

// 2.5 Fetch license status from server
async function syncLicenseStatus(force) {
  try {
    // License state only changes on renewal: check once per day (or on a forced settings refresh).
    const today = serverToday()
    if (!force && localStorage.getItem(LICENSE_CACHE_KEY) === today && localStorage.getItem('ae_license_info')) {
      return
    }
    const lic = await frappeGet('ssplbilling.api.license_api.get_license_status')
    localStorage.setItem(LICENSE_CACHE_KEY, today)
    localStorage.setItem('ae_license_info', JSON.stringify(lic))
  } catch (e) {
    console.warn('[Dashboard] get_license_status failed:', e)
  }
}

// 3. Sync today's opening box cash — refetch only once per calendar day
//    (date-keyed, NOT TTL: a stale value here would show yesterday's opening).
async function syncOpeningBoxCash(force) {
  try {
    const today = serverToday()
    const haveToday = localStorage.getItem(OPENING_CASH_DATE_KEY) === today &&
      localStorage.getItem('wb-opening-box-cash') != null
    if (force || !haveToday) {
      const openingRes = await frappeGet('ssplbilling.api.cahierlog_api.get_opening_total', { date: today })
      if (openingRes) {
        const boxCash = String(openingRes.total || 0)
        localStorage.setItem('opening_cash', boxCash)
        localStorage.setItem('wb-opening-box-cash', boxCash)
        localStorage.setItem(OPENING_CASH_DATE_KEY, today)
      }
    }
  } catch (e) {
    console.warn('[Dashboard] opening box cash sync failed:', e)
  }
}

// 4. Fetch and store all naming series for the requested DocTypes.
//    Rarely changes → seriesCache refetches on TTL expiry or when any
//    wb-series-* key is missing/empty; consumers read those LS keys.
async function syncNamingSeriesStep(force) {
  try {
    await syncNamingSeries(force)
  } catch (e) {
    console.warn('[Dashboard] syncNamingSeries failed:', e)
  }
}

// 5. Fetch and store E-Way Bill threshold value
async function syncEwayThreshold(force) {
  try {
    const ts = Number(localStorage.getItem(EWAY_CACHE_KEY) || 0)
    if (!force && localStorage.getItem('wb-eway-threshold') != null && (serverNow().getTime() - ts) < GENERIC_CACHE_TTL) return
    const ewayVal = await frappeGet('ssplbilling.api.ewaybill_api.get_eway_threshold')
    const threshold = String(ewayVal || 0)
    localStorage.setItem('wb-eway-threshold', threshold)
    localStorage.setItem('wb-eway-threshould', threshold)
    localStorage.setItem(EWAY_CACHE_KEY, String(serverNow().getTime()))
  } catch (e) {
    console.warn('[Dashboard] get_eway_threshold failed:', e)
  }
}

export async function fetchSettings(user = null, force = false) {
  const targetUser = user || session.user.value
  // Independent steps run together; naming series waits for billing settings (company defaults).
  await Promise.all([
    syncAllowedSeries(targetUser, force),
    syncBillingSettings(targetUser, force).then(() => syncNamingSeriesStep(force)),
    syncLicenseStatus(force),
    syncOpeningBoxCash(force),
    syncEwayThreshold(force),
  ])
}

// Forced full resync (Sync button, inherit-user switch). `user` is the settings
// user — the inherited one when an admin previews another user.
export async function syncSettings(user) {
  localStorage.removeItem(SETTINGS_CACHE_KEY)
  clearPrintCache()
  // force=true bypasses the series / opening-cash / naming-series caches too.
  await fetchSettings(user, true)
  await loadAllowedTiles(user !== session.user.value ? user : null, true)
  try {
    await useItemCache().refreshDiscountRuleCache()
  } catch (e) {
    console.warn('[Dashboard] refreshDiscountRuleCache failed:', e)
  }
}
