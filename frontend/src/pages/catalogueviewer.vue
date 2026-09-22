<template>
  <div class="min-h-screen overflow-y-auto flex flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] antialiased">
    <!-- Premium Hero Header -->
    <header class="relative overflow-hidden bg-gradient-to-br from-indigo-900 via-slate-900 to-black text-white px-6 text-center border-b border-[var(--color-border)] shrink-0 h-[20vh] min-h-[140px] flex items-center justify-center">
      <a
        href="https://www.chettiyarkada.in"
        class="absolute top-4 left-4 z-20 flex items-center gap-2 rounded-xl bg-slate-950/60 hover:bg-slate-900/80 px-4 py-2 text-xs font-bold text-slate-300 hover:text-white border border-slate-800/50 transition active:scale-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-white"
      >
        ← Back
      </a>

      <div v-if="isLoggedIn" class="absolute top-4 right-4 z-20 flex items-center gap-3 rounded-xl bg-slate-950/60 px-4 py-2 text-xs text-white border border-slate-800/50">
        <span class="max-w-40 truncate font-semibold">{{ userName }}</span>

        <!-- Selected Customer & Price list for System Users (clicking opens customer search to modify) -->
        <button
          v-if="session.isSystemUser.value && orderContext.customer"
          type="button"
          @click="toggleCustomerSection"
          class="flex items-center gap-1.5 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/35 border border-indigo-400/40 px-2.5 py-1 text-xs text-indigo-100 hover:text-white transition cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-white"
          title="Click to modify customer and price list"
        >
          <span class="font-bold text-white max-w-[180px] truncate">
            {{ orderContext.customer_name || orderContext.customer }}
          </span>
          <span class="text-indigo-300 text-[11px] truncate max-w-[120px]">
            ({{ orderContext.price_list }})
          </span>
          <span class="text-[11px] text-indigo-300 ml-0.5">✏️</span>
        </button>
        <button
          v-else-if="session.isSystemUser.value"
          type="button"
          @click="toggleCustomerSection"
          class="flex items-center gap-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/35 border border-amber-400/40 px-2.5 py-1 text-xs text-amber-200 hover:text-white transition cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-white"
          title="Click to select customer and price list"
        >
          <span class="font-bold">Select Customer</span>
          <span class="text-[11px]">🔍</span>
        </button>

        <RouterLink v-if="catalogueUser" to="/catalogue-cart" class="font-bold text-indigo-200 hover:text-white">Cart ({{ cartCount }})</RouterLink>
        <button type="button" @click="logout" class="font-bold text-indigo-200 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-white">Logout</button>
      </div>
      <button v-else type="button" @click="showLogin = true" class="absolute top-4 right-4 z-20 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg hover:bg-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-white">
        Login
      </button>

      <!-- Abstract glowing circles -->
      <div class="absolute -top-12 -left-12 w-48 h-48 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-16 -right-16 w-64 h-64 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none"></div>

      <div class="max-w-4xl mx-auto relative z-10 space-y-2">
        <div class="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[9px] font-bold uppercase tracking-wider">
          📦 Catalogues
        </div>
        <h1 class="text-xl md:text-3xl font-black tracking-tight leading-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-100 to-emerald-200">
          Sundaram and Sons Catalogues
        </h1>
        <p class="text-[10px] md:text-xs text-slate-400 max-w-xl mx-auto font-medium">
          Select a catalogue below to view items on discount, barcodes, prices, and play slideshow presentations.
        </p>
      </div>
    </header>

    <div v-if="showLogin" class="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4" @click.self="showLogin = false">
      <form class="w-full max-w-sm space-y-4 rounded-xl bg-[var(--color-surface)] p-6 text-[var(--color-text)] shadow-xl" @submit.prevent="handleWebsiteLogin">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-bold">Login</h2>
          <button type="button" aria-label="Close login" @click="showLogin = false">✕</button>
        </div>
        <p v-if="loginError" role="alert" class="text-sm text-red-600">{{ loginError }}</p>
        <label class="block text-sm font-medium">Email or Username
          <input v-model.trim="loginEmail" type="text" autocomplete="username" required class="mt-1 w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2" />
        </label>
        <label class="block text-sm font-medium">Password
          <input v-model="loginPassword" type="password" autocomplete="current-password" required class="mt-1 w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2" />
        </label>
        <button type="submit" :disabled="loginLoading" class="w-full rounded bg-indigo-600 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">
          {{ loginLoading ? 'Signing in…' : 'Sign In' }}
        </button>
      </form>
    </div>

    <CatalogueOrderParty
      v-if="session.isSystemUser.value && showCustomerSection"
      @applied="onCustomerApplied"
      @close="showCustomerSection = false"
    />
    <!-- Main Content Area -->
    <main class="flex-1 w-full px-6 py-12" :class="catalogueUser && cartCount ? 'lg:pr-[21rem]' : ''">
      <section class="mb-8 space-y-4" aria-label="Search catalogue items">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <label for="catalogue-item-search" class="block text-lg font-bold">
            {{ session.isSystemUser.value && includeAllItems ? 'Find any item to add to your cart' : 'Find catalogue items to add to your cart' }}
          </label>

          <!-- Toggle button: Only for System Users -->
          <div
            v-if="session.isSystemUser.value"
            class="inline-flex rounded-xl bg-[var(--color-surface)] p-1 border border-[var(--color-border)] shadow-sm shrink-0"
            role="group"
            aria-label="Item search filter"
          >
            <button
              type="button"
              @click="includeAllItems = false"
              class="px-3 py-1.5 text-xs font-bold rounded-lg transition-all cursor-pointer"
              :class="!includeAllItems ? 'bg-indigo-600 text-white shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              📖 Catalogue Items
            </button>
            <button
              type="button"
              @click="includeAllItems = true"
              class="px-3 py-1.5 text-xs font-bold rounded-lg transition-all cursor-pointer"
              :class="includeAllItems ? 'bg-indigo-600 text-white shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              📦 All Items
            </button>
          </div>
        </div>

        <div class="flex gap-2">
          <input
            id="catalogue-item-search"
            v-model="itemQuery"
            type="search"
            maxlength="100"
            :placeholder="session.isSystemUser.value && includeAllItems ? 'Search all items by item name, code or barcode' : 'Search catalogue items by item name, code or barcode'"
            class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-[var(--color-text)]"
          />
          <button v-if="itemQuery" type="button" class="rounded-xl border border-[var(--color-border)] px-4 cursor-pointer" @click="itemQuery = ''">Clear</button>
        </div>
        <p v-if="searchLoading" role="status">Searching items…</p>
        <p v-if="searchError" role="alert" class="text-[var(--color-danger)]">{{ searchError }} <button type="button" class="underline" @click="searchItems()">Try Again</button></p>
        <p v-else-if="itemQuery.trim() && !searchLoading && !searchResults.length" role="status">No matching catalogue items.</p>
        <div v-if="searchResults.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <article v-for="item in searchResults" :key="JSON.stringify([item.pageaddress || '', item.item_code, item.barcode])" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 space-y-2">
            <h2 class="font-bold">{{ item.item_name }}</h2>
            <p class="text-sm text-[var(--color-text-muted)]">{{ item.item_code }} <span v-if="item.barcode">· {{ item.barcode }}</span></p>
            <button v-if="item.pageaddress" type="button" class="text-sm text-[var(--color-info)] underline text-left" @click="openCatalogue(item.pageaddress)">{{ item.heading }}</button>
            <span v-else class="inline-block text-[11px] px-2 py-0.5 rounded-md bg-slate-800/20 text-[var(--color-text-muted)] border border-[var(--color-border)]">Non-catalogue item</span>
            <p class="text-sm">Available stock: {{ item.available_stock == null ? 'Unavailable' : item.available_stock + ' ' + item.stock_uom }}</p>
            <template v-if="catalogueUser">
              <p v-if="session.isSystemUser.value" class="text-xs">Price list: {{ orderContext.price_list || 'Select customer & price list in header' }}</p>
              <p>{{ item.order_rate == null ? 'Price unavailable' : priceFormatter.format(item.order_rate) + ' / ' + item.order_uom }}</p>
              <div class="flex items-center gap-2 border-t border-[var(--color-border)]/40 pt-3">
                <template v-if="item.order_rate != null">
                  <button
                    type="button"
                    :aria-label="`Decrease ${item.item_name}`"
                    class="rounded-lg border px-3 py-1 font-bold transition-colors border-rose-500/40 bg-rose-500/15 text-[var(--color-text)] shadow-sm hover:bg-rose-500/25 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-500 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
                    :disabled="!getQuantity(item.pageaddress || '', item.item_code)"
                    @click="adjustQuantity(item, -1)"
                  >
                    −
                  </button>
                  <input
                    type="text"
                    inputmode="numeric"
                    pattern="[0-9]*"
                    maxlength="5"
                    :aria-label="`Quantity for ${item.item_name}`"
                    :value="getQuantity(item.pageaddress || '', item.item_code)"
                    class="w-16 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-1 text-center font-bold text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-indigo-400"
                    @focus="$event.target.select()"
                    @change="setItemQuantity(item, $event)"
                    @keydown.enter="$event.target.blur()"
                  />
                  <button
                    type="button"
                    :aria-label="`Increase ${item.item_name}`"
                    class="rounded-lg border px-3 py-1 font-bold transition-colors border-emerald-500/40 bg-emerald-500/15 text-[var(--color-text)] shadow-sm hover:bg-emerald-500/25 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
                    :disabled="getQuantity(item.pageaddress || '', item.item_code) >= 10000"
                    @click="adjustQuantity(item, 1)"
                  >
                    +
                  </button>
                  <span v-if="getQuantity(item.pageaddress || '', item.item_code)" class="text-xs text-[var(--color-text-muted)] ml-1">in cart</span>
                </template>
                <span v-else class="text-xs text-[var(--color-text-muted)]">Price unavailable</span>
              </div>
            </template>
            <button v-else type="button" class="rounded bg-indigo-600 px-4 py-2 font-bold text-white" @click="showLogin = true">Sign in to add to cart</button>
          </article>
        </div>
        <button v-if="searchHasMore && !searchError" type="button" :disabled="searchLoading" class="text-[var(--color-info)] underline disabled:opacity-50" @click="searchItems(true)">Load more items</button>
      </section>

      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-16">
        <div class="relative w-16 h-16 mb-4">
          <div class="absolute inset-0 rounded-full border-4 border-[var(--color-info)]/20"></div>
          <div class="absolute inset-0 rounded-full border-4 border-t-[var(--color-info)] animate-spin"></div>
        </div>
        <div class="text-sm font-medium text-[var(--color-text-muted)] animate-pulse">Loading catalogues...</div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-16 max-w-md mx-auto space-y-4">
        <div class="text-5xl">⚠️</div>
        <h3 class="text-xl font-bold text-[var(--color-text)]">Failed to Load Catalogues</h3>
        <p class="text-xs text-[var(--color-text-muted)]">{{ error }}</p>
        <button
          @click="fetchCatalogues"
          class="rounded-xl bg-[var(--color-info)] px-6 py-2.5 text-xs font-bold text-white hover:bg-[var(--color-info)]/90 transition shadow-lg active:scale-95"
        >
          Try Again
        </button>
      </div>

      <!-- Empty State -->
      <div v-else-if="!catalogues.length" class="text-center py-16 max-w-md mx-auto space-y-4">
        <div class="text-6xl">🏷️</div>
        <h3 class="text-xl font-bold text-[var(--color-text)]">No Active Catalogues</h3>
        <p class="text-xs text-[var(--color-text-muted)]">Currently, there are no published catalogues available.</p>
      </div>

      <!-- Catalogues Grid -->
      <div v-else class="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        <div
          v-for="cat in catalogues"
          :key="cat.name"
          @click="openCatalogue(cat.pageaddress)"
          class="catalogue-card group relative flex flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3.5 shadow-md hover:shadow-2xl hover:border-[var(--color-info)]/60 cursor-pointer transition-all duration-300 transform hover:-translate-y-1"
        >
          <!-- Accent Light Border Top Glow -->
          <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

          <div class="flex-1 space-y-2">
            <!-- Icon and Active Items -->
            <div class="flex items-center justify-between">
              <span class="card-icon text-3xl">📖</span>
              <span class="card-item-count text-[10px] font-bold text-[var(--color-text-muted)]">
                {{ cat.item_count ?? 0 }} active {{ cat.item_count === 1 ? 'item' : 'items' }}
              </span>
            </div>

            <!-- Title -->
            <div class="space-y-1.5">
              <h3 class="card-heading text-lg font-black text-[var(--color-text)] group-hover:text-[var(--color-info)] transition-colors line-clamp-2">
                {{ cat.heading }}
              </h3>
            </div>
          </div>

          <!-- Bottom Action indicator -->
          <div class="card-action mt-3.5 pt-2 border-t border-[var(--color-border)]/40 flex items-center justify-between text-xs font-bold text-[var(--color-info)] group-hover:translate-x-1 transition-transform duration-300">
            <span>View Catalogue</span>
            <span>→</span>
          </div>
        </div>
      </div>
    </main>

    <CatalogueCartPanel v-if="catalogueUser" />

    <!-- Footer -->
    <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)]/50 py-6 px-6 text-center text-[10px] text-[var(--color-text-muted)] shrink-0 mt-auto">
      <div class="max-w-4xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-2">
        <span>© {{ new Date().getFullYear() }} Sundaram and Sons Private Ltd.</span>
        <span>Keyboard Fast wholesale Billing system</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { frappeGet } from '../api.js'
