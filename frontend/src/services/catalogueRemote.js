const ARROW_CODES = { 37: 'ArrowLeft', 38: 'ArrowUp', 39: 'ArrowRight', 40: 'ArrowDown' }
const FOCUSABLE = 'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'

function visibleControls(root) {
  return Array.from(root.querySelectorAll(FOCUSABLE)).filter(element => {
    const rect = element.getBoundingClientRect()
    return !element.disabled && element.tabIndex >= 0 && rect.width > 0 && rect.height > 0 &&
      !element.closest('[hidden], [inert], [aria-hidden="true"]') &&
      getComputedStyle(element).visibility !== 'hidden'
  })
}

function focusControl(element) {
  element.focus({ preventScroll: true })
  element.scrollIntoView({ block: 'nearest', inline: 'nearest' })
}

// Direction follows the rendered layout, so responsive grids and wrapped controls
// work without a hard-coded TV column count.
export function handleCatalogueRemote(event, root, initialTarget = null) {
  if (!root || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return false
  const key = ARROW_CODES[event.keyCode] || event.key
  const legacyOK = ['Select', 'Accept', 'OK'].includes(key) || event.keyCode === 23 ||
    (event.keyCode === 13 && key !== 'Enter')
  if (!key?.startsWith('Arrow') && !legacyOK) return false

  const dialog = root.querySelector('[data-remote-dialog]')
  const scope = dialog || root
  const controls = visibleControls(scope)
  if (!controls.length) return false
  const active = document.activeElement

  if (legacyOK) {
    if (!controls.includes(active) || !active.matches('button, a[href], [role="button"]')) return false
    event.preventDefault()
    active.click()
    return true
  }

  // Preserve caret movement and native select menus. Up/down can leave a text
  // field unless its own suggestion handler has already consumed the event.
  if (controls.includes(active) && (active.matches('select, textarea, [contenteditable="true"]') ||
      (active.matches('input, textarea') && ['ArrowLeft', 'ArrowRight'].includes(key)))) return false

  event.preventDefault()
  if (!controls.includes(active)) {
    focusControl(controls.includes(initialTarget) ? initialTarget : controls[0])
    return true
  }

  const origin = active.getBoundingClientRect()
  const horizontal = key === 'ArrowLeft' || key === 'ArrowRight'
  const sign = key === 'ArrowLeft' || key === 'ArrowUp' ? -1 : 1
  const primary = rect => horizontal ? rect.left + rect.width / 2 : rect.top + rect.height / 2
  const secondary = rect => horizontal ? rect.top + rect.height / 2 : rect.left + rect.width / 2
  const candidates = controls.filter(element => element !== active).map(element => {
    const rect = element.getBoundingClientRect()
    const distance = sign * (primary(rect) - primary(origin))
    const aligned = horizontal
      ? rect.top < origin.bottom && rect.bottom > origin.top
      : rect.left < origin.right && rect.right > origin.left
    return { element, distance, lane: aligned ? 0 : 1,
      score: distance + Math.abs(secondary(rect) - secondary(origin)) }
  }).filter(candidate => candidate.distance > 1)
  candidates.sort((a, b) => a.lane - b.lane || a.score - b.score)
  if (candidates.length) focusControl(candidates[0].element)
  return true
}
