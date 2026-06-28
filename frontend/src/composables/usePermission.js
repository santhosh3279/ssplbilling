/**
 * usePermission.js
 * ─────────────────────────────────────────────────────────────────────
 * Role-based access control using localStorage flags set by GeneralSettings.
 *
 * Flags (set via USER SERIES row in SSPL Billing Settings):
 *   wb-role-admin    = '1' | '0'
 *   wb-role-cashier  = '1' | '0'
 *   wb-role-biller   = '1' | '0'
 *   wb-role-accounts = '1' | '0'  (JournalContraEntry, Reports; all accounts visible)
 *
 * If no flags are set (settings never loaded), defaults to 'admin' so
 * the system admin is never locked out.
 *
 * Permission matrix:
 *   admin    → all routes
 *   accounts → JournalContraEntry, Reports; sees all GL accounts
 *   cashier  → biller routes + CashierDesk, PurchaseSubmit, CustomerLedger, JournalContraEntry
 *   biller   → SalesInvoice, PurchaseInvoice, Quotation, SalesOrderEntry, ParcelAddress, BarcodePrintPage, LoadingReceipt
 */

// Route names accessible by biller
export const BILLER_ROUTES = new Set([
  'SalesInvoice',
  'PurchaseInvoice',
  'Quotation',
  'SalesOrderEntry',
  'ParcelAddress',
  'BarcodePrintPage',
  'LoadingReceipt',
  'StockReconciliation',
  'GstDummyLedger',
  'GstLedger',
  'DailyReport',
  'StockLedger',
  'StoreTransfer',
  'Repack',
  'OfferDisplay',
  'PurchaseOrder',
])

// Route names additionally accessible by cashier (beyond biller)
export const CASHIER_EXTRA_ROUTES = new Set([
  'CashierDesk',
  'PurchaseSubmit',
  'CustomerLedger',
  'JournalContraEntry',
  'CashierManagement',
  'DailyReport',
  'SingleEntry',
  'NamingSettings',
  'Payment',
  'Expense',
  'IncentiveRedeem',
  'Unreconciled',
])

export const CASHIER_ROUTES = new Set([...BILLER_ROUTES, ...CASHIER_EXTRA_ROUTES])

// Routes accessible by accounts role
export const ACCOUNTS_ROUTES = new Set([
  'Payment',
  'JournalContraEntry',
  'Reports',
  'DailyReport',
  'SingleEntry',
  'IncentiveRedeem',
  'Unreconciled',
  'PurchaseOrder',
])

// Route names accessible by admin (excluding sale, purchase, accounts, ledger, stock, and sspl special sections)
export const ADMIN_ROUTES = new Set([
  'Reports',
  'DailyReport',
  'SSPLBillingSettings',
  'StoreSalesReport',
  'CostCenterSalesReport',
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
  if (!routeName || ['Dashboard', 'Login', 'DailyReport', 'Catelogue'].includes(routeName)) return true
  const role = getUserRole()
  if (role === 'admin') return ADMIN_ROUTES.has(routeName)
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
  'sales':             'SalesInvoice',
  'purchase-invoice':  'PurchaseInvoice',
  'quotation':         'Quotation',
  'sales-order':       'SalesOrderEntry',
  'cashier':           'CashierDesk',
  'purchase-submit':   'PurchaseSubmit',
  'ledger':            'CustomerLedger',
  'general-ledger':    'GeneralLedger',
  'purchase-order':    'PurchaseOrder',
  'journal-contra':    'JournalContraEntry',
  'stock-reconciliation': 'StockReconciliation',
  'payment':           'Payment',
  'expense':           'Expense',
  'pricelist-update':  'PriceListUpdate',
  'barcode-print':     'BarcodePrintPage',
  'incentive-ledger':  'IncentiveLedger',
  'incentive-redeem':  'IncentiveRedeem',
  'reports':           'Reports',
  'store-sale-report': 'StoreSalesReport',
  'cost-center-sale-report': 'CostCenterSalesReport',
  'Cashier-Management':'CashierManagement',
  'cancellation':      'Cancellation',
  'pricing-rules':     'DiscountRule',
  'discount-rules':    'DiscountRule',
  'loading-receipt':   'LoadingReceipt',
  'parcel-address':    'ParcelAddress',
  'gst-dummy-ledger':  'GstDummyLedger',
  'gst-ledger':        'GstLedger',
  'daily-report':      'DailyReport',
  'stock-ledger':      'StockLedger',
  'payment-reconciliation': 'Payment',
  'store-transfer':    'StoreTransfer',
  'repack':            'Repack',
  'single-entry':      'SingleEntry',
  'naming-settings':   'NamingSettings',
  'invoice-template':  'Dashboard',
  'stock-template':    'Dashboard',
  'ssplbillingsettings': 'SSPLBillingSettings',
  'offer-display':     'OfferDisplay',
  'catelogue':         'Catelogue',
  'unreconciled':      'Unreconciled',
}

export function canAccessTile(tileId) {
  const routeName = TILE_ROUTE_MAP[tileId]
  const role = getUserRole()
  if (!routeName) return role === 'admin'
  return canAccessRoute(routeName)
}
