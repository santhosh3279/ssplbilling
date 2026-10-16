<template>
  <!-- One-line text that scrolls sideways (back and forth) only when it is wider than its box -->
  <div ref="boxRef" class="marquee-box" :title="text">
    <span
      ref="textRef"
      class="marquee-text"
      :class="{ 'is-scrolling': overflow > 0 }"
      :style="overflow > 0 ? { '--marquee-shift': `-${overflow}px`, '--marquee-duration': `${duration}s` } : null"
    >{{ text }}</span>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  // Scroll speed in pixels per second
  speed: { type: Number, default: 40 },
})

const boxRef = ref(null)
const textRef = ref(null)
const overflow = ref(0)

// One iteration is one direction (alternate); the move takes 60% of it, the rest is the pause at each end
const duration = computed(() => Math.max(3, overflow.value / props.speed / 0.6))

function measure() {
  const box = boxRef.value
  const text = textRef.value
  if (!box || !text) return
  const diff = Math.ceil(text.scrollWidth - box.clientWidth)
  overflow.value = diff > 2 ? diff : 0
}

let observer = null

onMounted(() => {
  measure()
  if (typeof ResizeObserver !== 'undefined') {
    observer = new ResizeObserver(measure)
    observer.observe(boxRef.value)
  }
})

watch(() => props.text, () => nextTick(measure))

onBeforeUnmount(() => observer?.disconnect())
</script>

<style scoped>
.marquee-box {
  overflow: hidden;
  white-space: nowrap;
  min-width: 0;
}
.marquee-text {
  display: inline-block;
  white-space: nowrap;
}
.marquee-text.is-scrolling {
  animation: marquee-slide var(--marquee-duration, 8s) ease-in-out infinite alternate;
}
@keyframes marquee-slide {
  0%, 20% { transform: translateX(0); }
  80%, 100% { transform: translateX(var(--marquee-shift, 0)); }
}
@media (prefers-reduced-motion: reduce) {
  .marquee-text.is-scrolling {
    animation: none;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