import { session } from '../session.js'
import { cartCount, setCartUser, getQuantity, setQuantity } from '../services/catalogueCart.js'
import CatalogueCartPanel from '../components/CatalogueCartPanel.vue'
import CatalogueOrderParty from '../components/CatalogueOrderParty.vue'
import { orderContext, orderParams } from '../services/catalogueOrderContext.js'

const router = useRouter()
const isLoggedIn = session.isLoggedIn
const isWebsiteUser = session.isWebsiteUser
const catalogueUser = computed(() => isWebsiteUser.value || session.isSystemUser.value)
const userName = computed(() => session.fullName.value || session.user.value)
const showLogin = ref(false)
const loginEmail = ref('')
const loginPassword = ref('')
const loginError = ref('')
const loginLoading = ref(false)

const showCustomerSection = ref(!orderContext.value.customer)

watch(() => orderContext.value.customer, (newCust, oldCust) => {
  if (!oldCust && newCust) {
    showCustomerSection.value = false
  } else if (!newCust) {
    showCustomerSection.value = true
  }
})

function toggleCustomerSection() {
  showCustomerSection.value = !showCustomerSection.value
}

function onCustomerApplied() {
  showCustomerSection.value = false
}

const loading = ref(true)
const error = ref(null)
const catalogues = ref([])
const itemQuery = ref('')
const includeAllItems = ref(false)
const searchResults = ref([])
const searchLoading = ref(false)
const searchError = ref('')
const searchHasMore = ref(false)
const priceFormatter = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })
let searchTimer = null
let searchRequest = 0

