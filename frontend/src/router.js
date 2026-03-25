import { createRouter, createWebHistory } from 'vue-router'
import { session } from './session'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
import SalesEntry from './pages/SalesEntry.vue'
import QuotationEntry from './pages/QuotationEntry.vue'
import PurchaseEntry from './pages/PurchaseEntry.vue'
import PriceListUpdate from './pages/PriceListUpdate.vue'
import BarcodePrintPage from './pages/BarcodePrintPage.vue'
import CashierDesk from './pages/CashierDesk.vue'
import PurchaseSubmit from './pages/PurchaseSubmit.vue'
import CustomerLedger from './pages/CustomerLedger.vue'
import PayRec from './pages/PayRec.vue'
import JournalContraEntry from './pages/JournalContraEntry.vue'
import MaterialTransfer from './pages/MaterialTransfer.vue'
import CashierManagement from './pages/CashierManagement.vue'
import PricingRuleSync from './pages/PricingRuleSync.vue'
import PurchaseOrder from './pages/PurchaseOrder.vue'
import SalesOrderEntry from './pages/SalesOrderEntry.vue'
import IncentiveLedger from './pages/IncentiveLedger.vue'
import Reports from './pages/Reports.vue'
import StoreSalesReport from './pages/StoreSalesReport.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/sales',
    name: 'SalesEntry',
    component: SalesEntry,
  },
  {
    path: '/quotation',
    name: 'QuotationEntry',
    component: QuotationEntry,
  },
  {
    path: '/purchase',
    name: 'PurchaseEntry',
    component: PurchaseEntry,
  },
  {
    path: '/pricelist-update',
    name: 'PriceListUpdate',
    component: PriceListUpdate,
  },
  {
    path: '/barcode-print',
    name: 'BarcodePrintPage',
    component: BarcodePrintPage,
  },
  {
    path: '/cashier',
    name: 'CashierDesk',
    component: CashierDesk,
    meta: { requiresOpening: true },
  },
  {
    path: '/purchase-submit',
    name: 'PurchaseSubmit',
    component: PurchaseSubmit,
  },
  {
    path: '/ledger',
    name: 'CustomerLedger',
    component: CustomerLedger,
  },
  {
    path: '/journal-contra',
    name: 'JournalContraEntry',
    component: JournalContraEntry,
  },
  {
    path: '/payment',
    name: 'PayRec',
    component: PayRec,
  },
  {
    path: '/material-transfer',
    name: 'MaterialTransfer',
    component: MaterialTransfer,
  },
  {
    path: '/Cashier-Management',
    name: 'CashierManagement',
    component: CashierManagement,
  },
  {
    path: '/pricing-rules',
    name: 'PricingRuleSync',
    component: PricingRuleSync,
  },
  {
    path: '/purchase-order',
    name: 'PurchaseOrder',
    component: PurchaseOrder,
  },
  {
    path: '/sales-order',
    name: 'SalesOrderEntry',
    component: SalesOrderEntry,
  },
  {
    path: '/incentive-ledger',
    name: 'IncentiveLedger',
    component: IncentiveLedger,
  },
  {
    path: '/reports',
    name: 'Reports',
    component: Reports,
  },
  {
    path: '/store-sale-report',
    name: 'StoreSalesReport',
    component: StoreSalesReport,
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
    next()
  } catch (e) {
    next({ name: 'Login' })
  }
})

export default router
