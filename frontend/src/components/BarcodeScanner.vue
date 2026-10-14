<template>
  <div class="fixed inset-0 z-40 flex flex-col bg-black">
    <div class="flex items-center justify-between gap-2 px-4 py-3 text-white">
      <span class="text-base font-semibold">Scan Barcode</span>
      <div class="flex gap-2">
        <button
          v-if="zoomLevels.length > 1"
          type="button"
          class="rounded-full bg-white/15 px-3 py-1.5 text-sm font-semibold tabular-nums hover:bg-white/25"
          title="Zoom: hold the phone further back and zoom in so the camera can focus"
          @click="cycleZoom"
        >{{ zoomLabel }}</button>
        <button
          v-if="torchAvailable"
          type="button"
          class="rounded-full px-4 py-1.5 text-sm font-semibold"
          :class="torchOn ? 'bg-yellow-400 text-black' : 'bg-white/15 hover:bg-white/25'"
          @click="toggleTorch"
        >Light</button>
        <button
          type="button"
          class="rounded-full bg-white/15 px-4 py-1.5 text-sm font-semibold hover:bg-white/25"
          @click="close"
        >Close</button>
      </div>
    </div>

    <div ref="viewRef" class="relative flex-1 overflow-hidden" @pointerdown="tapToFocus">
      <video ref="videoRef" class="h-full w-full object-cover" playsinline muted autoplay></video>

      <!-- Aiming guide: only this area is decoded. Border colour shows scan state. -->
      <div v-if="!error" class="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div
          ref="boxRef"
          class="relative h-44 w-[85%] max-w-md rounded-2xl border-[3px] shadow-[0_0_0_9999px_rgba(0,0,0,0.45)] transition-colors duration-200"
          :class="boxClass"
        >
          <div v-if="!foundCode" class="scan-line absolute inset-x-3 h-0.5 bg-red-500/90"></div>
          <div v-else class="absolute inset-0 flex items-center justify-center rounded-xl bg-emerald-500/25">
            <span class="break-all px-3 text-center font-mono text-2xl font-black text-white drop-shadow">{{ foundCode }}</span>
          </div>
        </div>
      </div>

      <!-- Tap-to-focus ring -->
      <div
        v-if="focusRing"
        :key="focusRing.key"
        class="focus-ring pointer-events-none absolute h-16 w-16 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-yellow-300"
        :style="{ left: focusRing.x + 'px', top: focusRing.y + 'px' }"
      ></div>

      <div v-if="error" class="absolute inset-0 flex items-center justify-center p-6">
        <div class="max-w-sm rounded-xl bg-white/10 p-4 text-center text-sm text-white">{{ error }}</div>
      </div>
      <div v-else class="pointer-events-none absolute inset-x-0 bottom-3 space-y-1.5 px-4 text-center text-white">
        <div class="text-base font-semibold" :class="hintWarn ? 'text-amber-300' : foundCode ? 'text-emerald-300' : 'text-white'">
          {{ starting ? 'Starting camera…' : foundCode ? 'Found!' : hint }}
        </div>
        <div v-if="!starting && !foundCode" class="text-xs text-white/75">Hold 15–20 cm away · tap the screen to focus</div>
        <div v-if="ocrNote && !foundCode" class="font-mono text-xs text-sky-200">{{ ocrNote }}</div>
        <div v-if="status" class="mx-auto inline-flex items-center gap-1.5 rounded-lg bg-black/55 px-2 py-1 font-mono text-[11px] text-white/85">
          <span class="h-2 w-2 rounded-full" :class="alive ? 'bg-emerald-400' : 'bg-red-500'"></span>
          {{ status }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Full-screen camera barcode scanner.
 * Every frame the aiming box is cropped out of the video and decoded by the native
 * BarcodeDetector (when present) and by ZXing, so a phone whose native detector
 * silently returns nothing still scans. The printed code under the bars is read by
 * OCR as a fallback; OCR candidates are only accepted once `verify(text)` confirms
 * the code exists. Emits `detected` once with the decoded text.
 *
 * Feedback: a live frame rate (red dot = scan loop stalled), brightness/sharpness
 * hints, OCR progress, and a green box with the code before closing. The main back
 * camera is always used (see pickPrimaryCamera); zoom and tap-to-focus help phones
 * whose camera cannot focus up close.
 */
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  // async (text) => boolean — confirms an OCR reading before it is accepted
  verify: { type: Function, default: null },
})
const emit = defineEmits(['detected', 'close'])

