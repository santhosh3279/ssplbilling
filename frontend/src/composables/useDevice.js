import { ref, onMounted, onUnmounted } from 'vue'

export function useDevice() {
  const isTablet = ref(false)
  const isMobile = ref(false)

  const updateDevice = () => {
    const ua = navigator.userAgent.toLowerCase()

    // 1. User Agent Sniffing
    const isTabletUA = /(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)

    // 2. Capability Detection (Touch)
    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0

    // 3. Screen Size Logic (Common tablet range: 600px to 1280px)
    const width = window.innerWidth
    const isTabletSize = width >= 600 && width <= 1280

    isTablet.value = isTabletUA || (hasTouch && isTabletSize)
    isMobile.value = /mobile|iphone|ipod|android.*mobile/i.test(ua)
    
    // Maintain the body class for CSS targeting
    if (isTablet.value) {
      document.body.classList.add('is-tablet')
    } else {
      document.body.classList.remove('is-tablet')
    }
  }

  onMounted(() => {
    updateDevice()
    window.addEventListener('resize', updateDevice)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateDevice)
  })

  return { isTablet, isMobile }
}
