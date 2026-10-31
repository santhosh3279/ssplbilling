// Lightweight confetti burst on a throwaway full-screen canvas; no dependency.
const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7', '#ec4899', '#14b8a6']

export function fireConfetti({
  count = 160,
  duration = 2500,
  speed = 9, // min launch speed; max is speed * 2
  spread = 0.9, // radians of random aim jitter
  size = 6, // min piece size; max is size * 2
  gravity = 0.25,
  drag = 0.99,
} = {}) {
  if (typeof document === 'undefined') return

  const canvas = document.createElement('canvas')
  canvas.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:9999'
  document.body.appendChild(canvas)
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const w = window.innerWidth
  const h = window.innerHeight
  canvas.width = w * dpr
  canvas.height = h * dpr

  // Two cannons from the bottom corners, aimed up and inward
  const pieces = Array.from({ length: count }, (_, i) => {
    const left = i % 2 === 0
    const angle = (left ? -60 : -120) * (Math.PI / 180) + (Math.random() - 0.5) * spread
    const v = speed + Math.random() * speed
    return {
      x: left ? 0 : w,
      y: h,
      vx: Math.cos(angle) * v,
      vy: Math.sin(angle) * v,
      size: size + Math.random() * size,
      rot: Math.random() * Math.PI,
      vrot: (Math.random() - 0.5) * 0.3,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
    }
  })

  // Per frame: one setTransform per piece instead of save/translate/rotate/restore, and pieces
  // that fell below the screen are dropped. Runs at 800 pieces on cashier PCs, beside a Vue update.
  const start = performance.now()
  let live = pieces
  function frame(now) {
    const elapsed = now - start
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, w, h)
    ctx.globalAlpha = Math.max(0, 1 - Math.max(0, elapsed - duration * 0.6) / (duration * 0.4))
    live = live.filter(p => {
      p.vy += gravity
      p.vx *= drag
      p.x += p.vx
      p.y += p.vy
      p.rot += p.vrot
      if (p.y - p.size > h && p.vy > 0) return false
      const cos = Math.cos(p.rot) * dpr
      const sin = Math.sin(p.rot) * dpr
      ctx.setTransform(cos, sin, -sin, cos, p.x * dpr, p.y * dpr)
      ctx.fillStyle = p.color
      ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2)
      return true
    })
    if (elapsed < duration && live.length) requestAnimationFrame(frame)
    else canvas.remove()
  }
  requestAnimationFrame(frame)
}
