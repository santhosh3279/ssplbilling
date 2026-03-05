import { createRouter, createWebHistory } from 'vue-router'
import { session } from './session'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
import SalesEntry from './pages/SalesEntry.vue'
import CashierEntry from './pages/CashierEntry.vue'
import CustomerLedger from './pages/CustomerLedger.vue'
import PaymentEntry from './pages/PaymentEntry.vue'

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
    path: '/cashier',
    name: 'CashierEntry',
    component: CashierEntry,
  },
  {
    path: '/ledger',
    name: 'CustomerLedger',
    component: CustomerLedger,
  },
  {
    path: '/payment',
    name: 'PaymentEntry',
    component: PaymentEntry,
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
