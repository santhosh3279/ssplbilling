import { createRouter, createWebHistory } from 'vue-router'
import { session } from './session'
import { canAccessRoute } from './composables/usePermission'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
import SalesInvoice from './pages/SalesInvoice.vue'
import Quotation from './pages/Quotation.vue'
import PurchaseInvoice from './pages/PurchaseInvoice.vue'
import PriceListUpdate from './pages/PriceListUpdate.vue'
import BarcodePrintPage from './pages/BarcodePrintPage.vue'
import CashierDesk from './pages/CashierDesk.vue'
import PurchaseSubmit from './pages/PurchaseSubmit.vue'
import GeneralLedger from './pages/GeneralLedger.vue'
import Payment from './pages/Payment.vue'
import PaymentV2 from './pages/paymentv2.vue'
import JournalContraEntry from './pages/JournalContraEntry.vue'
import CashierManagement from './pages/CashierManagement.vue'
import PricingRuleSync from './pages/PricingRuleSync.vue'
import PurchaseOrder from './pages/PurchaseOrder.vue'
import SalesOrderEntry from './pages/SalesOrderEntry.vue'
import SalesOrder from './pages/SalesOrder.vue'
import IncentiveLedger from './pages/IncentiveLedger.vue'
import Reports from './pages/Reports.vue'
import StoreSalesReport from './pages/StoreSalesReport.vue'
import LoadingReceipt from './pages/LoadingReceipt.vue'
import ParcelAddress from './pages/ParcelAddress.vue'
import StockReconciliation from './pages/StockReconciliation.vue'
import SSPLBillingSettings from './pages/SSPLBillingSettings.vue'
import GstDummyLedger from './pages/GstDummyLedger.vue'
import GstLedger from './pages/GstLedger.vue'
import DailyReport from './pages/DailyReport.vue'
import StoreTransfer from './pages/StoreTransfer.vue'
import SingleEntry from './pages/SingleEntry.vue'
import Cancellation from './pages/Cancellation.vue'
import PartyLink from './pages/PartyLink.vue'
import NamingSettings from './pages/NamingSettings.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true, title: 'Login' },
  },
  {
    path: '/naming-settings',
    name: 'NamingSettings',
    component: NamingSettings,
    meta: { title: 'Naming Settings' },
  },
  {
    path: '/party-link',
    name: 'PartyLink',
    component: PartyLink,
    meta: { title: 'Party Link' },
  },
  {
    path: '/cancellation',
    name: 'Cancellation',
    component: Cancellation,
    meta: { title: 'Cancellation' },
  },
  {
    path: '/single-entry',
    name: 'SingleEntry',
    component: SingleEntry,
    meta: { title: 'Bulk Payment' },
  },
  {
    path: '/store-transfer',
    name: 'StoreTransfer',
    component: StoreTransfer,
    meta: { title: 'Store Transfer' },
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
    component: Payment,
    meta: { title: 'Payment / Receipt' },
  },
  {
    path: '/paymentv2',
    name: 'PaymentV2',
    component: PaymentV2,
    meta: { title: 'Payment / Receipt V2' },
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
    path: '/pricing-rules',
    name: 'PricingRuleSync',
    component: PricingRuleSync,
    meta: { title: 'Pricing Rules' },
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
    path: '/loading-receipt',
    name: 'LoadingReceipt',
    component: LoadingReceipt,
    meta: { title: 'Loading Receipt' },
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
]

const router = createRouter({
  history: createWebHistory(import.meta.env.DEV ? '/' : '/frontend'),
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
    if (!canAccessRoute(to.name)) {
      next({ name: 'Dashboard' })
      return
    }
    next()
  } catch (e) {
    next({ name: 'Login' })
  }
})

router.afterEach((to) => {
  const title = to.meta.title || 'Billing'
  document.title = title
})

export default router
