<template>
  <div class="h-screen overflow-y-auto flex flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] antialiased selection:bg-[var(--color-info)] selection:text-white main-content-wrapper">
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
        ref="goHomeButtonRef"
        @click="goHome"
        class="rounded-xl bg-[var(--color-info)] px-6 py-2.5 text-xs font-bold text-white hover:bg-[var(--color-info)]/90 transition shadow-lg active:scale-95 focus:outline-none focus:ring-4 focus:ring-[var(--color-info)]/50 focus:scale-105"
      >
        Go to Home
      </button>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Presentation Mode Overlay (Fullscreen) -->
      <div v-if="isFullscreen" class="fixed inset-0 z-50 bg-slate-950 text-white font-sans overflow-hidden select-none">
        
        <!-- Main Cards Area (Circular slider layout - now stays above footer controls) -->
        <main class="absolute inset-0 w-full h-screen flex items-center justify-center overflow-hidden">
          <div class="relative w-full h-screen flex items-center justify-center">
            <div
              v-for="(item, idx) in offer.items"
              :key="item.itemcode"
              :style="getItemStyle(idx)"
              class="absolute flex flex-col bg-slate-900/90 shadow-2xl hover:border-indigo-500/50 transition-all duration-300 p-6 border border-slate-800/80 rounded-2xl justify-between"
            >
              <!-- Top side for offer -->
              <div class="shrink-0 flex items-start justify-start w-full mb-2">
                <div v-if="item.discount_type && item.discount_desc" class="bg-slate-950/95 border border-amber-500/40 rounded-lg overflow-hidden shadow-2xl backdrop-blur-sm w-full">
                  <div class="bg-amber-500 text-black text-[9px] font-black uppercase px-2 py-0.5 text-left tracking-wider">
                    Active Offer
                  </div>
                  <div class="p-1.5 flex flex-col gap-0.5 font-normal text-[20px] text-amber-400 whitespace-normal break-words leading-tight">
                    <div 
                      v-for="(line, lIdx) in item.discount_desc.split(' | ')" 
                      :key="lIdx"
                    >
                      {{ line }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Middle section for image (Normal size, no stretch) -->
              <div class="flex-1 flex items-center justify-center min-h-0 py-2">
                <img
                  v-if="item.image"
                  :src="item.image"
                  :alt="item.itemname"
                  class="max-w-full object-contain transition-all duration-500"
                  :class="showControls ? 'max-h-[35vh]' : 'max-h-[48vh]'"
                />
                <!-- Placeholder -->
                <div
                  v-else
                  class="w-full h-full min-h-[20vh] rounded-xl bg-gradient-to-br from-slate-950 to-slate-900 flex flex-col items-center justify-center text-center p-4 select-none border border-slate-800/30"
                >
                  <div class="text-3xl mb-1">📦</div>
                  <span class="text-[9px] font-bold uppercase tracking-wider text-slate-500">
                    No Image Available
                  </span>
                </div>
              </div>

              <!-- Bottom side for item details -->
              <div class="shrink-0 space-y-2 pt-3 border-t border-slate-800/60">
                <h3 
                  class="font-normal text-slate-100 line-clamp-2 leading-tight"
                  :class="presentationCols >= 6 ? 'text-[22px]' : 'text-2xl md:text-3xl'"
                >
                  {{ item.itemname }}
                </h3>
                
                <div 
                  v-if="presentationCols < 6 && item.barcode_prices && item.barcode_prices.length"
                  class="flex items-center justify-center pt-2 shrink-0"
                >
                  <div class="w-full max-w-xl bg-slate-950/40 rounded-xl p-3 border border-slate-800/40 shadow-inner">
                    <table class="w-full text-left text-2xl border-collapse">

                      <tbody class="divide-y divide-slate-900/50 font-medium">
                        <tr 
                          v-for="bp in item.barcode_prices" 
                          :key="bp.barcode"
                        >
                          <td class="py-0.5 pr-2 font-mono text-slate-200 select-all font-bold">
                            {{ bp.barcode || '—' }} <span v-if="bp.uom" class="text-slate-500 font-normal text-lg font-sans">({{ bp.uom }})</span>
                          </td>
                          <td 
                            v-for="pl in offer.price_lists" 
                            :key="pl.price_list"
                            class="py-0.5 px-0.5 font-mono text-right text-indigo-400 font-bold tracking-widest"
                          >
                            <span v-if="bp.prices[pl.price_list] !== undefined && bp.prices[pl.price_list] !== null">
                              {{ encryptPrice(bp.prices[pl.price_list]) }}
                            </span>
                            <span v-else class="text-slate-600 font-normal">—</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>

        <!-- Header -->
        <header 
          class="absolute top-0 left-0 right-0 z-40 px-8 py-5 flex items-center justify-between bg-gradient-to-b from-slate-950 via-slate-950/80 to-transparent transition-all duration-500 transform"
          :class="showControls ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0 pointer-events-none'"
        >
          <div class="flex items-center gap-3">
            <span class="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
            <h1 class="text-lg font-bold tracking-tight text-slate-100">
              {{ offer.heading }}
            </h1>
          </div>
          
          <!-- Slide Indicator -->
          <div class="flex items-center gap-4 text-xs font-semibold text-slate-400">
            <span class="bg-slate-900/90 px-3 py-1 rounded-full border border-slate-800 font-bold">
              Item {{ activeIndex + 1 }} / {{ offer.items?.length || 0 }}
            </span>
            <span v-if="offer.timer > 0" class="text-xs uppercase tracking-wider bg-indigo-500/10 text-indigo-400 px-3 py-1 rounded-full border border-indigo-500/30 font-bold flex items-center gap-1.5 animate-pulse">
              <span>Next:</span>
              <span class="font-mono text-sm font-black bg-indigo-950/80 px-2 py-0.5 rounded text-indigo-300">
                {{ isPaused ? 'Paused' : `${slideshowTimeLeft}s` }}
              </span>
            </span>
          </div>
        </header>

        <!-- Controls / Navigation Bar -->
        <footer 
          class="absolute bottom-0 left-0 right-0 z-40 px-8 py-6 flex items-center justify-between bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent transition-all duration-500 transform"
          :class="showControls ? 'translate-y-0 opacity-100' : 'translate-y-full opacity-0 pointer-events-none'"
        >
          <div class="flex items-center gap-3">
            <button
              @click="exitPresentationMode"
              class="rounded-xl border border-slate-800 bg-slate-900/80 px-5 py-2.5 text-xs font-bold text-slate-300 hover:bg-slate-900 hover:text-white transition active:scale-95"
            >
              ❌ Exit Play
            </button>
            <button
              @click="loadOffer(true)"
              class="rounded-xl border border-slate-800 bg-slate-900/80 px-5 py-2.5 text-xs font-bold text-amber-400 hover:bg-amber-500/10 hover:border-amber-500/30 transition active:scale-95"
            >
              🔄 Refresh (R)
            </button>
          </div>
          
          <div class="flex items-center gap-4">
            <!-- Previous Button -->
            <button
              @click="prevItem"
              :disabled="!offer.items || offer.items.length <= 1"
              class="rounded-xl border border-slate-800 bg-slate-900/80 px-5 py-2.5 text-xs font-bold text-slate-200 hover:bg-slate-800 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition active:scale-95"
            >
              ◀ Previous
            </button>

            <!-- Pause / Play Toggle -->
            <button
              @click="togglePause"
              class="rounded-xl border border-slate-800 bg-slate-900/80 px-6 py-2.5 text-xs font-bold transition active:scale-95 font-bold"
              :class="isPaused ? 'text-emerald-400 hover:bg-emerald-500/10 hover:border-emerald-500/30' : 'text-amber-400 hover:bg-amber-500/10 hover:border-amber-500/30'"
            >
              {{ isPaused ? '▶ Resume timer' : '⏸ Pause timer' }}
            </button>

            <!-- Next Button -->
            <button
              @click="nextItem"
              :disabled="!offer.items || offer.items.length <= 1"
              class="rounded-xl border border-slate-800 bg-slate-900/80 px-5 py-2.5 text-xs font-bold text-slate-200 hover:bg-slate-800 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition active:scale-95"
            >
              Next ▶
            </button>
          </div>
          
          <!-- Quick Keyboard Legend -->
          <div class="text-[10px] text-slate-500 font-medium hidden md:block">
            Use Esc to Exit
          </div>
        </footer>

      </div>

      <!-- Regular Web View -->
      <template v-else>
        <!-- Premium Hero Header -->
        <header class="relative overflow-hidden bg-gradient-to-br from-indigo-900 via-slate-900 to-black text-white px-6 py-12 md:py-16 text-center border-b border-[var(--color-border)] shrink-0">
          <!-- Back to Catalogue Button -->
          <button 
            @click="goBackToCatalogue"
            class="absolute top-4 left-4 z-20 flex items-center gap-2 rounded-xl bg-slate-950/60 hover:bg-slate-900/80 px-4 py-2 text-xs font-bold text-slate-300 hover:text-white border border-slate-800/50 transition active:scale-95 focus:outline-none"
          >
            ← Back to Catalogue
          </button>
          
          <!-- Refresh Button -->
          <button 
            @click="loadOffer(false)"
            class="absolute top-4 right-4 z-20 flex items-center gap-2 rounded-xl bg-slate-950/60 hover:bg-slate-900/80 px-4 py-2 text-xs font-bold text-slate-300 hover:text-white border border-slate-800/50 transition active:scale-95 focus:outline-none"
          >
            🔄 Refresh (R)
          </button>
          
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
        <main class="flex-1 w-full mx-auto px-6 py-10" :class="containerClass">
          <div class="grid gap-6" :class="gridClass">
            <div
              v-for="item in offer.items"
              :key="item.itemcode"
              class="group relative flex flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden shadow-md hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1"
            >
              <!-- Image / Placeholder Frame -->
              <div class="relative aspect-square w-full bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4 border-b border-[var(--color-border)]/50 overflow-hidden shrink-0">
                <!-- Stacked Offer Badges Overlay -->
                <div v-if="item.discount_type && item.discount_desc" class="absolute top-2 left-2 z-10 pointer-events-none flex flex-col bg-slate-900/95 border border-[var(--color-warning)]/30 rounded-lg overflow-hidden shadow-lg backdrop-blur-sm max-w-[90%]">
                  <div class="bg-[var(--color-warning)] text-black text-[8px] font-black uppercase px-1.5 py-0.5 text-center tracking-wider shrink-0">
                    Offer
                  </div>
                  <div class="flex flex-col whitespace-normal break-words font-bold text-[var(--color-warning)]" :class="badgeTextClass">
                    <div 
                      v-for="(line, lIdx) in item.discount_desc.split(' | ')" 
                      :key="lIdx"
                      class="leading-none"
                    >
                      {{ line }}
                    </div>
                  </div>
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
              <div class="flex-1 flex flex-col justify-between" :class="cardPaddingClass">
                <div class="space-y-1.5">
                  <h3 class="font-bold text-[var(--color-text)] line-clamp-2 group-hover:text-[var(--color-info)] transition-colors" :class="cardTitleClass" :title="item.itemname">
                    {{ item.itemname }}
                  </h3>
                </div>

                <div class="space-y-2 shrink-0">
                  <!-- Barcode & Prices Table -->
                  <div v-if="item.barcode_prices && item.barcode_prices.length" class="pt-2 border-t border-[var(--color-border)]/40 shrink-0">
                    <div class="overflow-x-auto">
                      <table class="w-full text-left text-xl border-collapse">

                        <tbody class="divide-y divide-[var(--color-border)]/30 font-medium">
                          <tr 
                            v-for="bp in item.barcode_prices" 
                            :key="bp.barcode"
                            class="hover:bg-[var(--color-bg)]/50 transition-colors"
                          >
                            <td class="py-0.5 pr-2 font-mono text-[var(--color-text)] select-all font-bold">
                              {{ bp.barcode || '—' }} <span v-if="bp.uom" class="text-[var(--color-text-muted)] font-normal text-base font-sans">({{ bp.uom }})</span>
                            </td>
                            <td 
                              v-for="pl in offer.price_lists" 
                              :key="pl.price_list"
                              class="py-0.5 px-0.5 font-mono text-right text-[var(--color-info)] font-bold tracking-widest"
                            >
                              <span v-if="bp.prices[pl.price_list] !== undefined && bp.prices[pl.price_list] !== null">
                                {{ encryptPrice(bp.prices[pl.price_list]) }}
                              </span>
                              <span v-else class="text-[var(--color-text-muted)] font-normal">—</span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </template>

      <!-- Floating Actions (Visible in normal web view) -->
      <div v-if="!isFullscreen && offer" class="fixed bottom-10 right-10 z-40 flex flex-row items-center gap-4">
        <!-- Export PDF Button -->
        <button
          @click="exportToPDF"
          class="flex items-center gap-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 px-8 py-5 text-xl font-bold text-white shadow-2xl hover:scale-105 active:scale-95 focus:outline-none focus:ring-4 focus:ring-emerald-300 focus:bg-emerald-700 focus:scale-105 transition-all duration-300 border border-emerald-500"
        >
          <span>📄 Export PDF</span>
        </button>

        <!-- Refresh Button -->
        <button
          @click="loadOffer(false)"
          class="flex items-center gap-3 rounded-2xl bg-amber-600 hover:bg-amber-700 px-8 py-5 text-xl font-bold text-white shadow-2xl hover:scale-105 active:scale-95 focus:outline-none focus:ring-4 focus:ring-amber-300 focus:bg-amber-700 focus:scale-105 transition-all duration-300 border border-amber-500"
        >
          <span>🔄 Refresh (R)</span>
        </button>

        <!-- Play Slideshow Button -->
        <button
          ref="playButtonRef"
          @click="enterPresentationMode"
          class="flex items-center gap-3 rounded-2xl bg-indigo-600 hover:bg-indigo-700 px-8 py-5 text-xl font-bold text-white shadow-2xl hover:scale-105 active:scale-95 focus:outline-none focus:ring-4 focus:ring-indigo-300 focus:bg-indigo-700 focus:scale-105 transition-all duration-300 border border-indigo-500"
        >
          <span>📺 Play Slideshow</span>
        </button>
      </div>
    </template>

    <!-- Footer -->
    <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)]/50 py-6 px-6 text-center text-[10px] text-[var(--color-text-muted)] shrink-0">
      <div class="max-w-4xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-2">
        <span>© {{ new Date().getFullYear() }} Sundaram and Sons Private Ltd.</span>
        <span>Keyboard Fast wholesale Billing system</span>
      </div>
    </footer>
  </div>

  <!-- Export Options Modal -->
  <div v-if="showExportModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm transition-opacity duration-300">
    <div class="relative w-full max-w-md bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 shadow-2xl space-y-6 text-[var(--color-text)] animate-in fade-in zoom-in duration-200">
      <!-- Title -->
      <div>
        <h3 class="text-lg font-bold text-[var(--color-text)] flex items-center gap-2">
          📄 Export PDF Options
        </h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-1">
          Configure the layout options for the generated catalog PDF.
        </p>
      </div>

      <!-- Form controls -->
      <div class="space-y-4">
        <!-- Print Format Selector -->
        <div class="bg-[var(--color-bg)]/50 p-3.5 rounded-xl border border-[var(--color-border)]">
          <label class="block text-sm font-bold text-[var(--color-text)] mb-1">Print Template</label>
          <span class="block text-[10px] text-[var(--color-text-muted)] mb-2">
            Layout template. Edit it in the desk under Print Template.
          </span>
          <select
            v-model="selectedPrintTemplate"
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs font-medium text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-info)]"
          >
            <option v-for="pt in printTemplates" :key="pt" :value="pt">{{ pt }}</option>
          </select>
        </div>

        <!-- Include Prices Checkbox -->
        <label class="flex items-center gap-3 cursor-pointer group bg-[var(--color-bg)]/50 p-3.5 rounded-xl border border-[var(--color-border)] hover:border-[var(--color-info)]/60 transition">
          <input 
            v-model="includePricesInPrint" 
            type="checkbox"
            class="w-4 h-4 rounded border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-info)] focus:ring-[var(--color-info)] focus:ring-offset-[var(--color-surface)] focus:ring-2 cursor-pointer"
          />
          <div class="flex flex-col">
            <span class="text-sm font-bold text-[var(--color-text)] group-hover:text-[var(--color-info)] transition">Include Prices</span>
            <span class="text-[10px] text-[var(--color-text-muted)]">Show price list rates under each item in catalog.</span>
          </div>
        </label>

        <!-- Encrypt Prices Checkbox (Conditional) -->
        <div v-if="includePricesInPrint" class="animate-in slide-in-from-top-2 duration-200">
          <label class="flex items-center gap-3 cursor-pointer group bg-[var(--color-bg)]/50 p-3.5 rounded-xl border border-[var(--color-border)] hover:border-[var(--color-info)]/60 transition">
            <input 
              v-model="encryptPricesInPrint" 
              type="checkbox"
              class="w-4 h-4 rounded border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-info)] focus:ring-[var(--color-info)] focus:ring-offset-[var(--color-surface)] focus:ring-2 cursor-pointer"
            />
            <div class="flex flex-col">
              <span class="text-sm font-bold text-[var(--color-text)] group-hover:text-[var(--color-info)] transition">Encrypt Prices?</span>
              <span class="text-[10px] text-[var(--color-text-muted)]">Obfuscate price digits to cipher letters.</span>
            </div>
          </label>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="flex items-center justify-end gap-3 pt-2">
        <button 
          @click="closeExportModal"
          class="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)]/60 px-5 py-2.5 text-xs font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-bg)] hover:text-[var(--color-text)] transition active:scale-95"
        >
          Cancel
        </button>
        <button 
          @click="triggerPrint"
          :disabled="printing"
          class="rounded-xl bg-[var(--color-info)] hover:bg-[var(--color-info)]/90 disabled:opacity-50 disabled:pointer-events-none px-6 py-2.5 text-xs font-bold text-white transition active:scale-95 shadow-lg shadow-[var(--color-info)]/20"
        >
          {{ printing ? 'Preparing…' : 'Print Catalog' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import { encryptPrice } from '../encryption.js'
import { initFrappeSocket } from '../services/frappeSocket.js'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref(null)
const offer = ref(null)
let refreshInterval = null

// Presentation Mode States
const isFullscreen = ref(false)
const activeIndex = ref(0)
const prevActiveIndex = ref(0)
const isPaused = ref(false)
const slideshowTimeLeft = ref(0)
let slideshowInterval = null

const playButtonRef = ref(null)
const goHomeButtonRef = ref(null)

const showControls = ref(true)
let controlsTimeout = null

function resetControlsTimer() {
  showControls.value = true
  if (controlsTimeout) {
    clearTimeout(controlsTimeout)
  }
  controlsTimeout = setTimeout(() => {
    if (isFullscreen.value) {
      showControls.value = false
    }
  }, 3000)
}

function focusPlayButton() {
  nextTick(() => {
    if (playButtonRef.value) {
      playButtonRef.value.focus()
    }
  })
}

function focusGoHomeButton() {
  nextTick(() => {
    if (goHomeButtonRef.value) {
      goHomeButtonRef.value.focus()
    }
  })
}

watch(activeIndex, (newVal, oldVal) => {
  prevActiveIndex.value = oldVal
})

const pageaddress = computedRouteParam()

function computedRouteParam() {
  return route.params.pageaddress
}

const gridClass = computed(() => {
  return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
})

const containerClass = computed(() => {
  return 'max-w-7xl'
})

const cardPaddingClass = computed(() => {
  return 'p-5 gap-4'
})

const cardTitleClass = computed(() => {
  return 'text-[14px] leading-snug font-bold'
})

const cardCodeClass = computed(() => {
  return 'text-[11px]'
})

const badgeTextClass = computed(() => {
  return 'text-[10px] p-1.5 gap-1'
})

// Presentation Column Count Computes the active visible column count (safely limited by available items count)
const presentationCols = computed(() => {
  if (!offer.value?.items?.length) return 4
  return Math.min(parseInt(offer.value.tile_grid) || 4, offer.value.items.length)
})

// Helper to compute circular difference centered around the active visible columns range [-1, C]
function getCircularDiff(idx, activeIdx) {
  if (!offer.value?.items?.length) return 0
  const N = offer.value.items.length
  const C = presentationCols.value
  
  let diff = idx - activeIdx
  const center = (C - 1) / 2
  const halfN = N / 2
  
  let targetDiff = diff - center
  while (targetDiff < -halfN) targetDiff += N
  while (targetDiff >= halfN) targetDiff -= N
  return targetDiff + center
}

// Detect if an item is wrapping around the boundary of the circular list to disable slide transition.
function isItemWrapping(idx) {
  if (!offer.value?.items?.length) return false
  const N = offer.value.items.length
  if (N <= 2) return false

  const diff = getCircularDiff(idx, activeIndex.value)
  const prevDiff = getCircularDiff(idx, prevActiveIndex.value)

  return Math.abs(diff - prevDiff) > 1
}

// Circular Carousel Position and Styling Calculator
function getItemStyle(idx) {
  if (!offer.value?.items?.length) return {}
  const N = offer.value.items.length
  const C = presentationCols.value
  
  const diff = getCircularDiff(idx, activeIndex.value)

  // Determine visibility: active columns [0, C-1] plus one peeking on each side
  const isVisible = (diff >= -1 && diff <= C) || (N === C + 1 && diff === -1)
  
  // Choose card size and spacing by splitting the screen to C + 1 and subtracting a dynamic gap
  const gapVal = C >= 9 ? 0.8 : (C >= 6 ? 1.0 : 1.5)
  const cardWidthVal = (100 / (C + 1)) - gapVal
  const maxW = '1200px'

  const transitionStyle = isItemWrapping(idx)
    ? 'none'
    : 'all 0.6s cubic-bezier(0.25, 0.8, 0.25, 1)'

  const cardHeightVal = showControls.value ? '76vh' : '90vh'
  const cardTopVal = showControls.value ? '6vh' : '3vh'

  if (!isVisible) {
    const translateVal = diff < 0 ? -100 : 100
    return {
      opacity: 0,
      transform: `translateX(${translateVal}vw) scale(0.7)`,
      pointerEvents: 'none',
      position: 'absolute',
      zIndex: 0,
      width: `${cardWidthVal}vw`,
      maxWidth: maxW,
      height: cardHeightVal,
      top: cardTopVal,
      maxHeight: 'none',
      transition: transitionStyle
    }
  }

  const isActive = diff >= 0 && diff < C
  const opacity = isActive ? 1 : 0.5
  const scale = isActive ? 1.02 : 0.88
  const zIndex = isActive ? 20 : 10
  
  // Translate calculation: (diff - (C-1)/2) * (cardWidth + gap)
  const translateX = (diff - (C - 1) / 2) * (cardWidthVal + gapVal)

  return {
    opacity: opacity,
    transform: `translateX(${translateX}vw) scale(${scale})`,
    zIndex: zIndex,
    position: 'absolute',
    width: `${cardWidthVal}vw`,
    maxWidth: maxW,
    height: cardHeightVal,
    top: cardTopVal,
    maxHeight: 'none',
    transition: transitionStyle,
    pointerEvents: isActive ? 'auto' : 'none'
  }
}

function startTimer() {
  // Disabled automatic polling to keep data in local memory and not ask server repeatedly.
  // stopTimer()
  // const sec = offer.value?.timer
  // if (sec && sec > 0) {
  //   refreshInterval = setInterval(() => {
  //     loadOffer(true)
  //   }, sec * 1000)
  // }
}

function stopTimer() {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

// Presentation Actions
function startSlideshow() {
  stopSlideshow()
  if (isPaused.value) return
  const sec = parseInt(offer.value?.timer) || 8 // Default to 8 seconds
  slideshowTimeLeft.value = sec
  slideshowInterval = setInterval(() => {
    if (slideshowTimeLeft.value > 1) {
      slideshowTimeLeft.value--
    } else {
      nextItem()
    }
  }, 1000)
}

function stopSlideshow() {
  if (slideshowInterval) {
    clearInterval(slideshowInterval)
    slideshowInterval = null
  }
}

function resetSlideshowTimer() {
  stopSlideshow()
  startSlideshow()
}

function nextItem() {
  if (!offer.value?.items?.length) return
  const N = offer.value.items.length
  activeIndex.value = (activeIndex.value + 1) % N
  resetSlideshowTimer()
}

function prevItem() {
  if (!offer.value?.items?.length) return
  const N = offer.value.items.length
  activeIndex.value = (activeIndex.value - 1 + N) % N
  resetSlideshowTimer()
}

function togglePause() {
  isPaused.value = !isPaused.value
  if (isPaused.value) {
    stopSlideshow()
  } else {
    startSlideshow()
  }
}

function enterPresentationMode() {
  const docEl = document.documentElement
  if (docEl.requestFullscreen) {
    docEl.requestFullscreen().then(() => {
      isFullscreen.value = true
      activeIndex.value = 0
      isPaused.value = false
      startSlideshow()
    }).catch(err => {
      alert(`Error enabling fullscreen: ${err.message}`)
    })
  } else {
    isFullscreen.value = true
    activeIndex.value = 0
    isPaused.value = false
    startSlideshow()
  }
}

function exitPresentationMode() {
  if (document.fullscreenElement) {
    document.exitFullscreen().catch(err => {
      console.error(err)
    })
  }
  isFullscreen.value = false
  stopSlideshow()
  focusPlayButton()
}

function handleFullscreenChange() {
  const inFullscreen = !!document.fullscreenElement
  isFullscreen.value = inFullscreen
  if (!inFullscreen) {
    stopSlideshow()
    focusPlayButton()
  }
}

async function loadOffer(silent = false) {
  if (!pageaddress) {
    loading.value = false
    error.value = 'Invalid page address'
    return
  }

  if (!silent) {
    loading.value = true
  }
  error.value = null
  try {
    const res = await frappeGet('ssplbilling.api.offer_api.get_offer_details', {
      pageaddress: pageaddress
    })
    
    if (res) {
      // Blank cipher_map means encryption is off; clear any stale key.
      const cipher = (res.cipher_map || '').trim()
      if (cipher) {
        localStorage.setItem('wb-cipher', cipher)
      } else {
        localStorage.removeItem('wb-cipher')
      }
      offer.value = res
      document.title = `${res.heading} | Deals`
      startTimer()
      if (!silent) {
        focusPlayButton()
      }
    } else {
      if (!silent) {
        error.value = 'Offer not found'
        focusGoHomeButton()
      }
    }
  } catch (err) {
    console.error(err)
    if (!silent) {
      error.value = err.message || 'Failed to load offers'
      focusGoHomeButton()
    }
  } finally {
    if (!silent) {
      loading.value = false
    }
  }
}

function goHome() {
  if (import.meta.env.DEV) {
    router.push('/')
  } else {
    window.location.href = '/frontend/'
  }
}

function goBackToCatalogue() {
  router.push('/catelogue')
}

const showExportModal = ref(false)
const includePricesInPrint = ref(false)
const encryptPricesInPrint = ref(false)
const printTemplates = ref([])
const selectedPrintTemplate = ref('')
const printing = ref(false)

watch(includePricesInPrint, (newVal) => {
  if (!newVal) {
    encryptPricesInPrint.value = false
  }
})

async function loadPrintTemplates() {
  try {
    const res = await frappeGet('ssplbilling.api.offer_api.get_offer_print_templates')
    printTemplates.value = Array.isArray(res) ? res : []
    if (!selectedPrintTemplate.value && printTemplates.value.length) {
      selectedPrintTemplate.value = printTemplates.value[0]
    }
  } catch (err) {
    console.error(err)
  }
}

function exportToPDF() {
  showExportModal.value = true
  if (!printTemplates.value.length) {
    loadPrintTemplates()
  }
}

function closeExportModal() {
  showExportModal.value = false
}

function waitForImages(win) {
  const images = Array.from(win.document.images || [])
  const pending = images
    .filter(img => !img.complete)
    .map(img => new Promise(resolve => {
      img.addEventListener('load', resolve, { once: true })
      img.addEventListener('error', resolve, { once: true })
    }))
  // Cap the wait so a dead image URL cannot block printing forever.
  return Promise.race([
    Promise.all(pending),
    new Promise(resolve => setTimeout(resolve, 5000))
  ])
}

// The catalogue layout lives in the "SSPL Offer Catalogue" Print Template, so the
// server renders the HTML. It is printed from an offscreen iframe rather than a
// second tab: the SPA stays put, and no popup blocker is involved.
async function triggerPrint() {
  if (printing.value) return
  printing.value = true
  let frame = null
  try {
    const html = await frappeGet('ssplbilling.api.offer_api.render_offer_catalog', {
      pageaddress: pageaddress,
      print_template: selectedPrintTemplate.value || '',
      include_prices: includePricesInPrint.value ? 1 : 0,
      encrypt_prices: encryptPricesInPrint.value ? 1 : 0
    })
    if (!html) {
      alert('Could not render the catalog. Check the print template.')
      return
    }

    frame = document.createElement('iframe')
    // Parked offscreen at page size rather than hidden: a display:none or
    // visibility:hidden frame lays out nothing and prints blank pages.
    frame.setAttribute('aria-hidden', 'true')
    frame.style.cssText = 'position:fixed;left:-10000px;top:0;width:210mm;height:297mm;border:0;'
    document.body.appendChild(frame)

    const doc = frame.contentDocument
    doc.open()
    doc.write(
      `<!doctype html><html><head><meta charset="utf-8"><title>${offer.value?.heading || 'Catalog'}</title>` +
      `<style>@media print { * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } }</style>` +
      `</head><body>${html}</body></html>`
    )
    doc.close()
    showExportModal.value = false

    // Wait for the images to settle, otherwise the first page prints blank.
    await waitForImages(frame.contentWindow)

    // Keep the frame alive until the print dialog is done with it, and register
    // the listener before print() — the call blocks and afterprint can fire
    // before it returns. afterprint is not fired everywhere, so a timer backstops.
    const el = frame
    const cleanup = () => {
      if (el.parentNode) {
        el.parentNode.removeChild(el)
      }
    }
    el.contentWindow.addEventListener('afterprint', cleanup, { once: true })
    setTimeout(cleanup, 60000)
    frame = null // ownership handed to cleanup; do not remove it in the catch

    el.contentWindow.focus()
    el.contentWindow.print()
  } catch (err) {
    console.error(err)
    if (frame && frame.parentNode) {
      frame.parentNode.removeChild(frame)
    }
    alert(err.message || 'Failed to render catalog')
  } finally {
    printing.value = false
  }
}

watch(isFullscreen, (newVal) => {
  if (newVal) {
    resetControlsTimer()
  } else {
    showControls.value = true
    if (controlsTimeout) {
      clearTimeout(controlsTimeout)
      controlsTimeout = null
    }
  }
})

function handleKeyDown(event) {
  resetControlsTimer()
  const key = event.key
  const keyCode = event.keyCode

  if (isFullscreen.value) {
    if (key === 'ArrowRight' || key === 'ArrowDown' || keyCode === 39 || keyCode === 40) {
      event.preventDefault()
      nextItem()
    } else if (key === 'ArrowLeft' || key === 'ArrowUp' || keyCode === 37 || keyCode === 38) {
      event.preventDefault()
      prevItem()
    } else if (key === ' ' || key === 'Enter' || keyCode === 13 || keyCode === 32 || key === 'MediaPlayPause' || keyCode === 179) {
      event.preventDefault()
      togglePause()
    } else if (key === 'Escape' || key === 'Backspace' || keyCode === 27 || keyCode === 8 || keyCode === 10009 || keyCode === 461) {
      event.preventDefault()
      exitPresentationMode()
    } else if (key === 'r' || key === 'R') {
      event.preventDefault()
      loadOffer(true)
    }
  } else {
    if (key === 'Enter' || keyCode === 13 || key === ' ' || keyCode === 32) {
      const activeEl = document.activeElement
      const isInteractive = activeEl && (
        activeEl.tagName === 'BUTTON' ||
        activeEl.tagName === 'INPUT' ||
        activeEl.tagName === 'SELECT' ||
        activeEl.tagName === 'TEXTAREA' ||
        activeEl.tagName === 'A' ||
        activeEl.getAttribute('role') === 'button'
      )
      if (!isInteractive) {
        event.preventDefault()
        enterPresentationMode()
      }
    } else if (
      key === 'ArrowRight' || key === 'ArrowLeft' || key === 'ArrowUp' || key === 'ArrowDown' ||
      keyCode === 37 || keyCode === 38 || keyCode === 39 || keyCode === 40
    ) {
      if (!document.activeElement || document.activeElement === document.body) {
        event.preventDefault()
        focusPlayButton()
      }
    } else if (key === 'r' || key === 'R') {
      event.preventDefault()
      loadOffer(false)
    }
  }
}

// ── Live refresh over websocket ───────────────────────────────────────────────
// The offer page is public (guest), so the backend broadcasts offer_page_update to
// the website room, which guest sockets join. We refresh when the changed doctype
// affects THIS page: an Offer-Items change matching our pageaddress, or an Item
// change whose item_code is currently shown in this offer.
let _offerSocket = null
let _offerHandler = null
let _offerRefreshTimer = null

function scheduleOfferRefresh() {
  if (_offerRefreshTimer) clearTimeout(_offerRefreshTimer)
  _offerRefreshTimer = setTimeout(() => {
    _offerRefreshTimer = null
    loadOffer(true) // silent refresh — no loading spinner
  }, 800)
}

function setupOfferSocket() {
  initFrappeSocket().then((socket) => {
    if (!socket) return
    _offerSocket = socket
    _offerHandler = (data) => {
      if (!data) return
      const affectsThisPage =
        (data.type === 'offer' && data.pageaddress && data.pageaddress === pageaddress) ||
        (data.type === 'item' &&
          data.item_code &&
          offer.value?.items?.some((i) => i.itemcode === data.item_code))
      if (affectsThisPage) scheduleOfferRefresh()
    }
    socket.on('offer_page_update', _offerHandler)
  })
}

function teardownOfferSocket() {
  if (_offerRefreshTimer) clearTimeout(_offerRefreshTimer)
  if (_offerSocket && _offerHandler) {
    _offerSocket.off('offer_page_update', _offerHandler)
  }
  _offerSocket = null
  _offerHandler = null
}

onMounted(() => {
  loadOffer()
  setupOfferSocket()
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('mousemove', resetControlsTimer)
})

onBeforeUnmount(() => {
  stopTimer()
  stopSlideshow()
  teardownOfferSocket()
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('mousemove', resetControlsTimer)
  if (controlsTimeout) {
    clearTimeout(controlsTimeout)
  }
})
</script>

<style scoped>
/* Core stylesheet variables integrated */
</style>

