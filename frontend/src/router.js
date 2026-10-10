import { createRouter, createWebHistory } from 'vue-router'
import { session } from './session'
import { canAccessRoute } from './composables/usePermission'
import { initTabSession } from './services/tabSession'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
const SalesInvoice = () => import('./pages/SalesInvoice.vue')
const Quotation = () => import('./pages/Quotation.vue')
const PurchaseInvoice = () => import('./pages/PurchaseInvoice.vue')
const PriceListUpdate = () => import('./pages/PriceListUpdate.vue')
const StockCheck = () => import('./pages/StockCheck.vue')
const BarcodePrintPage = () => import('./pages/BarcodePrintPage.vue')
const CashierDesk = () => import('./pages/CashierDesk.vue')
const PurchaseSubmit = () => import('./pages/PurchaseSubmit.vue')
const GeneralLedger = () => import('./pages/GeneralLedger.vue')
const PaymentV2 = () => import('./pages/paymentv2.vue')
const JournalContraEntry = () => import('./pages/JournalContraEntry.vue')
const CashierManagement = () => import('./pages/CashierManagement.vue')
const PricingRuleSync = () => import('./pages/PricingRuleSync.vue')
const DiscountRule = () => import('./pages/DiscountRule.vue')
const PurchaseOrder = () => import('./pages/PurchaseOrder.vue')
const SalesOrderEntry = () => import('./pages/SalesOrderEntry.vue')
const SalesOrder = () => import('./pages/SalesOrder.vue')
const IncentiveLedger = () => import('./pages/IncentiveLedger.vue')
const IncentiveRedeem = () => import('./pages/IncentiveRedeem.vue')
const IncentiveEntry = () => import('./pages/IncentiveEntry.vue')
const Reports = () => import('./pages/Reports.vue')
const StoreSalesReport = () => import('./pages/StoreSalesReport.vue')
const CostCenterSalesReport = () => import('./pages/CostCenterSalesReport.vue')
const StockStatusReport = () => import('./pages/StockStatusReport.vue')
const StockAgingReport = () => import('./pages/StockAgingReport.vue')
const OutstandingCustomersReport = () => import('./pages/OutstandingCustomersReport.vue')
const LedgerSalesPurchaseReport = () => import('./pages/LedgerSalesPurchaseReport.vue')
const ItemSalesSummary = () => import('./pages/ItemSalesSummary.vue')
const StoreWiseItemSales = () => import('./pages/StoreWiseItemSales.vue')
const FastMovingItems = () => import('./pages/FastMovingItems.vue')
const MaterialTransferReport = () => import('./pages/MaterialTransferReport.vue')
const LoadingReceipt = () => import('./pages/LoadingReceipt.vue')
const CustomerEnquiry = () => import('./pages/CustomerEnquiry.vue')
const ParcelAddress = () => import('./pages/ParcelAddress.vue')
const StockReconciliation = () => import('./pages/StockReconciliation.vue')
const SSPLBillingSettings = () => import('./pages/SSPLBillingSettings.vue')
const UserCreation = () => import('./pages/UserCreation.vue')
const GstDummyLedger = () => import('./pages/GstDummyLedger.vue')
const GstLedger = () => import('./pages/GstLedger.vue')
const DailyReport = () => import('./pages/DailyReport.vue')
const StoreTransfer = () => import('./pages/StoreTransfer.vue')
const SingleEntry = () => import('./pages/SingleEntry.vue')
const Cancellation = () => import('./pages/Cancellation.vue')
const NamingSettings = () => import('./pages/NamingSettings.vue')
const Expense = () => import('./pages/expense.vue')
const Repack = () => import('./pages/Repack.vue')
const Catalogue = () => import('./pages/catalogue.vue')
const OfferPage = () => import('./pages/OfferPage.vue')
const CatalougePage = () => import('./pages/catalougepage.vue')
const Catelogue = () => import('./pages/catelogue.vue')
const CatalogueViewer = () => import('./pages/catalogueviewer.vue')
const CatalogueCart = () => import('./pages/CatalogueCart.vue')
const CatalogueCheckout = () => import('./pages/CatalogueCheckout.vue')
const Unreconciled = () => import('./pages/unreconciled.vue')
const ChequeRegister = () => import('./pages/ChequeRegister.vue')
const CashflowReport = () => import('./pages/CashflowReport.vue')
const LandCostVoucher = () => import('./pages/land_cost_voucher.vue')
const AccountTree = () => import('./pages/AccountTree.vue')
const Hrms = () => import('./pages/Hrms.vue')
const Employee = () => import('./pages/Employee.vue')
const Employees = () => import('./pages/employees.vue')
const EsslMachines = () => import('./pages/EsslMachines.vue')
const EsslMapping = () => import('./pages/EsslMapping.vue')
const EsslAttendance = () => import('./pages/EsslAttendance.vue')
const DeviceUsers = () => import('./pages/DeviceUsers.vue')
const AttendanceChart = () => import('./pages/AttendanceChart.vue')
const ShiftRoaster = () => import('./pages/ShiftRoaster.vue')
const BatchReports = () => import('./pages/BatchReports.vue')
const ModifySubmitted = () => import('./pages/modifysubmitted.vue')

