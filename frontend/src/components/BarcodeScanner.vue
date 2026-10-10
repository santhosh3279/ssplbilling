<template>
  <div class="fixed inset-0 z-40 flex flex-col bg-black">
    <div class="flex items-center justify-between gap-2 px-4 py-3 text-white">
      <span class="text-base font-semibold">Scan Barcode</span>
      <div class="flex gap-2">
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

    <div ref="viewRef" class="relative flex-1 overflow-hidden">
      <video ref="videoRef" class="h-full w-full object-cover" playsinline muted autoplay></video>

      <!-- Aiming guide: only this area is decoded -->
      <div v-if="!error" class="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div ref="boxRef" class="relative h-44 w-[85%] max-w-md rounded-2xl border-2 border-white/80 shadow-[0_0_0_9999px_rgba(0,0,0,0.45)]">
          <div class="scan-line absolute inset-x-3 h-0.5 bg-red-500/90"></div>
        </div>
      </div>

      <div v-if="error" class="absolute inset-0 flex items-center justify-center p-6">
        <div class="max-w-sm rounded-xl bg-white/10 p-4 text-center text-sm text-white">{{ error }}</div>
      </div>
      <div v-else class="absolute inset-x-0 bottom-4 space-y-1 px-4 text-center text-white/80">
        <div class="text-sm">{{ starting ? 'Starting camera…' : 'Fit the barcode or its printed number inside the box' }}</div>
        <div v-if="status" class="font-mono text-[11px] text-white/50">{{ status }}</div>
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
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'

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

const NATIVE_FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'code_93', 'codabar', 'itf', 'qr_code']
const SCAN_INTERVAL = 150
const OCR_INTERVAL = 1200

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
let tickCount = 0
let done = false
const scanCanvas = document.createElement('canvas')
const ocrCanvas = document.createElement('canvas')

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
  try { navigator.vibrate?.(80) } catch (e) { /* not supported */ }
  stop()
  emit('detected', String(text).trim())
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
  const hints = new Map()
  hints.set(DecodeHintType.TRY_HARDER, true)
  hints.set(DecodeHintType.POSSIBLE_FORMATS, [
    BarcodeFormat.CODE_128, BarcodeFormat.EAN_13, BarcodeFormat.EAN_8, BarcodeFormat.UPC_A,
    BarcodeFormat.UPC_E, BarcodeFormat.CODE_39, BarcodeFormat.CODE_93, BarcodeFormat.ITF,
    BarcodeFormat.CODABAR, BarcodeFormat.QR_CODE,
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
  const res = video?.videoWidth ? `${video.videoWidth}×${video.videoHeight}` : ''
  status.value = `bars: ${bars} · text: ${ocrWorker ? 'on' : 'loading'}${res ? ' · ' + res : ''}`
}

async function decodeBars() {
  const canvas = drawCrop(scanCanvas, boxInVideo(), 1280)
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
    // Accept only a token seen in two reads in a row, then confirm it with the server
    const stable = tokens.filter(t => lastOcrTokens.includes(t) && !rejectedOcr.has(t))
    lastOcrTokens = tokens
    for (const t of stable) {
      const ok = props.verify ? await props.verify(t) : true
      if (done) return
      if (ok) return found(t)
      rejectedOcr.add(t)
    }
  } catch (e) {
    console.warn('[BarcodeScanner] OCR', e)
  } finally {
    ocrBusy = false
  }
}

async function tick() {
  if (done) return
  const video = videoRef.value
  if (video && video.readyState >= 2 && video.videoWidth) {
    tickCount++
    const code = await decodeBars()
    if (code) return found(code)
    if (ocrWorker && !ocrBusy && Date.now() - lastOcrAt > OCR_INTERVAL) readText()
    if (tickCount % 10 === 0) updateStatus()
  }
  if (!done) scanTimer = setTimeout(tick, SCAN_INTERVAL)
}

async function startCamera() {
  stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } },
    audio: false,
  })
  if (done) return stop()
  track = stream.getVideoTracks()[0]
  const caps = track.getCapabilities?.() || {}
  // Close-up barcodes stay blurry without continuous autofocus
  if (caps.focusMode?.includes('continuous')) {
    try { await track.applyConstraints({ advanced: [{ focusMode: 'continuous' }] }) } catch (e) { /* ignore */ }
  }
  torchAvailable.value = !!caps.torch
  videoRef.value.srcObject = stream
  await videoRef.value.play()
  starting.value = false
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
  try {
    await Promise.all([startCamera(), initNative()])
  } catch (e) {
    console.error('[BarcodeScanner]', e)
    error.value = cameraErrorMessage(e)
    stop()
    return
  }
  updateStatus()
  tick()
  initZxing().then(updateStatus).catch(e => console.error('[BarcodeScanner] ZXing', e))
  initOcr().then(updateStatus).catch(e => console.error('[BarcodeScanner] OCR', e))
}

function stop() {
  clearTimeout(scanTimer)
  scanTimer = null
  stream?.getTracks().forEach(t => t.stop())
  stream = null
  track = null
  ocrWorker?.terminate()
  ocrWorker = null
}

function close() {
  done = true
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
</style>