const viewRef = ref(null)
const videoRef = ref(null)
const boxRef = ref(null)
const error = ref('')
const starting = ref(true)
const status = ref('')
const torchAvailable = ref(false)
const torchOn = ref(false)
const hint = ref('Fit the barcode or its printed number inside the box')
const hintWarn = ref(false)
const ocrNote = ref('')
const foundCode = ref('')
const alive = ref(true)
const zoomLevels = ref([])
const zoom = ref(1)
const focusRing = ref(null)

// 1D formats only: item labels carry linear barcodes, and each extra format costs decode time
const NATIVE_FORMATS = ['code_128', 'ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_39', 'code_93', 'codabar', 'itf']
const SCAN_INTERVAL = 150
const OCR_INTERVAL = 1200
// OCR (Tesseract WASM + language data) starts only if the bars have not read by then,
// so it doesn't compete with the camera start-up and the bar decoders
const OCR_START_DELAY = 2500
const FOUND_DELAY = 150
// Decoding a smaller copy of the aiming box is several times faster and still
// leaves enough pixels per bar for labels filling the box
const DECODE_WIDTH = 800
// deviceId of the main back camera, so later scans open it without a second camera start
const LENS_KEY = 'bs-primary-lens'
const DEFAULT_ZOOM = 2
// Rough guide values for the hints only; decoding always runs regardless
const DARK_BELOW = 45
const BLURRY_BELOW = 6

let stream = null
let track = null
let nativeDetector = null
let zxingReader = null
let ocrWorker = null
let ocrBusy = false
let lastOcrAt = 0
let lastOcrTokens = []
const rejectedOcr = new Set()
let scanTimer = null
let foundTimer = null
let focusTimer = null
let ocrStartTimer = null
let tickCount = 0
let lastTickAt = 0
let fpsWindowStart = 0
let fpsFrames = 0
let fps = 0
let brightness = null
let sharpness = null
let done = false
const scanCanvas = document.createElement('canvas')
const ocrCanvas = document.createElement('canvas')
const qualityCanvas = document.createElement('canvas')

const boxClass = computed(() => {
  if (foundCode.value) return 'border-emerald-400'
  if (hintWarn.value) return 'border-amber-400'
  return 'border-white/80'
})
const zoomLabel = computed(() => `${Number(zoom.value.toFixed(1))}×`)

function cameraErrorMessage(e) {
  if (!window.isSecureContext) {
    return `Live scanning needs a secure connection. Open this page with https:// instead of http:// (${location.host}).`
  }
  if (e?.name === 'NotAllowedError') return 'Camera permission was denied. Allow camera access in the browser settings and try again.'
  if (e?.name === 'NotFoundError' || e?.name === 'OverconstrainedError') return 'No camera found on this device.'
  return 'Could not start the camera: ' + (e?.message || e)
}

function found(text) {
  if (done || !text) return
  done = true
  clearTimeout(scanTimer)
  const code = String(text).trim()
  foundCode.value = code
  try { navigator.vibrate?.(80) } catch (e) { /* not supported */ }
  // Freeze the frame so the code is shown over what was scanned; stopping the
  // tracks right away blanks the video on some browsers
  try { videoRef.value?.pause() } catch (e) { /* ignore */ }
  foundTimer = setTimeout(() => {
    stop()
    emit('detected', code)
  }, FOUND_DELAY)
}

/** Aiming box in video pixels, accounting for object-cover scaling. `extraBelow` grows it downwards. */
function boxInVideo(extraBelow = 0) {
  const video = videoRef.value
  const vw = video.videoWidth, vh = video.videoHeight
  const view = viewRef.value.getBoundingClientRect()
  const box = boxRef.value.getBoundingClientRect()
  const scale = Math.max(view.width / vw, view.height / vh)
  const offX = (vw * scale - view.width) / 2
  const offY = (vh * scale - view.height) / 2
  const x = Math.max(0, (box.left - view.left + offX) / scale)
  const y = Math.max(0, (box.top - view.top + offY) / scale)
  const w = Math.min(vw - x, box.width / scale)
  const h = Math.min(vh - y, (box.height * (1 + extraBelow)) / scale)
  return { x, y, w, h }
}