const routes = [
  {
    path: '/hrms',
    name: 'Hrms',
    component: Hrms,
    meta: { title: 'HRMS' },
  },
  {
    path: '/hrms/employee',
    name: 'Employee',
    component: Employee,
    meta: { title: 'Employee Management' },
  },
  {
    path: '/hrms/employees',
    name: 'Employees',
    component: Employees,
    meta: { title: 'Employees' },
  },
  {
    path: '/hrms/essl-machines',
    name: 'EsslMachines',
    component: EsslMachines,
    meta: { title: 'eSSL Machines' },
  },
  {
    path: '/hrms/essl-mapping',
    name: 'EsslMapping',
    component: EsslMapping,
    meta: { title: 'Employee Mapping' },
  },
  {
    path: '/hrms/attendance',
    name: 'EsslAttendance',
    component: EsslAttendance,
    meta: { title: 'Attendance' },
  },
  {
    path: '/hrms/device-users',
    name: 'DeviceUsers',
    component: DeviceUsers,
    meta: { title: 'Device Users' },
  },
  {
    path: '/hrms/attendance-chart',
    name: 'AttendanceChart',
    component: AttendanceChart,
    meta: { title: 'Attendance Chart' },
  },
  {
    path: '/hrms/shift-roaster',
    name: 'ShiftRoaster',
    component: ShiftRoaster,
    meta: { title: 'Shift Roaster' },
  },
  {
    path: '/catalogue-editor',
    name: 'OfferDisplay',
    component: Catalogue,
    meta: { title: 'Offer Display' },
  },
  {
    path: '/expense',
    name: 'Expense',
    component: Expense,
    meta: { title: 'Expense Entry' },
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true, title: 'Login' },
  },
  {
    // Public mobile page: no login, no license gate (guest API: stock_check_api.search_stock)
    path: '/stock-check',
    name: 'StockCheck',
    component: StockCheck,
    meta: { public: true, title: 'Stock Check' },
  },
  {
    path: '/naming-settings',
    name: 'NamingSettings',
    component: NamingSettings,
    meta: { title: 'Naming Settings' },
  },
  {
    path: '/cancellation',
    name: 'Cancellation',
    component: Cancellation,
    meta: { title: 'Cancellation' },
  },
  {
    path: '/modifysubmitted',
    name: 'ModifySubmitted',
    component: ModifySubmitted,
    meta: { title: 'Modify Submitted Bill' },
  },
  {
    path: '/modify-submitted',
    redirect: '/modifysubmitted',
  },
  {
    path: '/single-entry',
    name: 'SingleEntry',
    component: SingleEntry,
    meta: { title: 'Single Entry' },
  },
  {
    path: '/store-transfer',
    name: 'StoreTransfer',
    component: StoreTransfer,
    meta: { title: 'Store Transfer' },
  },
  {
    path: '/repack',
    name: 'Repack',
    component: Repack,
    meta: { title: 'Repack' },
  },
  {
    path: '/land-cost-voucher',
    name: 'LandCostVoucher',
    component: LandCostVoucher,
    meta: { title: 'Landed Cost Voucher' },
  },
  {
    path: '/daily-report',
    name: 'DailyReport',
    component: DailyReport,
    meta: { title: 'Daily Report' },
  },
  {
    path: '/general-ledger',
    name: 'GeneralLedger',
    component: GeneralLedger,
    meta: { title: 'General Ledger' },
  },
  {
    path: '/ssplbillingsettings',
    name: 'SSPLBillingSettings',
    component: SSPLBillingSettings,
    meta: { title: 'Settings' },
  },
  {
    path: '/ssplbillingsettings/create-user',
    name: 'UserCreation',
    component: UserCreation,
    meta: { title: 'Create Customer User' },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: 'Dashboard' },
  },
  {
    path: '/sales',
    name: 'SalesInvoice',
    component: SalesInvoice,
    meta: { title: 'Sales Invoice' },
  },
  {
    path: '/quotation',
    name: 'Quotation',
    component: Quotation,
    meta: { title: 'Quotation' },
  },
  {
    path: '/purchase-invoice',
    name: 'PurchaseInvoice',
    component: PurchaseInvoice,
    meta: { title: 'Purchase Invoice' },
  },
  {
    path: '/pricelist-update',
    name: 'PriceListUpdate',
    component: PriceListUpdate,
    meta: { title: 'Price List' },
  },
  {
    path: '/barcode-print',
    name: 'BarcodePrintPage',
    component: BarcodePrintPage,
    meta: { title: 'Barcode Print' },
  },
  {
    path: '/cashier',
    name: 'CashierDesk',
    component: CashierDesk,
    meta: { requiresOpening: true, title: 'Cashier' },
  },
  {
    path: '/purchase-submit',
    name: 'PurchaseSubmit',
    component: PurchaseSubmit,
    meta: { title: 'Purchase Submit' },
  },
  {
    path: '/ledger',
    name: 'CustomerLedger',
    component: GeneralLedger,
    meta: { title: 'Customer Ledger' },
  },
  {
    path: '/journal-contra',
    name: 'JournalContraEntry',
    component: JournalContraEntry,
    meta: { title: 'Contra Entry' },
  },
  {
    path: '/payment',
    name: 'Payment',
    component: PaymentV2,
    meta: { title: 'Payment / Receipt' },
  },
  {
    path: '/stock-reconciliation',
    name: 'StockReconciliation',
    component: StockReconciliation,
    meta: { title: 'Stock Recon' },
  },
  {
    path: '/Cashier-Management',
    name: 'CashierManagement',
    component: CashierManagement,
    meta: { title: 'Cashier Mgmt' },
  },
  {
    path: '/discount-rules',
    name: 'DiscountRule',
    component: DiscountRule,
    meta: { title: 'Discount Rules' },
  },
  {
    path: '/pricing-rules',
    redirect: '/discount-rules',
  },
  {
    path: '/purchase-order',
    name: 'PurchaseOrder',
    component: PurchaseOrder,
    meta: { title: 'Purchase Order' },
  },
  {
    path: '/sales-order',
    name: 'SalesOrderEntry',
    component: SalesOrder,
    meta: { title: 'Sales Order' },
  },
  {
    path: '/incentive-ledger',
    name: 'IncentiveLedger',
    component: IncentiveLedger,
    meta: { title: 'Incentives' },
  },
  {
    path: '/incentive-redeem',
    name: 'IncentiveRedeem',
    component: IncentiveRedeem,
    meta: { title: 'Incentive Redeem' },
  },
  {
    path: '/incentive-entry',
    name: 'IncentiveEntry',
    component: IncentiveEntry,
    meta: { title: 'Incentive Entry' },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: Reports,
    meta: { title: 'Reports' },
  },
  {
    path: '/store-sale-report',
    name: 'StoreSalesReport',
    component: StoreSalesReport,
    meta: { title: 'Store Sales' },
  },
  {
    path: '/cost-center-sale-report',
    name: 'CostCenterSalesReport',
    component: CostCenterSalesReport,
    meta: { title: 'Cost Center Sales' },
  },
  {
    path: '/stock-status-report',
    name: 'StockStatusReport',
    component: StockStatusReport,
    meta: { title: 'Stock Status' },
  },
  {
    path: '/stock-aging-report',
    name: 'StockAgingReport',
    component: StockAgingReport,
    meta: { title: 'Stock Aging' },
  },
  {
    path: '/outstanding-customers-report',
    name: 'OutstandingCustomersReport',
    component: OutstandingCustomersReport,
    meta: { title: 'Outstanding Customers' },
  },
  {
    path: '/ledger-sales-purchase-report',
    name: 'LedgerSalesPurchaseReport',
    component: LedgerSalesPurchaseReport,
    meta: { title: 'Ledger Sales & Purchase' },
  },
  {
    path: '/item-sales-summary',
    name: 'ItemSalesSummary',
    component: ItemSalesSummary,
    meta: { title: 'Item Sales Summary' },
  },
  {
    path: '/store-wise-item-sales',
    name: 'StoreWiseItemSales',
    component: StoreWiseItemSales,
    meta: { title: 'Store Wise Item Sales' },
  },
  {
    path: '/fast-moving-items',
    name: 'FastMovingItems',
    component: FastMovingItems,
    meta: { title: 'Fast Moving Items' },
  },
  {
    path: '/material-transfer-report',
    name: 'MaterialTransferReport',
    component: MaterialTransferReport,
    meta: { title: 'Material Transfer Report' },
  },
  {
    path: '/cashflow-report',
    name: 'CashflowReport',
    component: CashflowReport,
    meta: { title: 'Cashflow Report' },
  },
  {
    path: '/loading-receipt',
    name: 'LoadingReceipt',
    component: LoadingReceipt,
    meta: { title: 'Loading Receipt' },
  },
  {
    path: '/customer-enquiry',
    name: 'CustomerEnquiry',
    component: CustomerEnquiry,
    meta: { title: 'Customer Enquiry' },
  },
  {
    path: '/parcel-address',
    name: 'ParcelAddress',
    component: ParcelAddress,
    meta: { title: 'Parcel Address' },
  },
  {
    path: '/gst-dummy-ledger',
    name: 'GstDummyLedger',
    component: GstDummyLedger,
    meta: { title: 'GST Dummy' },
  },
  {
    path: '/gst-ledger',
    name: 'GstLedger',
    component: GstLedger,
    meta: { title: 'GST Ledger' },
  },
  {
    path: '/catalogue/:pageaddress',
    name: 'OfferPage',
    component: OfferPage,
    meta: { public: true, title: 'Offers' },
  },
  {
    path: '/catalougepage/:pageaddress',
    name: 'CatalougePage',
    component: CatalougePage,
    meta: { public: true, title: 'Catalogue' },
  },
  {
    path: '/catalogueviewer',
    name: 'CatalogueViewer',
    component: CatalogueViewer,
    meta: { public: true, title: 'Catalogue Viewer' },
  },
  {
    path: '/catalogue-cart',
    name: 'CatalogueCart',
    component: CatalogueCart,
    meta: { public: true, title: 'Catalogue Cart' },
  },
  {
    path: '/catalogue-checkout',
    name: 'CatalogueCheckout',
    component: CatalogueCheckout,
    meta: { public: true, title: 'Catalogue Checkout' },
  },
  {
    path: '/displaycatalogue',
    name: 'Catelogue',
    component: Catelogue,
    meta: { public: true, title: 'Catalogue' },
  },
  {
    path: '/unreconciled',
    name: 'Unreconciled',
    component: Unreconciled,
    meta: { title: 'Unreconciled Entries' },
  },
  {
    path: '/cheques',
    name: 'ChequeRegister',
    component: ChequeRegister,
    meta: { title: 'Cheque Register' },
  },
  {
    path: '/account-tree',
    name: 'AccountTree',
    component: AccountTree,
    meta: { title: 'Chart of Accounts' },
  },
  {
    path: '/batch-reports',
    name: 'BatchReports',
    component: BatchReports,
    meta: { title: 'Batch Reports' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(
    import.meta.env.DEV
      ? '/'
      : window.location.pathname.startsWith('/catalogue/') || window.location.pathname.startsWith('/displaycatalogue')
      ? '/'
      : '/frontend'
  ),
  routes,
})