async function searchItems(append = false) {
  clearTimeout(searchTimer)
  const query = itemQuery.value.trim()
  const request = ++searchRequest
  if (!append) searchResults.value = []
  searchError.value = ''
  if (!query) {
    searchLoading.value = false
    searchHasMore.value = false
    return
  }
  searchLoading.value = true
  try {
    const all_items = session.isSystemUser.value && includeAllItems.value ? 1 : 0
    const result = await frappeGet('ssplbilling.api.catalogue_order_api.search_catalogue_items', {
      ...orderParams(),
      query,
      all_items,
      start: append ? searchResults.value.length : 0
    })
    if (request !== searchRequest) return
    searchResults.value = append ? [...searchResults.value, ...result.items] : result.items
    searchHasMore.value = result.has_more
  } catch (error) {
    if (request === searchRequest) searchError.value = error.message || 'Could not search items.'
  } finally {
    if (request === searchRequest) searchLoading.value = false
  }
}

watch([itemQuery, catalogueUser, orderContext, includeAllItems], () => {
  ++searchRequest
  clearTimeout(searchTimer)
  searchResults.value = []
  searchHasMore.value = false
  searchError.value = ''
  searchLoading.value = !!itemQuery.value.trim()
  if (searchLoading.value) searchTimer = setTimeout(() => searchItems(), 300)
})

