<template>
  <div class="fixed inset-0 overflow-hidden bg-black font-sans text-white antialiased select-none" @mousemove="resetControlsTimer">
    <!-- Loading -->
    <div v-if="loading" class="flex h-full flex-col items-center justify-center">
      <div class="relative mb-4 h-16 w-16">
        <div class="absolute inset-0 rounded-full border-4 border-indigo-500/20"></div>
        <div class="absolute inset-0 animate-spin rounded-full border-4 border-t-indigo-500"></div>
      </div>
      <div class="animate-pulse text-sm font-medium text-slate-400">Loading catalogue...</div>
    </div>

    <!-- Error / Not found -->
    <div v-else-if="error || !offer" class="mx-auto flex h-full max-w-md flex-col items-center justify-center p-8 text-center">
      <div class="mb-6 text-6xl">🏷️</div>
      <h2 class="mb-2 text-2xl font-bold">Catalogue Not Found</h2>
      <p class="mb-6 text-sm leading-relaxed text-slate-400">{{ error || 'No active items at this address.' }}</p>
      <button
        ref="backButtonRef"
        type="button"
        class="rounded-xl bg-indigo-600 px-6 py-2.5 text-xs font-bold text-white shadow-lg hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-300"
        @click="goBack"
      >
        ← Back
      </button>
    </div>

    <template v-else>
        <!-- Mat layout: rows x columns window onto a flat mat of items that glides upward without page breaks -->
        <main
          class="mat-stage absolute inset-0 flex items-center justify-center overflow-hidden px-[3vw] transition-all duration-500"
          :class="showControls ? 'pt-[9vh] pb-[12vh]' : 'pt-[3vh] pb-[3vh]'"
        >
          <div class="mat-surface h-full w-full">
            <div ref="matViewport" class="mat-viewport relative h-full w-full overflow-hidden">
              <div ref="matTrack" class="absolute inset-x-0 top-0 will-change-transform">
                <div
                  v-for="r in matRows"
                  :key="r"
                  class="absolute inset-x-0 grid"
                  :style="{
                    top: `${r * matRowPitch}px`,
                    height: `${matRowHeight}px`,
                    gap: `${matGap}px`,
                    gridTemplateColumns: `repeat(${MAT_COLS_C}, minmax(0, 1fr))`
                  }"
                >
                  <template v-for="c in MAT_COLS_C" :key="c">
                    <div
                      v-if="matItemAt(r, c - 1)"
                      class="mat-tile relative flex min-h-0 min-w-0 flex-col overflow-hidden rounded-2xl border border-white/70 bg-white p-[0.6vw]"
                      :style="matTileStyle(r, c - 1)"
                    >
                      <template v-for="item in [matItemAt(r, c - 1)]" :key="item.itemcode">
                        <div
                          v-if="item.discount_type && item.discount_desc"
                          class="absolute left-0 right-0 top-0 z-10 truncate bg-amber-500 px-2 py-0.5 text-[0.75vw] font-black uppercase tracking-wide text-black"
                        >
                          {{ item.discount_desc.split(' | ')[0] }}
                        </div>
                        <div class="flex min-h-0 flex-1 items-center justify-center" :class="item.discount_type && item.discount_desc ? 'pt-[1.4vw]' : ''">
                          <img v-if="item.image" :src="item.image" :alt="item.itemname" class="max-h-full max-w-full object-contain" />
                          <span v-else class="text-[2.6vw] leading-none">📦</span>
                        </div>
                        <div class="shrink-0 space-y-0.5 border-t border-slate-100 pt-[0.4vw]">
                          <h3 class="line-clamp-2 text-[0.9vw] font-semibold leading-tight text-slate-900">{{ item.itemname }}</h3>
                          <div
                            v-if="item.barcode_prices && item.barcode_prices.length"
                            class="flex items-baseline justify-between gap-1 font-mono text-[0.85vw] font-bold"
                          >
                            <span class="truncate text-slate-600">{{ item.barcode_prices[0].uom || item.barcode_prices[0].barcode }}</span>
                            <span class="flex gap-2 text-indigo-700 tracking-wider">
                              <template v-for="pl in offer.price_lists" :key="pl.price_list">
                                <span v-if="item.barcode_prices[0].prices[pl.price_list] != null">
                                  {{ encryptPrice(item.barcode_prices[0].prices[pl.price_list]) }}
                                </span>
                              </template>
                            </span>
                          </div>
                        </div>
                      </template>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </main>

      <!-- Header -->
      <header
        class="absolute left-0 right-0 top-0 z-40 flex transform items-center justify-between bg-gradient-to-b from-black via-black/90 to-transparent px-8 py-5 transition-all duration-500"
        :class="showControls ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0 pointer-events-none'"
      >
        <div class="flex items-center gap-3">
          <span class="inline-flex h-2 w-2 animate-ping rounded-full bg-emerald-600"></span>
          <h1 class="text-lg font-bold tracking-tight">{{ offer.heading }}</h1>
        </div>
        <div class="flex items-center gap-4 text-xs font-semibold text-slate-300">
          <span class="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 font-bold">{{ offer.items?.length || 0 }} items</span>
          <span class="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-indigo-700">
            {{ !matGlides ? 'All items shown' : isPaused ? 'Paused' : `Gliding · 1 row / ${slideSeconds()}s` }}
          </span>
        </div>
      </header>

      <!-- Controls -->
      <footer
        class="absolute bottom-0 left-0 right-0 z-40 flex transform items-center justify-between bg-gradient-to-t from-black via-black/90 to-transparent px-8 py-6 transition-all duration-500"
        :class="showControls ? 'translate-y-0 opacity-100' : 'translate-y-full opacity-0 pointer-events-none'"
      >
        <div class="flex items-center gap-3">
          <button type="button" class="ctrl-btn text-slate-700" @click="goBack">← Back</button>
          <button type="button" class="ctrl-btn text-amber-800" @click="loadOffer(true)">🔄 Refresh (R)</button>
        </div>
        <div class="flex items-center gap-4">
          <button type="button" class="ctrl-btn text-slate-800" :disabled="!matGlides" @click="nudge(-1)">▲ Back a row</button>
          <button
            type="button"
            class="ctrl-btn px-6"
            :class="isPaused ? 'text-emerald-700' : 'text-amber-800'"
            :disabled="!matGlides"
            @click="togglePause"
          >
            {{ isPaused ? '▶ Resume' : '⏸ Pause' }}
          </button>
          <button type="button" class="ctrl-btn text-slate-800" :disabled="!matGlides" @click="nudge(1)">▼ Next row</button>
        </div>
        <button type="button" class="ctrl-btn text-indigo-700" @click="toggleFullscreen">
          {{ isFullscreen ? '⤡ Exit Fullscreen (F)' : '⛶ Fullscreen (F)' }}
        </button>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import { encryptPrice } from '../encryption.js'
