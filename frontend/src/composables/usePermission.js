/**
 * usePermission.js
 * ─────────────────────────────────────────────────────────────────────
 * Role-based access control using localStorage flags set by GeneralSettings.
 *
 * OVERRIDE: when SSPL Dashboard Tile Access is configured for the user
 * (wb-allowed-tiles-v3 cache written by Dashboard.vue), routes are allowed
 * only for the visible tiles and the role matrix below is bypassed.
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
  'CustomerEnquiry',
  'StockReconciliation',
  'GstDummyLedger',
  'GstLedger',
  'DailyReport',
  'StockLedger',
  'StoreTransfer',
  'Repack',
  'OfferDisplay',
  'PurchaseOrder',
  'LandCostVoucher',
  'Hrms',
  'Employee',
  'Employees',
  'EsslMachines',
  'EsslMapping',
  'EsslAttendance',
  'DeviceUsers',
  'AttendanceChart',
  'ShiftRoaster',
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
  'IncentiveEntry',
  'Unreconciled',
  'ChequeRegister',
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
  'IncentiveEntry',
  'Unreconciled',
  'PurchaseOrder',
  'ChequeRegister',
  'StoreSalesReport',
  'CostCenterSalesReport',
  'StockStatusReport',
  'StockAgingReport',
  'OutstandingCustomersReport',
  'LedgerSalesPurchaseReport',
  'ItemSalesSummary',
  'StoreWiseItemSales',
  'FastMovingItems',
  'MaterialTransferReport',
  'CashflowReport',
  'AccountTree',
  'GeneralLedger',
  'Hrms',
  'Employee',
  'Employees',
  'EsslMachines',
  'EsslMapping',
  'EsslAttendance',
  'DeviceUsers',
  'AttendanceChart',
  'ShiftRoaster',
])

// Route names accessible by admin (excluding sale, purchase, accounts, ledger, stock, and sspl special sections)
export const ADMIN_ROUTES = new Set([
  'Reports',
  'DailyReport',
  'SSPLBillingSettings',
  'StoreSalesReport',
  'CostCenterSalesReport',
  'StockStatusReport',
  'StockAgingReport',
  'OutstandingCustomersReport',
  'LedgerSalesPurchaseReport',
  'ItemSalesSummary',
  'StoreWiseItemSales',
  'FastMovingItems',
  'MaterialTransferReport',
  'CashflowReport',
  'IncentiveLedger',
  'IncentiveEntry',
  'CustomerEnquiry',
  'DiscountRule',
  'ChequeRegister',
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
 * Returns the tile ids configured via SSPL Dashboard Tile Access, read from the
 * cache written by Dashboard.vue (wb-allowed-tiles-v3), or null when tile access
 * is not doctype-configured for this user.
 */
function getConfiguredTileIds() {
  try {
    const cached = JSON.parse(localStorage.getItem('wb-allowed-tiles-v3') || 'null')
    return Array.isArray(cached?.tiles) ? cached.tiles : null
  } catch {
    return null
  }
}

/**
 * Returns true if the current user may navigate to the given route name.
 * Dashboard and Login are always accessible.
 *
 * When tiles are configured via SSPL Dashboard Tile Access, only the routes of
 * the visible tiles are allowed and the role-based sets below are bypassed.
 * Without a tile configuration, the role-based logic applies as before.
 */
export function getLicenseInfo() {
  try {
    return JSON.parse(localStorage.getItem('ae_license_info') || 'null')
  } catch {
    return null
  }
}

// HRMS sub-pages are now restricted under the 'hrms' license feature.
export const PUBLIC_HRMS_ROUTES = []

function getTileIdForRoute(routeName) {
  const hrmsRoutes = [
    'Hrms',
    'Employees',
    'EsslMachines',
    'EsslMapping',
    'EsslAttendance',
    'DeviceUsers',
    'AttendanceChart',
    'ShiftRoaster',
  ]
  if (hrmsRoutes.includes(routeName)) return 'hrms'
  if (routeName === 'Employee') return 'employee'

  for (const [tid, rname] of Object.entries(TILE_ROUTE_MAP)) {
    if (rname === routeName) {
      return tid
    }
  }
  return null
}