function setItemQuantity(item, event) {
  if (!catalogueUser.value || item.order_rate == null) return
  const value = event.target.value.trim()
  const pageaddr = item.pageaddress || ''
  if (/^\d+$/.test(value) && Number(value) <= 10000) {
    setQuantity(pageaddr, item.item_code, Number(value))
    if (getQuantity(pageaddr, item.item_code) !== Number(value)) {
      searchError.value = 'Could not update the cart. It supports up to 100 items and 10,000 units per item.'
    }
  }
  event.target.value = getQuantity(pageaddr, item.item_code)
}

function adjustQuantity(item, delta) {
  if (!catalogueUser.value || (delta > 0 && item.order_rate == null)) return
  const pageaddr = item.pageaddress || ''
  const current = getQuantity(pageaddr, item.item_code)
  const next = Math.max(0, current + delta)
  setQuantity(pageaddr, item.item_code, next)
  if (getQuantity(pageaddr, item.item_code) !== next) {
    searchError.value = 'Could not update the cart. It supports up to 100 items and 10,000 units per item.'
  }
}

const changeCartQuantity = adjustQuantity

onBeforeUnmount(() => {
  ++searchRequest
  clearTimeout(searchTimer)
})

async function fetchCatalogues() {
  loading.value = true
  error.value = null
  try {
    const res = await frappeGet('ssplbilling.api.offer_api.get_offer_list')
    if (res) {
      catalogues.value = res
    } else {
      catalogues.value = []
    }
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Failed to fetch catalogues'
  } finally {
    loading.value = false
  }
}

