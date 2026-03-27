/**
 * usePermission.js
 * ─────────────────────────────────────────────────────────────────────
 * Role-based access control using localStorage flags set by GeneralSettings.
 *
 * Flags (set via USER SERIES row in SSPL Billing Settings):
 *   wb-role-admin   = '1' | '0'
 *   wb-role-cashier = '1' | '0'
 *   wb-role-biller  = '1' | '0'
 *
 * If no flags are set (settings never loaded), defaults to 'admin' so
 * the system admin is never locked out.
 *
 * Permission matrix:
 *   admin   → all routes
 *   cashier → biller routes + CashierDesk, PurchaseSubmit, CustomerLedger
 *   biller  → SalesEntry, PurchaseEntry, QuotationEntry, SalesOrderEntry
 */

// Route names accessible by biller
export const BILLER_ROUTES = new Set([
  'SalesEntry',
  'PurchaseEntry',
  'QuotationEntry',
  'SalesOrderEntry',
])

// Route names additionally accessible by cashier (beyond biller)
export const CASHIER_EXTRA_ROUTES = new Set([
  'CashierDesk',
  'PurchaseSubmit',
  'CustomerLedger',
])

export const CASHIER_ROUTES = new Set([...BILLER_ROUTES, ...CASHIER_EXTRA_ROUTES])

/**
 * Returns the effective role for the current user.
 * Priority: admin > cashier > biller > admin (fallback if nothing set).
 */
export function getUserRole() {
  const isAdmin   = localStorage.getItem('wb-role-admin')
  const isCashier = localStorage.getItem('wb-role-cashier')
  const isBiller  = localStorage.getItem('wb-role-biller')

  // If no flags have ever been written, treat as admin (unconfigured system)
  if (isAdmin === null && isCashier === null && isBiller === null) return 'admin'

  if (isAdmin   === '1') return 'admin'
  if (isCashier === '1') return 'cashier'
  if (isBiller  === '1') return 'biller'

  // All flags explicitly '0' — fallback to admin to avoid full lockout
  return 'admin'
}

/**
 * Returns true if the current user may navigate to the given route name.
 * Dashboard and Login are always accessible.
 */
export function canAccessRoute(routeName) {
  if (!routeName || routeName === 'Dashboard' || routeName === 'Login') return true
  const role = getUserRole()
  if (role === 'admin') return true
  if (role === 'cashier') return CASHIER_ROUTES.has(routeName)
  if (role === 'biller') return BILLER_ROUTES.has(routeName)
  return false
}

/**
 * Returns true if the current user can access a dashboard tile / sidebar link
 * identified by its route id (path segment, e.g. 'sales', 'cashier').
 */
const TILE_ROUTE_MAP = {
  'sales':             'SalesEntry',
  'purchase':          'PurchaseEntry',
  'quotation':         'QuotationEntry',
  'sales-order':       'SalesOrderEntry',
  'cashier':           'CashierDesk',
  'purchase-submit':   'PurchaseSubmit',
  'ledger':            'CustomerLedger',
  'purchase-order':    'PurchaseOrder',
  'journal-contra':    'JournalContraEntry',
  'material-transfer': 'MaterialTransfer',
  'payment':           'PayRec',
  'pricelist-update':  'PriceListUpdate',
  'barcode-print':     'BarcodePrintPage',
  'incentive-ledger':  'IncentiveLedger',
  'reports':           'Reports',
  'store-sale-report': 'StoreSalesReport',
  'Cashier-Management':'CashierManagement',
  'pricing-rules':     'PricingRuleSync',
  'loading-receipt':   'LoadingReceipt',
  'parcel-address':    'ParcelAddress',
}

export function canAccessTile(tileId) {
  const routeName = TILE_ROUTE_MAP[tileId]
  if (!routeName) return getUserRole() === 'admin'
  return canAccessRoute(routeName)
}