function drawCrop(canvas, r, maxWidth, minWidth = 0) {
  const s = Math.min(maxWidth / r.w, Math.max(1, minWidth / r.w))
  canvas.width = Math.round(r.w * s)
  canvas.height = Math.round(r.h * s)
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  ctx.drawImage(videoRef.value, r.x, r.y, r.w, r.h, 0, 0, canvas.width, canvas.height)
  return canvas
}

/** Mean brightness and horizontal edge strength (barcode bars are vertical) of a small copy of the crop. */
function measureQuality(source) {
  const w = 160
  const h = Math.max(8, Math.round((source.height / source.width) * w))
  qualityCanvas.width = w
  qualityCanvas.height = h
  const ctx = qualityCanvas.getContext('2d', { willReadFrequently: true })
  ctx.drawImage(source, 0, 0, w, h)
  const px = ctx.getImageData(0, 0, w, h).data
  let lum = 0, edge = 0, prev = 0
  for (let i = 0, n = 0; i < px.length; i += 4, n++) {
    const y = 0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]
    lum += y
    if (n % w) edge += Math.abs(y - prev)
    prev = y
  }
  brightness = Math.round(lum / (w * h))
  sharpness = Math.round(edge / ((w - 1) * h))
  if (brightness < DARK_BELOW) {
    setHint(torchAvailable.value && !torchOn.value ? 'Too dark — tap Light' : 'Too dark — add more light', true)
  } else if (sharpness < BLURRY_BELOW) {
    setHint('Blurry or no barcode — move back a little, tap to focus', true)
  } else {
    setHint('Reading… hold steady', false)
  }
}

function setHint(text, warn) {
  hint.value = text
  hintWarn.value = warn
}

async function initNative() {
  if (!('BarcodeDetector' in window)) return
  try {
    const supported = await window.BarcodeDetector.getSupportedFormats()
    const formats = NATIVE_FORMATS.filter(f => supported.includes(f))
    if (formats.length) nativeDetector = new window.BarcodeDetector({ formats })
  } catch (e) { /* unusable native detector: ZXing covers it */ }
}

async function initZxing() {
  const [{ BrowserMultiFormatReader }, { DecodeHintType, BarcodeFormat }] = await Promise.all([
    import('@zxing/browser'),
    import('@zxing/library'),
  ])
  // No TRY_HARDER: it multiplies the decode time on the main thread, and the next
  // frame (150 ms later) is a cheaper retry than a slow, exhaustive pass on this one
  const hints = new Map()
  hints.set(DecodeHintType.POSSIBLE_FORMATS, [
    BarcodeFormat.CODE_128, BarcodeFormat.EAN_13, BarcodeFormat.EAN_8, BarcodeFormat.UPC_A,
    BarcodeFormat.UPC_E, BarcodeFormat.CODE_39, BarcodeFormat.CODE_93, BarcodeFormat.ITF,
    BarcodeFormat.CODABAR,
  ])
  zxingReader = new BrowserMultiFormatReader(hints)
}

async function initOcr() {
  const { createWorker } = await import('tesseract.js')
  const base = new URL(import.meta.env.BASE_URL + 'ocr/', location.href).href
  const worker = await createWorker('eng', 1, {
    workerPath: base + 'worker.min.js',
    corePath: base,
    langPath: base,
  })
  await worker.setParameters({
    tessedit_char_whitelist: '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-',
    tessedit_pageseg_mode: '6', // uniform block: sparse modes (11/12) misread the bars as letters
  })
  if (done) { worker.terminate(); return }
  ocrWorker = worker
}

