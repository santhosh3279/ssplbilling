<template>
  <div class="fixed inset-0 z-40 flex flex-col bg-black">
    <div class="flex items-center justify-between px-4 py-3 text-white">
      <span class="text-base font-semibold">Scan Barcode</span>
      <button
        type="button"
        class="rounded-full bg-white/15 px-4 py-1.5 text-sm font-semibold hover:bg-white/25"
        @click="close"
      >Close</button>
    </div>

    <div class="relative flex-1 overflow-hidden">
      <video ref="videoRef" class="h-full w-full object-cover" playsinline muted autoplay></video>

      <!-- Aiming guide -->
      <div v-if="!error" class="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div class="relative h-40 w-[80%] max-w-sm rounded-2xl border-2 border-white/80 shadow-[0_0_0_9999px_rgba(0,0,0,0.45)]">
          <div class="scan-line absolute inset-x-3 h-0.5 bg-red-500/90"></div>
        </div>
      </div>

      <div v-if="error" class="absolute inset-0 flex items-center justify-center p-6">
        <div class="max-w-sm rounded-xl bg-white/10 p-4 text-center text-sm text-white">{{ error }}</div>
      </div>
      <div v-else-if="starting" class="absolute inset-x-0 bottom-6 text-center text-sm text-white/80">Starting camera…</div>
      <div v-else class="absolute inset-x-0 bottom-6 text-center text-sm text-white/80">Point the camera at a barcode</div>
    </div>
  </div>
</template>

<script setup>
/**
 * Full-screen camera barcode scanner.
 * Uses the browser's native BarcodeDetector when available (Android Chrome) and
 * falls back to a lazily loaded ZXing decoder elsewhere (iOS Safari, Firefox).
 * Emits `detected` once with the decoded text, then stops the camera.
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'

const emit = defineEmits(['detected', 'close'])

const videoRef = ref(null)
const error = ref('')
const starting = ref(true)

let stream = null
let zxingControls = null
let scanTimer = null
let done = false

const NATIVE_FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'code_93', 'codabar', 'itf', 'qr_code']

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

async function startNative() {
  const supported = await window.BarcodeDetector.getSupportedFormats()
  const formats = NATIVE_FORMATS.filter(f => supported.includes(f))
  if (!formats.length) return false
  const detector = new window.BarcodeDetector({ formats })

  stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
    audio: false,
  })
  if (done) { stop(); return true }
  videoRef.value.srcObject = stream
  await videoRef.value.play()
  starting.value = false

  const tick = async () => {
    if (done) return
    try {
      const codes = await detector.detect(videoRef.value)
      if (codes.length) return found(codes[0].rawValue)
    } catch (e) { /* frame not ready yet */ }
    scanTimer = setTimeout(tick, 120)
  }
  tick()
  return true
}

async function startZxing() {
  const { BrowserMultiFormatReader } = await import('@zxing/browser')
  if (done) return
  const reader = new BrowserMultiFormatReader()
  zxingControls = await reader.decodeFromConstraints(
    { video: { facingMode: { ideal: 'environment' } }, audio: false },
    videoRef.value,
    (result) => { if (result) found(result.getText()) },
  )
  starting.value = false
  if (done) stop()
}

async function start() {
  if (!navigator.mediaDevices?.getUserMedia) {
    error.value = cameraErrorMessage(null)
    return
  }
  try {
    const usedNative = 'BarcodeDetector' in window && await startNative()
    if (!usedNative) await startZxing()
  } catch (e) {
    console.error('[BarcodeScanner]', e)
    error.value = cameraErrorMessage(e)
    stop()
  }
}

function stop() {
  clearTimeout(scanTimer)
  scanTimer = null
  zxingControls?.stop()
  zxingControls = null
  stream?.getTracks().forEach(t => t.stop())
  stream = null
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
