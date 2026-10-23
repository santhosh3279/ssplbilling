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
  allCorners = false, // true: cannons from all four corners, not just the bottom two
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
  ctx.scale(dpr, dpr)

  // Cannons in the bottom corners aim up and inward; top-corner cannons (allCorners) aim down and inward
  const cannons = [
    { x: 0, y: h, deg: -60 },
    { x: w, y: h, deg: -120 },
    ...(allCorners
      ? [
          { x: 0, y: 0, deg: 30 },
          { x: w, y: 0, deg: 150 },
        ]
      : []),
  ]
  const pieces = Array.from({ length: count }, (_, i) => {
    const c = cannons[i % cannons.length]
    const angle = c.deg * (Math.PI / 180) + (Math.random() - 0.5) * spread
    const v = speed + Math.random() * speed
    return {
      x: c.x,
      y: c.y,
      vx: Math.cos(angle) * v,
      vy: Math.sin(angle) * v,
      size: size + Math.random() * size,
      rot: Math.random() * Math.PI,
      vrot: (Math.random() - 0.5) * 0.3,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
    }
  })

  const start = performance.now()
  function frame(now) {
    const elapsed = now - start
    ctx.clearRect(0, 0, w, h)
    ctx.globalAlpha = Math.max(0, 1 - Math.max(0, elapsed - duration * 0.6) / (duration * 0.4))
    for (const p of pieces) {
      p.vy += gravity
      p.vx *= drag
      p.x += p.vx
      p.y += p.vy
      p.rot += p.vrot
      ctx.save()
      ctx.translate(p.x, p.y)
      ctx.rotate(p.rot)
      ctx.fillStyle = p.color
      ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2)
      ctx.restore()
    }
    if (elapsed < duration) requestAnimationFrame(frame)
    else canvas.remove()
  }
  requestAnimationFrame(frame)
}