function updateStatus() {
  const bars = [nativeDetector && 'native', zxingReader && 'zxing'].filter(Boolean).join('+') || 'loading'
  const video = videoRef.value
  const settings = track?.getSettings?.() || {}
  const parts = [
    track?.label ? track.label.replace(/,?\s*facing back/i, '') : '',
    `${fps} fps`,
    `bars: ${bars}`,
    `text: ${ocrWorker ? 'on' : 'loading'}`,
    video?.videoWidth ? `${video.videoWidth}×${video.videoHeight}` : '',
    settings.zoom ? `zoom ${Number(settings.zoom.toFixed(1))}×` : '',
    settings.focusMode ? `focus ${settings.focusMode}` : '',
    brightness !== null ? `light ${brightness}` : '',
    sharpness !== null ? `sharp ${sharpness}` : '',
  ]
  status.value = parts.filter(Boolean).join(' · ')
}

async function decodeBars(canvas) {
  if (nativeDetector) {
    try {
      const codes = await nativeDetector.detect(canvas)
      if (codes.length) return codes[0].rawValue
    } catch (e) { /* frame not ready */ }
  }
  // ZXing every other tick when native also runs (it is the slower of the two)
  if (zxingReader && (!nativeDetector || tickCount % 2 === 0)) {
    try {
      return zxingReader.decodeFromCanvas(canvas).getText()
    } catch (e) { /* NotFoundException: nothing in this frame */ }
  }
  return ''
}

/** Tokens that could be a printed item code: no OCR noise from the bars themselves. */
function ocrTokens(text) {
  return [...new Set(
    (text || '').toUpperCase().split(/\s+/)
      .map(t => t.replace(/^-+|-+$/g, ''))
      .filter(t => t.length >= 3 && t.length <= 20 && !/^(.)\1+$/.test(t)),
  )]
}

async function readText() {
  ocrBusy = true
  lastOcrAt = Date.now()
  try {
    const canvas = drawCrop(ocrCanvas, boxInVideo(0.25), 1400, 900)
    const { data } = await ocrWorker.recognize(canvas)
    if (done) return
    const tokens = ocrTokens(data?.text)
    ocrNote.value = tokens.length ? `Text seen: ${tokens.slice(0, 4).join(' ')}` : 'Text: nothing readable yet'
    // Accept only a token seen in two reads in a row, then confirm it with the server
    const stable = tokens.filter(t => lastOcrTokens.includes(t) && !rejectedOcr.has(t))
    lastOcrTokens = tokens
    for (const t of stable) {
      ocrNote.value = `Checking ${t}…`
      const ok = props.verify ? await props.verify(t) : true
      if (done) return
      if (ok) return found(t)
      rejectedOcr.add(t)
      ocrNote.value = `${t} is not an item code`
    }
  } catch (e) {
    console.warn('[BarcodeScanner] OCR', e)
  } finally {
    ocrBusy = false
  }
}

function countFrame() {
  const now = Date.now()
  lastTickAt = now
  fpsFrames++
  if (now - fpsWindowStart >= 1000) {
    fps = Math.round((fpsFrames * 1000) / (now - fpsWindowStart))
    fpsFrames = 0
    fpsWindowStart = now
    updateStatus()
  }
}

async function tick() {
  if (done) return
  try {
    const video = videoRef.value
    if (video && video.readyState >= 2 && video.videoWidth) {
      tickCount++
      countFrame()
      const canvas = drawCrop(scanCanvas, boxInVideo(), DECODE_WIDTH)
      if (tickCount % 4 === 0) measureQuality(canvas)
      const code = await decodeBars(canvas)
      if (code) return found(code)
      if (ocrWorker && !ocrBusy && Date.now() - lastOcrAt > OCR_INTERVAL) readText()
    }
  } catch (e) {
    // Never let one bad frame end the scan loop
    console.warn('[BarcodeScanner] frame', e)
  } finally {
    if (!done) scanTimer = setTimeout(tick, SCAN_INTERVAL)
  }
}

// Red status dot when no frame has been scanned for a while (camera frozen or loop stalled)
let aliveTimer = null
function watchAlive() {
  aliveTimer = setInterval(() => {
    alive.value = !lastTickAt || Date.now() - lastTickAt < 1500
  }, 500)
}

/** Continuous autofocus, re-sent with every constraint change so a zoom or tap-to-focus
 * call can't leave the camera on a fixed focus. */
