<template>
  <div class="h-screen overflow-y-auto flex flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] antialiased selection:bg-[var(--color-info)] selection:text-white">
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
                  class="max-h-[35vh] max-w-full object-contain"
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
                  v-if="presentationCols < 6"
                  class="flex items-center justify-between pt-1"
                >
                  <div class="flex flex-col">
                    <span class="text-[18px] uppercase font-normal text-slate-500 tracking-wider">Item Code</span>
                    <span class="font-mono text-[24px] font-normal text-slate-300 leading-normal">{{ item.itemcode }}</span>
                  </div>
                  <div v-if="item.barcode" class="flex flex-col items-end">
                    <span class="text-[18px] uppercase font-normal text-slate-500 tracking-wider">Barcode</span>
                    <span class="font-mono text-[24px] font-normal bg-indigo-500/10 text-indigo-400 px-3 py-1 rounded-full border border-indigo-500/20 leading-normal">
                      {{ item.barcode }}
                    </span>
                  </div>
                </div>
                <div v-else class="text-[18px] font-mono text-slate-400 mt-1 truncate">
                  Code: {{ item.itemcode }}
                </div>
              </div>
            </div>
          </div>
        </main>

        <!-- Header -->
        <header class="absolute top-0 left-0 right-0 z-40 px-8 py-5 flex items-center justify-between bg-gradient-to-b from-slate-950 via-slate-950/80 to-transparent">
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
        <footer class="absolute bottom-0 left-0 right-0 z-40 px-8 py-6 flex items-center justify-between bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent">
          <button
            @click="exitPresentationMode"
            class="rounded-xl border border-slate-800 bg-slate-900/80 px-5 py-2.5 text-xs font-bold text-slate-300 hover:bg-slate-900 hover:text-white transition active:scale-95"
          >
            ❌ Exit Play
          </button>
          
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
              class="group relative flex flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
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
                  <div class="flex items-center gap-1.5 text-[var(--color-text-muted)] font-mono" :class="cardCodeClass">
                    <span class="bg-[var(--color-midlight)] px-1.5 py-0.5 rounded">Code</span>
                    <span>{{ item.itemcode }}</span>
                  </div>
                </div>

                <div class="space-y-2 shrink-0">
                  <!-- Barcode Badge -->
                  <div v-if="item.barcode" class="pt-2 border-t border-[var(--color-border)]/40 flex items-center justify-between">
                    <span class="uppercase font-bold text-[var(--color-text-muted)] tracking-wider" :class="cardCodeClass">Barcode</span>
                    <span class="font-mono font-bold bg-[var(--color-info)]/10 text-[var(--color-info)] px-2 py-0.5 rounded-full select-all" :class="cardCodeClass">
                      {{ item.barcode }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </template>

      <!-- Floating Play Button (Visible in normal web view) -->
      <div v-if="!isFullscreen && offer" class="fixed bottom-10 right-10 z-40">
        <button
          @click="enterPresentationMode"
          class="flex items-center gap-4 rounded-2xl bg-indigo-600 hover:bg-indigo-700 px-10 py-5 text-2xl font-bold text-white shadow-2xl hover:scale-105 active:scale-95 transition-all duration-300 border border-indigo-500"
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
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { frappeGet } from '../api.js'

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

watch(activeIndex, (newVal, oldVal) => {
  prevActiveIndex.value = oldVal
})

const pageaddress = computedRouteParam()

function computedRouteParam() {
  return route.params.pageaddress
}

const gridClass = computed(() => {
  const cols = parseInt(offer.value?.tile_grid) || 4
  if (cols === 1) return 'grid-cols-1'
  if (cols === 2) return 'grid-cols-1 sm:grid-cols-2'
  if (cols === 4) return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
  if (cols === 6) return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6'
  if (cols === 9) return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 2xl:grid-cols-9'
  return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
})

const containerClass = computed(() => {
  const cols = parseInt(offer.value?.tile_grid) || 4
  if (cols >= 9) return 'max-w-[95vw]'
  if (cols >= 6) return 'max-w-[90vw]'
  return 'max-w-7xl'
})

const cardPaddingClass = computed(() => {
  const cols = parseInt(offer.value?.tile_grid) || 4
  if (cols >= 9) return 'p-3 gap-2'
  if (cols >= 6) return 'p-4 gap-3'
  return 'p-5 gap-4'
})

const cardTitleClass = computed(() => {
  const cols = parseInt(offer.value?.tile_grid) || 4
  if (cols >= 9) return 'text-[11px] leading-tight font-extrabold'
  if (cols >= 6) return 'text-[12px] leading-snug font-bold'
  return 'text-[14px] leading-snug font-bold'
})

const cardCodeClass = computed(() => {
  const cols = parseInt(offer.value?.tile_grid) || 4
  if (cols >= 9) return 'text-[8px]'
  if (cols >= 6) return 'text-[9px]'
  return 'text-[11px]'
})

const badgeTextClass = computed(() => {
  const cols = parseInt(offer.value?.tile_grid) || 4
  if (cols >= 9) return 'text-[8px] p-1 gap-0.5'
  if (cols >= 6) return 'text-[8px] p-1 gap-1'
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
      height: '76vh',
      top: '6vh',
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
    height: '76vh',
    top: '6vh',
    maxHeight: 'none',
    transition: transitionStyle,
    pointerEvents: isActive ? 'auto' : 'none'
  }
}

function startTimer() {
  stopTimer()
  const sec = offer.value?.timer
  if (sec && sec > 0) {
    refreshInterval = setInterval(() => {
      loadOffer(true)
    }, sec * 1000)
  }
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
}

function handleFullscreenChange() {
  const inFullscreen = !!document.fullscreenElement
  isFullscreen.value = inFullscreen
  if (!inFullscreen) {
    stopSlideshow()
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
      offer.value = res
      document.title = `${res.heading} | Deals`
      startTimer()
    } else {
      if (!silent) {
        error.value = 'Offer not found'
      }
    }
  } catch (err) {
    console.error(err)
    if (!silent) {
      error.value = err.message || 'Failed to load offers'
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

onMounted(() => {
  loadOffer()
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onBeforeUnmount(() => {
  stopTimer()
  stopSlideshow()
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped>
/* Core stylesheet variables integrated */
</style>
