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
        <span class="max-w-40 truncate">{{ userName }}</span>
        <RouterLink v-if="isWebsiteUser" to="/catalogue-cart" class="font-bold text-indigo-200 hover:text-white">Cart ({{ cartCount }})</RouterLink>
        <button type="button" @click="logout" class="font-bold text-indigo-200 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-white">Logout</button>
      </div>

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

    <!-- Main Content Area -->
    <main class="flex-1 w-full px-6 py-12" :class="isWebsiteUser && cartCount ? 'lg:pr-[21rem]' : ''">
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

    <CatalogueCartPanel v-if="isWebsiteUser" />

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
import { ref, computed, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { frappeGet } from '../api.js'
import { session } from '../session.js'
import { cartCount, setCartUser } from '../services/catalogueCart.js'
import CatalogueCartPanel from '../components/CatalogueCartPanel.vue'

const router = useRouter()
const isLoggedIn = session.isLoggedIn
const isWebsiteUser = session.isWebsiteUser
const userName = computed(() => session.fullName.value || session.user.value)

const loading = ref(true)
const error = ref(null)
const catalogues = ref([])
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

onMounted(() => {
  session.checkWebsiteUser().then(() => {
    if (session.isWebsiteUser.value) setCartUser(session.user.value)
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