function focusConstraint() {
  const caps = track?.getCapabilities?.() || {}
  return caps.focusMode?.includes('continuous') ? { focusMode: 'continuous' } : {}
}

async function setZoom(value) {
  try {
    await track.applyConstraints({ advanced: [{ zoom: value, ...focusConstraint() }] })
    zoom.value = track.getSettings?.().zoom || value
  } catch (e) { /* zoom not applied */ }
  updateStatus()
}

function cycleZoom() {
  const levels = zoomLevels.value
  const i = levels.findIndex(z => Math.abs(z - zoom.value) < 0.05)
  setZoom(levels[(i + 1) % levels.length])
}

async function setupTrack() {
  const caps = track.getCapabilities?.() || {}
  // Close-up barcodes stay blurry without continuous autofocus
  if (caps.focusMode?.includes('continuous')) {
    try { await track.applyConstraints({ advanced: [{ focusMode: 'continuous' }] }) } catch (e) { /* ignore */ }
  }
  torchAvailable.value = !!caps.torch
  torchOn.value = false
  // Zooming in lets the phone be held far enough back for the lens to focus
  zoomLevels.value = []
  zoom.value = 1
  if (caps.zoom && caps.zoom.max > 1) {
    const levels = [1, 2, 3].filter(z => z >= caps.zoom.min && z <= caps.zoom.max)
    if (levels.length > 1) {
      zoomLevels.value = levels
      await setZoom(Math.min(DEFAULT_ZOOM, caps.zoom.max))
    }
  }
}

async function startCamera(deviceId = null) {
  const video = deviceId
    ? { deviceId: { exact: deviceId }, width: { ideal: 1920 }, height: { ideal: 1080 } }
    : { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } }
  stream = await navigator.mediaDevices.getUserMedia({ video, audio: false })
  if (done) return stop()
  track = stream.getVideoTracks()[0]
  await setupTrack()
  videoRef.value.srcObject = stream
  await videoRef.value.play()
  starting.value = false
}

/**
 * The phone's main (wide) back camera. The browser's default back camera is often the
 * ultra-wide or a fixed-focus lens, which cannot focus at barcode distance.
 * Labels are only filled in after camera permission is granted.
 *   Android: "camera2 0, facing back" — the lowest camera2 number is the main sensor
 *   iPhone:  "Back Camera" is the main lens; the others are named Ultra Wide, Telephoto, …
 */
function pickPrimaryCamera(cams) {
  const back = cams.filter(d => /back|rear|environment/i.test(d.label))
  if (!back.length) return null
  const numbered = back
    .map(d => ({ d, n: /camera2? (\d+)/i.exec(d.label) }))
    .filter(x => x.n)
    .sort((a, b) => Number(a.n[1]) - Number(b.n[1]))
  if (numbered.length) return numbered[0].d
  return back.find(d => /^back camera$/i.test(d.label.trim()))
    || back.find(d => !/ultra|tele|depth|macro|dual|triple/i.test(d.label))
    || back[0]
}

const hasAutofocus = () => !!track?.getCapabilities?.().focusMode?.includes('continuous')

/**
 * Switch to the main back camera if the browser opened another one. A name is only a
 * guess, so the camera must also report continuous autofocus; when it doesn't, the
 * other back cameras are tried in turn and the first that does is kept.
 */
async function usePrimaryCamera() {
  let cams = []
  try {
    cams = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput')
  } catch (e) { return }
  const primary = pickPrimaryCamera(cams)
  if (!primary || done) return
  const back = cams.filter(d => /back|rear|environment/i.test(d.label))
  const candidates = [primary, ...back.filter(d => d.deviceId !== primary.deviceId)]
  const current = () => track?.getSettings?.().deviceId

  for (const cam of candidates) {
    if (done) return
    if (current() !== cam.deviceId) {
      stopStream()
      starting.value = true
      try { await startCamera(cam.deviceId) } catch (e) { continue }
    }
    if (hasAutofocus()) {
      try { localStorage.setItem(LENS_KEY, cam.deviceId) } catch (e) { /* storage blocked */ }
      return
    }
  }
  // No camera reports autofocus (some browsers hide it): settle on the main one by name
  if (done || current() === primary.deviceId) return
  stopStream()
  starting.value = true
  try {
    await startCamera(primary.deviceId)
    try { localStorage.setItem(LENS_KEY, primary.deviceId) } catch (e) { /* storage blocked */ }
  } catch (e) {
    console.error('[BarcodeScanner] main camera', e)
    try { await startCamera() } catch (err) { error.value = cameraErrorMessage(err) }
  }
}