function openCatalogue(pageaddress) {
  router.push({ name: 'CatalougePage', params: { pageaddress } })
}

async function logout() {
  await session.logout()
  setCartUser(null)
}

async function handleWebsiteLogin() {
  loginError.value = ''
  loginLoading.value = true
  let signedIn = false
  try {
    await session.login(loginEmail.value, loginPassword.value)
    signedIn = true
    await session.checkWebsiteUser()
    if (!catalogueUser.value) {
      await session.logout()
      loginError.value = 'Sign in with a Website User or System User account.'
      return
    }
    setCartUser(session.user.value)
    loginPassword.value = ''
    showLogin.value = false
  } catch (err) {
    if (signedIn) await session.logout()
    loginError.value = err.message || 'Could not sign in.'
  } finally {
    loginLoading.value = false
  }
}

onMounted(() => {
  session.checkWebsiteUser().then(() => {
    if (catalogueUser.value) setCartUser(session.user.value)
  }).catch((err) => console.warn('[catalogueviewer] Session check failed:', err))
  fetchCatalogues()
})
</script>

<style scoped>
.catalogue-card {
  font-size: 26px !important;
}
.catalogue-card .card-item-count {
  font-size: 20px !important;
}
.catalogue-card .card-heading {
  font-size: 27px !important;
}
.catalogue-card .card-badge {
  font-size: 18px !important;
}
.catalogue-card .card-action {
  font-size: 24px !important;
}
.catalogue-card .card-icon {
  font-size: 40px !important;
}
</style>