export function canAccessRoute(routeName) {
  if (!routeName || ['Dashboard', 'Login'].includes(routeName)) return true
  if (PUBLIC_HRMS_ROUTES.includes(routeName)) return true

  if (routeName === 'PriceListUpdate') {
    return canAccessTile('purchase-invoice')
  }

  const license = getLicenseInfo()
  if (license) {
    if (!license.valid || license.days_remaining < 0) {
      return false
    }
    if (Array.isArray(license.features)) {
      const tileId = getTileIdForRoute(routeName)
      if (tileId && !license.features.includes(tileId) && !license.features.includes('*')) {
        return false
      }
    }
  }

  const role = getUserRole()
  if (role === 'admin') return true

  // Tile access configured → the tile list is the sole authority; the role
  // matrix (and its always-allowed extras) is fully suppressed.
  const tileIds = getConfiguredTileIds()
  if (tileIds) {
    const allowed = new Set(tileIds.map((id) => TILE_ROUTE_MAP[id]).filter(Boolean))
    // Tiles that reach pages indirectly (via search modals) rather than TILE_ROUTE_MAP
    if (tileIds.includes('outstanding-bills')) allowed.add('CustomerLedger')
    // Employees is a sub-page of the HRMS portal and has no tile of its own,
    // so the 'hrms' tile grants it (the 'employee' tile does too, when configured)
    if (tileIds.includes('hrms') || tileIds.includes('employee')) allowed.add('Employees')
    // Same for the eSSL machines list and other HRMS sub-pages — HRMS sub-pages, no tile of their own
    if (tileIds.includes('hrms')) {
      allowed.add('EsslMachines')
      allowed.add('EsslMapping')
      allowed.add('EsslAttendance')
      allowed.add('DeviceUsers')
      allowed.add('AttendanceChart')
      allowed.add('ShiftRoaster')
    }
    if (allowed.has('Reports')) {
      allowed.add('StoreSalesReport')
      allowed.add('CostCenterSalesReport')
      allowed.add('StockStatusReport')
      allowed.add('StockAgingReport')
      allowed.add('OutstandingCustomersReport')
      allowed.add('ItemSalesSummary')
      allowed.add('StoreWiseItemSales')
      allowed.add('FastMovingItems')
      allowed.add('MaterialTransferReport')
      allowed.add('CashflowReport')
    }
    return allowed.has(routeName)
  }

  if (['DailyReport', 'Catelogue'].includes(routeName)) return true

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
  'hrms':              'Hrms',
  'employee':          'Employee',
  'essl-machines':     'EsslMachines',
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
  'incentive-entry':   'IncentiveEntry',
  'reports':           'Reports',
  'store-sale-report': 'StoreSalesReport',
  'cost-center-sale-report': 'CostCenterSalesReport',
  'stock-status-report': 'StockStatusReport',
  'stock-aging-report': 'StockAgingReport',
  'outstanding-customers-report': 'OutstandingCustomersReport',
  'Cashier-Management':'CashierManagement',
  'cancellation':      'Cancellation',
  'pricing-rules':     'DiscountRule',
  'discount-rules':    'DiscountRule',
  'loading-receipt':   'LoadingReceipt',
  'customer-enquiry':  'CustomerEnquiry',
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
  'cheques':           'ChequeRegister',
  'ledger-sales-purchase-report': 'LedgerSalesPurchaseReport',
  'item-sales-summary': 'ItemSalesSummary',
  'store-wise-item-sales': 'StoreWiseItemSales',
  'fast-moving-items': 'FastMovingItems',
  'material-transfer-report': 'MaterialTransferReport',
  'land-cost-voucher': 'LandCostVoucher',
  'account-tree':      'AccountTree',
}

export function canAccessTile(tileId) {
  if (tileId === 'pricelist-update') {
    return canAccessTile('purchase-invoice')
  }

  const license = getLicenseInfo()
  if (license) {
    if (!license.valid || license.days_remaining < 0) {
      return false
    }
    if (Array.isArray(license.features) && !license.features.includes(tileId) && !license.features.includes('*')) {
      return false
    }
  }

  // Tile access configured → membership in the configured list decides,
  // regardless of role flags.
  const tileIds = getConfiguredTileIds()
  if (tileIds) return tileIds.includes(tileId)

  const routeName = TILE_ROUTE_MAP[tileId]
  if (!routeName) return getUserRole() === 'admin'
  return canAccessRoute(routeName)
}