router.beforeEach(async (to, from, next) => {
  if (to.meta.public) {
    next()
    return
  }
  try {
    await session.init()
    if (!session.isLoggedIn.value) {
      next({ name: 'Login' })
      return
    }
    if (await session.checkWebsiteUser()) {
      next({ name: 'CatalogueViewer' })
      return
    }
    await initTabSession()
    if (!canAccessRoute(to.name)) {
      next({ name: 'Dashboard' })
      return
    }
    next()
  } catch (e) {
    next({ name: 'Login' })
  }
})

// Pages load lazily, and billing tabs outlive deploys that delete old chunks. When a page chunk is
// gone, hard-load the target once so the tab picks up the new build; the key prevents a reload loop.
const CHUNK_RELOAD_KEY = 'wb-chunk-reload'
router.onError((error, to) => {
  const message = String(error?.message || '')
  if (!/dynamically imported module|Importing a module script failed/i.test(message)) return
  const target = to ? router.resolve(to.fullPath).href : window.location.href
  if (sessionStorage.getItem(CHUNK_RELOAD_KEY) === target) return
  sessionStorage.setItem(CHUNK_RELOAD_KEY, target)
  window.location.assign(target)
})

router.afterEach((to) => {
  sessionStorage.removeItem(CHUNK_RELOAD_KEY)
  const title = to.meta.title || 'Billing'
  document.title = title
})

export default router