/** Best effort: browsers that ignore points of interest still refocus on single-shot. */
async function tapToFocus(e) {
  if (!track || done) return
  const view = viewRef.value.getBoundingClientRect()
  const x = e.clientX - view.left
  const y = e.clientY - view.top
  focusRing.value = { x, y, key: Date.now() }
  clearTimeout(focusTimer)
  const caps = track.getCapabilities?.() || {}
  const advanced = { zoom: zoom.value }
  if (caps.pointsOfInterest || 'pointsOfInterest' in (track.getSettings?.() || {})) {
    advanced.pointsOfInterest = [{ x: x / view.width, y: y / view.height }]
  }
  if (caps.focusMode?.includes('single-shot')) advanced.focusMode = 'single-shot'
  if (!caps.zoom) delete advanced.zoom
  if (Object.keys(advanced).length) {
    try { await track.applyConstraints({ advanced: [advanced] }) } catch (err) { /* ignore */ }
  }
  focusTimer = setTimeout(async () => {
    focusRing.value = null
    if (track && caps.focusMode?.includes('continuous')) {
      const keep = caps.zoom ? { zoom: zoom.value } : {}
      try { await track.applyConstraints({ advanced: [{ ...keep, focusMode: 'continuous' }] }) } catch (err) { /* ignore */ }
    }
    updateStatus()
  }, 1500)
}

async function toggleTorch() {
  try {
    await track.applyConstraints({ advanced: [{ torch: !torchOn.value }] })
    torchOn.value = !torchOn.value
  } catch (e) { torchAvailable.value = false }
}

async function start() {
  if (!navigator.mediaDevices?.getUserMedia) {
    error.value = cameraErrorMessage(null)
    return
  }
  // Open the main back camera found on an earlier scan straight away
  let savedLens = ''
  try { savedLens = localStorage.getItem(LENS_KEY) || '' } catch (e) { /* storage blocked */ }
  try {
    await Promise.all([
      (savedLens ? startCamera(savedLens).catch(() => startCamera()) : startCamera()),
      initNative(),
    ])
  } catch (e) {
    console.error('[BarcodeScanner]', e)
    error.value = cameraErrorMessage(e)
    stop()
    return
  }
  await usePrimaryCamera()
  if (done || error.value) return
  fpsWindowStart = Date.now()
  updateStatus()
  watchAlive()
  tick()
  initZxing().then(updateStatus).catch(e => console.error('[BarcodeScanner] ZXing', e))
  ocrStartTimer = setTimeout(() => {
    if (!done) initOcr().then(updateStatus).catch(e => console.error('[BarcodeScanner] OCR', e))
  }, OCR_START_DELAY)
}

function stopStream() {
  stream?.getTracks().forEach(t => t.stop())
  stream = null
  track = null
}

function stop() {
  clearTimeout(scanTimer)
  scanTimer = null
  clearTimeout(focusTimer)
  clearTimeout(ocrStartTimer)
  clearInterval(aliveTimer)
  stopStream()
  ocrWorker?.terminate()
  ocrWorker = null
}

function close() {
  done = true
  clearTimeout(foundTimer)
  stop()
  emit('close')
}

function onKeydown(e) {
  if (e.key === 'Escape') close()
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  start()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  done = true
  clearTimeout(foundTimer)
  stop()
})
</script>

<style scoped>
.scan-line {
  animation: scan 1.8s ease-in-out infinite alternate;
}
@keyframes scan {
  from { top: 12%; }
  to { top: 88%; }
}
.focus-ring {
  animation: focus-ring 0.6s ease-out forwards;
}
@keyframes focus-ring {
  from { transform: translate(-50%, -50%) scale(1.6); opacity: 0; }
  to { transform: translate(-50%, -50%) scale(1); opacity: 1; }
}
</style>