import { initFrappeSocket } from '../services/frappeSocket.js'

const route = useRoute()
const router = useRouter()
const pageaddress = route.params.pageaddress

const loading = ref(true)
const error = ref(null)
const offer = ref(null)
const isPaused = ref(false)
const isFullscreen = ref(!!document.fullscreenElement)
const backButtonRef = ref(null)

const showControls = ref(true)
let controlsTimeout = null

function resetControlsTimer() {
  showControls.value = true
  if (controlsTimeout) clearTimeout(controlsTimeout)
  controlsTimeout = setTimeout(() => {
    showControls.value = false
  }, 3000)
}

// Mat mode: a columns-wide mat of every item that glides upward one row per speed interval.
// Position is kept in rows (glideRows) so a resize never makes the mat jump; only the
// rows inside the visible window are rendered, so long catalogues stay cheap.
// Rows / columns / speed come from SSPL TV Slideshow Settings (Mat Glider section).
const matSettings = computed(() => offer.value?.mat_glider || {})
const clampInt = (v, d) => Math.min(12, Math.max(1, parseInt(v) || d))
const MAT_COLS_C = computed(() => clampInt(matSettings.value.columns, 6))
const MAT_ROWS_C = computed(() => clampInt(matSettings.value.rows, 4))
const matViewport = ref(null)
const matTrack = ref(null)
const matRowPitch = ref(0)
const matRowHeight = ref(0)
const matGap = ref(0)
const matFirstRow = ref(0)
let glideRows = 0
let glideNudge = 0
let glideRaf = null
let glideLastTs = null
let matResizeObserver = null

// Everything fits in one window: show it still instead of looping repeats.
const matGlides = computed(() => (offer.value?.items?.length || 0) > MAT_COLS_C.value * MAT_ROWS_C.value)
const matRows = computed(() => {
  const count = matGlides.value ? MAT_ROWS_C.value + 1 : MAT_ROWS_C.value
  return Array.from({ length: count }, (_, i) => matFirstRow.value + i)
})

