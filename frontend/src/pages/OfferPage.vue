<template>
  <div class="min-h-screen flex flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] antialiased selection:bg-[var(--color-info)] selection:text-white">
    <!-- Loading Screen -->
    <div v-if="loading" class="flex-1 flex flex-col items-center justify-center p-8">
      <div class="relative w-16 h-16 mb-4">
        <div class="absolute inset-0 rounded-full border-4 border-[var(--color-info)]/20"></div>
        <div class="absolute inset-0 rounded-full border-4 border-t-[var(--color-info)] animate-spin"></div>
      </div>
      <div class="text-sm font-medium text-[var(--color-text-muted)] animate-pulse">Loading offers...</div>
    </div>

    <!-- Error / Not Found Screen -->
    <div v-else-if="error || !offer" class="flex-1 flex flex-col items-center justify-center p-8 text-center max-w-md mx-auto">
      <div class="text-6xl mb-6">🏷️</div>
      <h2 class="text-2xl font-bold text-[var(--color-text)] mb-2">Offer List Not Found</h2>
      <p class="text-sm text-[var(--color-text-muted)] leading-relaxed mb-6">
        We couldn't find any active offer items at this address. The link may have expired or contains a typo.
      </p>
      <button
        @click="goHome"
        class="rounded-xl bg-[var(--color-info)] px-6 py-2.5 text-xs font-bold text-white hover:bg-[var(--color-info)]/90 transition shadow-lg active:scale-95"
      >
        Go to Home
      </button>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Premium Hero Header -->
      <header class="relative overflow-hidden bg-gradient-to-br from-indigo-900 via-slate-900 to-black text-white px-6 py-12 md:py-16 text-center border-b border-[var(--color-border)] shrink-0">
        <!-- Abstract glowing circles -->
        <div class="absolute -top-12 -left-12 w-48 h-48 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-16 -right-16 w-64 h-64 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none"></div>
        
        <div class="max-w-4xl mx-auto relative z-10 space-y-4">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase tracking-wider">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
            Active Offers
          </div>
          <h1 class="text-3xl md:text-5xl font-black tracking-tight leading-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-100 to-emerald-200">
            {{ offer.heading }}
          </h1>
          <p class="text-xs md:text-sm text-slate-400 max-w-xl mx-auto font-medium">
            Explore our curated list of items on discount. Check out the barcodes or codes below to claim the deals.
          </p>
        </div>
      </header>

      <!-- Items Grid Section -->
      <main class="flex-1 max-w-7xl w-full mx-auto px-6 py-10">
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          <div
            v-for="item in offer.items"
            :key="item.itemcode"
            class="group relative flex flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            <!-- Image / Placeholder Frame -->
            <div class="relative aspect-square w-full bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4 border-b border-[var(--color-border)]/50 overflow-hidden shrink-0">
              <!-- Stacked Offer Badges Overlay -->
              <div v-if="item.discount_type && item.discount_desc" class="absolute top-3 left-3 flex flex-col gap-1 z-10 items-start pointer-events-none">
                <span class="text-[8px] uppercase font-black bg-[var(--color-warning)] text-black px-1.5 py-0.5 rounded shadow-sm">
                  Offer
                </span>
                <span 
                  v-for="(line, lIdx) in item.discount_desc.split(' | ')" 
                  :key="lIdx"
                  class="font-bold text-[9px] bg-slate-900/95 text-[var(--color-warning)] border border-[var(--color-warning)]/30 px-2 py-0.5 rounded shadow-md backdrop-blur-sm whitespace-nowrap"
                >
                  {{ line }}
                </span>
              </div>

              <img
                v-if="item.image"
                :src="item.image"
                :alt="item.itemname"
                class="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
              />
              <!-- Premium placeholder if no image exists -->
              <div
                v-else
                class="w-full h-full rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-900 dark:to-slate-800 flex flex-col items-center justify-center text-center p-4 select-none"
              >
                <div class="text-3xl mb-2 group-hover:scale-110 transition-transform duration-300">📦</div>
                <span class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  No Image Available
                </span>
              </div>
            </div>

            <!-- Card Details -->
            <div class="flex-1 p-5 flex flex-col justify-between gap-4">
              <div class="space-y-1.5">
                <h3 class="font-bold text-[14px] text-[var(--color-text)] line-clamp-2 leading-snug group-hover:text-[var(--color-info)] transition-colors" :title="item.itemname">
                  {{ item.itemname }}
                </h3>
                <div class="flex items-center gap-1.5 text-[11px] text-[var(--color-text-muted)] font-mono">
                  <span class="bg-[var(--color-midlight)] px-1.5 py-0.5 rounded">Code</span>
                  <span>{{ item.itemcode }}</span>
                </div>
              </div>

              <div class="space-y-2 shrink-0">
                <!-- Barcode Badge -->
                <div v-if="item.barcode" class="pt-2 border-t border-[var(--color-border)]/40 flex items-center justify-between">
                  <span class="text-[10px] uppercase font-bold text-[var(--color-text-muted)] tracking-wider">Barcode</span>
                  <span class="font-mono text-xs font-bold bg-[var(--color-info)]/10 text-[var(--color-info)] px-2 py-0.5 rounded-full select-all">
                    {{ item.barcode }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </template>

    <!-- Footer -->
    <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)]/50 py-6 px-6 text-center text-[10px] text-[var(--color-text-muted)] shrink-0">
      <div class="max-w-4xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-2">
        <span>© {{ new Date().getFullYear() }} Sundaram and Sons Private Ltd.</span>
        <span>Keyboard Fast wholesale Billing system</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { frappeGet } from '../api.js'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref(null)
const offer = ref(null)

const pageaddress = computedRouteParam()

function computedRouteParam() {
  return route.params.pageaddress
}

async function loadOffer() {
  if (!pageaddress) {
    loading.value = false
    error.value = 'Invalid page address'
    return
  }

  loading.value = true
  error.value = null
  try {
    const res = await frappeGet('ssplbilling.api.offer_api.get_offer_details', {
      pageaddress: pageaddress
    })
    
    if (res) {
      offer.value = res
      document.title = `${res.heading} | Deals`
    } else {
      error.value = 'Offer not found'
    }
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Failed to load offers'
  } finally {
    loading.value = false
  }
}

function goHome() {
  router.push('/')
}

onMounted(() => {
  loadOffer()
})
</script>

<style scoped>
/* Core stylesheet variables integrated */
</style>
