/**
 * usePermission.js
 * ─────────────────────────────────────────────────────────────────────
 * Role-based access control using localStorage flags set by GeneralSettings.
 *
 * Flags (set via USER SERIES row in SSPL Billing Settings):
 *   wb-role-admin    = '1' | '0'
 *   wb-role-cashier  = '1' | '0'
 *   wb-role-biller   = '1' | '0'
 *   wb-role-accounts = '1' | '0'  (PayRec, JournalContraEntry, Reports; all accounts visible)
 *
 * If no flags are set (settings never loaded), defaults to 'admin' so
 * the system admin is never locked out.
 *
 * Permission matrix:
 *   admin    → all routes
 *   accounts → PayRec, JournalContraEntry, Reports; sees all GL accounts
 *   cashier  → biller routes + CashierDesk, PurchaseSubmit, CustomerLedger, PayRec, JournalContraEntry
 *   biller   → SalesEntry, PurchaseEntry, QuotationEntry, SalesOrderEntry, ParcelAddress, BarcodePrintPage, LoadingReceipt
 */

// Route names accessible by biller
export const BILLER_ROUTES = new Set([
  'SalesEntry',
  'SalesInvoice',
  'PurchaseEntry',
  'QuotationEntry',
  'SalesOrderEntry',
  'ParcelAddress',
  'BarcodePrintPage',
  'LoadingReceipt',
  'MaterialTransfer',
  'StockReconciliation',
  'GstDummyLedger',
  'GstLedger',
  'DailyReport',
])

// Route names additionally accessible by cashier (beyond biller)
export const CASHIER_EXTRA_ROUTES = new Set([
  'CashierDesk',
  'PurchaseSubmit',
  'CustomerLedger',
  'PayRec',
  'JournalContraEntry',
  'CashierManagement',
  'DailyReport',
])

export const CASHIER_ROUTES = new Set([...BILLER_ROUTES, ...CASHIER_EXTRA_ROUTES])

// Routes accessible by accounts role
export const ACCOUNTS_ROUTES = new Set([
  'PayRec',
  'JournalContraEntry',
  'Reports',
  'DailyReport',
])

/**
 * Returns the effective role for the current user.
 * Priority: admin > cashier > biller > admin (fallback if nothing set).
 */
/**
 * Returns true if the current user has the Accounts flag enabled.
 */
export function canAccessAccounts() {
  return localStorage.getItem('wb-role-accounts') === '1'
}

export function getUserRole() {
  const isAdmin    = localStorage.getItem('wb-role-admin')
  const isCashier  = localStorage.getItem('wb-role-cashier')
  const isBiller   = localStorage.getItem('wb-role-biller')
  const isAccounts = localStorage.getItem('wb-role-accounts')

  // If no flags have ever been written, treat as admin (unconfigured system)
  if (isAdmin === null && isCashier === null && isBiller === null && isAccounts === null) return 'admin'

  if (isAdmin    === '1') return 'admin'
  if (isAccounts === '1') return 'accounts'
  if (isCashier  === '1') return 'cashier'
  if (isBiller   === '1') return 'biller'

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
  if (role === 'accounts') return ACCOUNTS_ROUTES.has(routeName)
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
  'stock-reconciliation': 'StockReconciliation',
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
  'gst-dummy-ledger':  'GstDummyLedger',
  'gst-ledger':        'GstLedger',
  'daily-report':      'DailyReport',
  'sales-invoice':     'SalesInvoice',
  'reconcile':         'Dashboard',
  'invoice-template':  'Dashboard',
  'ssplbillingsettings': 'SSPLBillingSettings',
}

export function canAccessTile(tileId) {
  const routeName = TILE_ROUTE_MAP[tileId]
  const role = getUserRole()
  if (!routeName) return role === 'admin'
  return canAccessRoute(routeName)
}