function slideSeconds() {
  return parseFloat(matSettings.value.speed) || parseInt(offer.value?.timer) || 8
}

function matItemAt(row, col) {
  const items = offer.value?.items || []
  if (!items.length) return null
  const i = row * MAT_COLS_C.value + col
  if (!matGlides.value) return i >= 0 && i < items.length ? items[i] : null
  return items[((i % items.length) + items.length) % items.length]
}

function matTileStyle(row, col) {
  const i = row * MAT_COLS_C.value + col
  return {
    animationDelay: `${-((Math.abs(i) * 0.53) % 5).toFixed(2)}s`,
    animationDuration: `${4 + (Math.abs(i) % 3)}s`
  }
}

function measureMat() {
  const el = matViewport.value
  if (!el) return
  const gap = window.innerWidth * 0.011
  const pitch = (el.clientHeight + gap) / MAT_ROWS_C.value
  matGap.value = gap
  matRowPitch.value = pitch
  matRowHeight.value = Math.max(0, pitch - gap)
  applyGlide()
}

// A refresh can change the row count; re-measure so row height follows.
watch(MAT_ROWS_C, () => nextTick(measureMat))

function applyGlide() {
  const first = Math.floor(glideRows)
  if (first !== matFirstRow.value) matFirstRow.value = first
  if (matTrack.value) {
    matTrack.value.style.transform = `translate3d(0, ${-(glideRows * matRowPitch.value)}px, 0)`
  }
}

function glideFrame(ts) {
  if (glideLastTs == null) glideLastTs = ts
  const dt = Math.min((ts - glideLastTs) / 1000, 0.1)
  glideLastTs = ts
  if (matGlides.value) {
    if (!isPaused.value) glideRows += dt / slideSeconds()
    // Prev/Next nudges ease in over a few frames instead of snapping.
    if (glideNudge) {
      const step = Math.abs(glideNudge) < 0.002 ? glideNudge : glideNudge * Math.min(1, dt * 6)
      glideRows += step
      glideNudge -= step
    }
  }
  applyGlide()
  glideRaf = requestAnimationFrame(glideFrame)
}

function startGlide() {
  if (glideRaf) return
  glideLastTs = null
  nextTick(() => {
    measureMat()
    if (matViewport.value && !matResizeObserver && typeof ResizeObserver !== 'undefined') {
      matResizeObserver = new ResizeObserver(measureMat)
      matResizeObserver.observe(matViewport.value)
    }
    if (!glideRaf) glideRaf = requestAnimationFrame(glideFrame)
  })
}

function stopGlide() {
  if (glideRaf) cancelAnimationFrame(glideRaf)
  glideRaf = null
  glideNudge = 0
  if (matResizeObserver) {
    matResizeObserver.disconnect()
    matResizeObserver = null
  }
}

function nudge(rows) {
  if (matGlides.value) glideNudge += rows
}

function togglePause() {
  isPaused.value = !isPaused.value
}

function toggleFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen().catch(err => console.error(err))
  } else if (document.documentElement.requestFullscreen) {
    document.documentElement.requestFullscreen().catch(err => console.error(err))
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

// Opened from the TV live display: step back; a direct link goes to that catalogue.
function goBack() {
  if (typeof window.history.state?.back === 'string') router.back()
  else if (pageaddress) router.push({ name: 'OfferPage', params: { pageaddress } })
  else router.push({ name: 'Catelogue' })
}

async function loadOffer(silent = false) {
  if (!pageaddress) {
    loading.value = false
    error.value = 'Invalid page address'
    return
  }
  if (!silent) loading.value = true
  error.value = null
  try {
    const res = await frappeGet('ssplbilling.api.offer_api.get_offer_details', { pageaddress })
    if (res) {
      // Blank cipher_map means encryption is off; clear any stale key.
      const cipher = (res.cipher_map || '').trim()
      if (cipher) localStorage.setItem('wb-cipher', cipher)
      else localStorage.removeItem('wb-cipher')
      // Plain item tiles, so each template row is shown as its variants.
      res.items = res.items.flatMap(item => (item.is_template ? item.variants : [item]))
      offer.value = res
      document.title = `${res.heading} | Mat`
    } else if (!silent) {
      error.value = 'Catalogue not found'
    }
  } catch (err) {
    console.error(err)
    if (!silent) error.value = err.message || 'Failed to load catalogue'
  } finally {
    if (!silent) loading.value = false
  }
}

function handleKeyDown(event) {
  if (event.ctrlKey || event.metaKey || event.altKey) return
  resetControlsTimer()
  const key = event.key
  const code = event.keyCode
  if (key === 'ArrowDown' || key === 'ArrowRight' || code === 40 || code === 39) {
    event.preventDefault()
    nudge(1)
  } else if (key === 'ArrowUp' || key === 'ArrowLeft' || code === 38 || code === 37) {
    event.preventDefault()
    nudge(-1)
  } else if (
    key === ' ' || key === 'Enter' || key === 'Select' || key === 'OK' || key === 'Accept' ||
    key === 'MediaPlayPause' || code === 13 || code === 23 || code === 32 || code === 179
  ) {
    // Enter on a focused control clicks it; otherwise it toggles the glide.
    if (document.activeElement?.tagName === 'BUTTON') return
    event.preventDefault()
    togglePause()
  } else if (key === 'Escape' || key === 'Backspace' || code === 27 || code === 8 || code === 10009 || code === 461) {
    if (document.fullscreenElement) return // browser leaves fullscreen first
    event.preventDefault()
    goBack()
  } else if (key === 'r' || key === 'R') {
    event.preventDefault()
    loadOffer(true)
  } else if (key === 'f' || key === 'F') {
    event.preventDefault()
    toggleFullscreen()
  }
}

// Live refresh: the backend broadcasts offer_page_update to the website room.
let offerSocket = null
let offerHandler = null
let offerRefreshTimer = null

function setupOfferSocket() {
  initFrappeSocket().then(socket => {
    if (!socket) return
    offerSocket = socket
    offerHandler = data => {
      if (!data) return
      const affectsThisPage =
        (data.type === 'offer' && data.pageaddress === pageaddress) ||
        (data.type === 'item' && data.item_code && offer.value?.items?.some(i => i.itemcode === data.item_code))
      if (!affectsThisPage) return
      if (offerRefreshTimer) clearTimeout(offerRefreshTimer)
      offerRefreshTimer = setTimeout(() => {
        offerRefreshTimer = null
        loadOffer(true)
      }, 800)
    }
    socket.on('offer_page_update', offerHandler)
  })
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeyDown)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  setupOfferSocket()
  resetControlsTimer()
  await loadOffer()
  if (!offer.value) {
    nextTick(() => backButtonRef.value?.focus())
    return
  }
  // ?start=<item index> opens with that item's row at the top.
  const start = parseInt(route.query.start) || 0
  glideRows = matGlides.value ? Math.floor(Math.max(0, start) / MAT_COLS_C.value) : 0
  matFirstRow.value = Math.floor(glideRows)
  startGlide()
})

onBeforeUnmount(() => {
  stopGlide()
  window.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  if (controlsTimeout) clearTimeout(controlsTimeout)
  if (offerRefreshTimer) clearTimeout(offerRefreshTimer)
  if (offerSocket && offerHandler) offerSocket.off('offer_page_update', offerHandler)
})
</script>

<style scoped>
.ctrl-btn {
  border-radius: 0.75rem;
  border: 1px solid rgb(226 232 240);
  background: #fff;
  padding: 0.625rem 1.25rem;
  font-size: 0.75rem;
  font-weight: 700;
  transition: background-color 0.15s, transform 0.15s;
}
.ctrl-btn:hover {
  background: rgb(241 245 249);
}
.ctrl-btn:active {
  transform: scale(0.95);
}
.ctrl-btn:disabled {
  opacity: 0.3;
  pointer-events: none;
}
.ctrl-btn:focus-visible {
  outline: 3px solid #818cf8;
  outline-offset: 3px;
}

/* Mat: flat surface (no tilt / taper), tiles bob out of phase. */
.mat-stage {
  background: #000;
}
.mat-tile {
  box-shadow: 0 18px 30px -12px rgba(15, 23, 42, 0.28), 0 4px 10px -4px rgba(15, 23, 42, 0.12);
  animation-name: mat-float;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  animation-direction: alternate;
}
@keyframes mat-float {
  from { transform: translateY(0); }
  to { transform: translateY(-0.9vh); }
}
.mat-viewport {
  -webkit-mask-image: linear-gradient(to bottom, transparent 0, #000 5%, #000 95%, transparent 100%);
  mask-image: linear-gradient(to bottom, transparent 0, #000 5%, #000 95%, transparent 100%);
}
@media (prefers-reduced-motion: reduce) {
  .mat-tile { animation: none; }
}
</style>
