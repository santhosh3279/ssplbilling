<template>
  <div class="flex w-72 max-w-full items-center gap-2 py-1 pl-1 pr-2">
    <audio
      ref="audioEl"
      :src="src"
      preload="metadata"
      class="hidden"
      @loadedmetadata="onMetadata"
      @play="onPlay"
      @pause="onPause"
      @ended="onEnded"
    />
    <button
      type="button"
      class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
      :title="playing ? 'Pause' : 'Play'"
      @click="toggle"
    >
      <svg v-if="playing" viewBox="0 0 24 24" class="h-7 w-7 fill-current"><path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" /></svg>
      <svg v-else viewBox="0 0 24 24" class="h-7 w-7 fill-current"><path d="M8 5.14v13.72a.5.5 0 0 0 .76.43l10.6-6.86a.5.5 0 0 0 0-.86L8.76 4.71A.5.5 0 0 0 8 5.14z" /></svg>
    </button>

    <div class="min-w-0 flex-1">
      <div
        ref="waveEl"
        class="relative flex h-8 cursor-pointer touch-none items-center gap-[2px]"
        @pointerdown="startSeek"
        @pointermove="moveSeek"
        @pointerup="endSeek"
        @pointercancel="endSeek"
      >
        <span
          v-for="(h, i) in bars"
          :key="i"
          class="min-w-0 flex-1 rounded-full"
          :class="i < playedBars ? 'bg-[#34B7F1]' : 'bg-[var(--color-text-muted)] opacity-50'"
          :style="{ height: `${Math.round(h * 100)}%` }"
        />
        <span
          class="pointer-events-none absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#34B7F1]"
          :style="{ left: `${progress * 100}%` }"
        />
      </div>
      <div class="flex items-center justify-between text-[10px] text-[var(--color-text-muted)]">
        <span>{{ timeLabel }}</span>
        <button
          v-if="playing || rate !== 1"
          type="button"
          class="rounded-full bg-[var(--color-surface-raised)] px-1.5 font-bold text-[var(--color-text)]"
          title="Playback speed"
          @click="cycleRate"
        >{{ rate }}×</button>
      </div>
    </div>
  </div>
</template>

<script>
// Only one voice note plays at a time, as in WhatsApp
let currentAudio = null
</script>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  src: { type: String, required: true },
  // Seeds the stand-in waveform when the audio cannot be decoded
  seed: { type: String, default: '' },
})

const BAR_COUNT = 40
const RATES = [1, 1.5, 2]

const audioEl = ref(null)
const waveEl = ref(null)
const playing = ref(false)
const current = ref(0)
const duration = ref(0)
const rate = ref(1)
const bars = ref(placeholderBars(props.seed))

let frame = 0
let seeking = false

const progress = computed(() => (duration.value ? Math.min(current.value / duration.value, 1) : 0))
const playedBars = computed(() => Math.round(progress.value * BAR_COUNT))
const timeLabel = computed(() => formatTime(playing.value || current.value ? current.value : duration.value))

function formatTime(sec) {
  const s = Math.max(0, Math.floor(sec || 0))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

function placeholderBars(seed) {
  let h = 2166136261
  for (const c of seed || 'voice') h = Math.imul(h ^ c.charCodeAt(0), 16777619)
  return Array.from({ length: BAR_COUNT }, () => {
    h = Math.imul(h ^ (h >>> 15), 2246822507) >>> 0
    return 0.2 + (h % 1000) / 1250
  })
}

async function decodeBars(url) {
  try {
    const buf = await (await fetch(url)).arrayBuffer()
    // An offline context decodes without needing a user gesture or an output device
    const audio = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(buf)
    if (!Number.isFinite(audioEl.value?.duration)) duration.value = audio.duration
    const data = audio.getChannelData(0)
    const size = Math.floor(data.length / BAR_COUNT) || 1
    const peaks = Array.from({ length: BAR_COUNT }, (_, b) => {
      let sum = 0
      for (let j = b * size; j < (b + 1) * size && j < data.length; j++) sum += data[j] * data[j]
      return Math.sqrt(sum / size)
    })
    const max = Math.max(...peaks) || 1
    if (url === props.src) bars.value = peaks.map((p) => 0.15 + (p / max) * 0.85)
  } catch {
    // Keep the stand-in waveform
  }
}

watch(() => props.src, decodeBars, { immediate: true })

function onMetadata() {
  const d = audioEl.value.duration
  if (Number.isFinite(d)) duration.value = d
}

function tick() {
  if (audioEl.value && !seeking) current.value = audioEl.value.currentTime
  if (playing.value) frame = requestAnimationFrame(tick)
}

function onPlay() {
  if (currentAudio && currentAudio !== audioEl.value) currentAudio.pause()
  currentAudio = audioEl.value
  playing.value = true
  frame = requestAnimationFrame(tick)
}

function onPause() {
  playing.value = false
  cancelAnimationFrame(frame)
  current.value = audioEl.value?.currentTime || 0
}

function onEnded() {
  onPause()
  current.value = 0
  rate.value = 1
  audioEl.value.playbackRate = 1
}

function toggle() {
  const a = audioEl.value
  if (a.paused) a.play().catch(() => {})
  else a.pause()
}

function cycleRate() {
  rate.value = RATES[(RATES.indexOf(rate.value) + 1) % RATES.length]
  audioEl.value.playbackRate = rate.value
}

function seekTo(e) {
  const rect = waveEl.value.getBoundingClientRect()
  const ratio = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1)
  current.value = ratio * duration.value
}

function startSeek(e) {
  if (!duration.value) return
  seeking = true
  waveEl.value.setPointerCapture(e.pointerId)
  seekTo(e)
}

function moveSeek(e) {
  if (seeking) seekTo(e)
}

function endSeek() {
  if (!seeking) return
  seeking = false
  audioEl.value.currentTime = current.value
}

onBeforeUnmount(() => {
  cancelAnimationFrame(frame)
  // A detached audio element keeps playing, so stop it when the chat closes
  audioEl.value?.pause()
  if (currentAudio === audioEl.value) currentAudio = null
})
</script>
