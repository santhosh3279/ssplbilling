import { createRouter, createWebHistory } from 'vue-router'
import { session } from './session'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
import SalesEntry from './pages/SalesEntry.vue'
import PurchaseEntry from './pages/PurchaseEntry.vue'
import PriceListUpdate from './pages/PriceListUpdate.vue'
import Cashierpage from './pages/Cashierpage.vue'
import CustomerLedger from './pages/CustomerLedger.vue'
import PaymentReceiptEntry from './pages/PaymentReceiptEntry.vue'

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
    path: '/cashier',
    name: 'Cashierpage',
    component: Cashierpage,
  },
  {
    path: '/ledger',
    name: 'CustomerLedger',
    component: CustomerLedger,
  },
  {
    path: '/payment',
    name: 'PaymentReceiptEntry',
    component: PaymentReceiptEntry,
  },
]

const router = createRouter({
  history: createWebHistory('/frontend'),
  routes,
})

router.beforeEach(async (to, from, next) => {
  if (to.meta.public) {
    next()
    return
  }
  try {
    await session.init()
    if (session.isLoggedIn.value) {
      next()
    } else {
      next({ name: 'Login' })
    }
  } catch (e) {
    next({ name: 'Login' })
  }
})

export default router
