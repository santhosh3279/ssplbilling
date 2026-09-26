const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const document = { activeElement: null }
const context = vm.createContext({ document, getComputedStyle: () => ({ visibility: 'visible' }) })
const source = fs.readFileSync('src/services/catalogueRemote.js', 'utf8').replace('export function', 'function')
vm.runInContext(source, context)

function control(name, left, top, tag = 'BUTTON', width = 80, height = 60) {
  return {
    name, tagName: tag, tabIndex: 0, disabled: false, clicks: 0, scrolls: 0,
    getBoundingClientRect: () => ({ left, top, width, height, right: left + width, bottom: top + height }),
    closest: () => null,
    matches(selector) {
      return selector.split(',').some(part => {
        part = part.trim()
        return part === tag.toLowerCase() || (part === 'a[href]' && tag === 'A')
      })
    },
    focus() { document.activeElement = this },
    scrollIntoView() { this.scrolls++ },
    click() { this.clicks++ }
  }
}
const a = control('a', 0, 0), b = control('b', 100, 0)
const c = control('c', 0, 100), d = control('d', 100, 100)
const root = { querySelector: () => null, querySelectorAll: () => [a, b, c, d] }
context.root = root
function send(key, keyCode = 0, extras = {}) {
  const event = { key, keyCode, defaultPrevented: false,
    preventDefault() { this.defaultPrevented = true }, ...extras }
  context.event = event
  const handled = vm.runInContext('handleCatalogueRemote(event, root)', context)
  return { handled, event }
}
assert.equal(send('ArrowDown').handled, true)
assert.equal(document.activeElement, a, 'first arrow establishes focus')
assert.equal(send('ArrowRight').event.defaultPrevented, true)
assert.equal(document.activeElement, b)
send('ArrowDown')
assert.equal(document.activeElement, d, 'down preserves the grid column')
send('ArrowLeft')
assert.equal(document.activeElement, c)
send('Unidentified', 38)
assert.equal(document.activeElement, a, 'legacy TV arrow key codes work')
send('ArrowLeft')
assert.equal(document.activeElement, a, 'no movement beyond the grid edge')
send('Select', 23)
assert.equal(a.clicks, 1, 'legacy remote OK clicks exactly once')
assert.equal(send('Enter', 13).handled, false, 'native Enter remains browser-controlled')
assert.equal(send('ArrowRight', 39, { defaultPrevented: true }).handled, false)
assert.equal(send('ArrowRight', 39, { ctrlKey: true }).handled, false)
b.disabled = true
send('ArrowRight')
assert.notEqual(document.activeElement, b, 'disabled controls are skipped')
b.disabled = false
assert(a.scrolls > 0, 'focused cards scroll into view')

const input = control('input', 0, 0, 'INPUT')
context.root = { querySelector: () => null, querySelectorAll: () => [input, c] }
document.activeElement = input
assert.equal(send('ArrowLeft').handled, false, 'text caret arrows are preserved')
send('ArrowDown')
assert.equal(document.activeElement, c, 'down leaves a single-line input')
const select = control('select', 0, 0, 'SELECT')
context.root = { querySelector: () => null, querySelectorAll: () => [select, c] }
document.activeElement = select
assert.equal(send('ArrowDown').handled, false, 'native select menus keep their arrows')
const modal = { querySelectorAll: () => [c, d] }
context.root = { querySelector: () => modal, querySelectorAll: () => [a, b, c, d] }
document.activeElement = a
send('ArrowRight')
assert.equal(document.activeElement, c, 'dialog navigation cannot focus the background')

for (const file of ['OfferPage.vue', 'catalougepage.vue']) {
  const page = fs.readFileSync(`src/pages/${file}`, 'utf8')
  assert(page.includes("import { handleCatalogueRemote } from '../services/catalogueRemote.js'"))
  assert.match(page, /tabindex="0"\s+role="group"/, 'item cards are focusable')
  const handler = page.slice(page.indexOf('function handleKeyDown(event)'), page.indexOf('// ── Live refresh'))
  const actions = []
  const pageContext = vm.createContext({
    handleCatalogueRemote: () => false, catalogueRoot: { value: null }, exportDialog: { value: null },
    playButtonRef: { value: null }, showExportModal: { value: false }, showLogin: { value: false },
    isFullscreen: { value: true }, resetControlsTimer: () => {},
    nextItem: () => actions.push('next'), prevItem: () => actions.push('prev'),
    togglePause: () => actions.push('pause'), exitPresentationMode: () => actions.push('exit'),
    document: { activeElement: { tagName: 'DIV', getAttribute: () => null } },
    enterPresentationMode: () => actions.push('play'), loadOffer: () => {},
  })
  vm.runInContext(handler, pageContext)
  for (const [key, keyCode] of [['ArrowRight',39], ['ArrowLeft',37], ['Select',23], ['Unidentified',10009]]) {
    pageContext.event = { key, keyCode, preventDefault() {} }
    vm.runInContext('handleKeyDown(event)', pageContext)
  }
  assert.deepEqual(actions, ['next', 'prev', 'pause', 'exit'], `${file}: slideshow controls retained`)
  pageContext.isFullscreen.value = false
  pageContext.event = { key: 'Select', keyCode: 23, preventDefault() {} }
  vm.runInContext('handleKeyDown(event)', pageContext)
  assert.equal(actions.at(-1), 'play', `${file}: OK on an item opens presentation`)
  const presentation = page.slice(page.indexOf('function enterPresentationMode()'), page.indexOf('function exitPresentationMode()'))
  const presentationContext = vm.createContext({
    document: { documentElement: {}, activeElement: { closest: () => ({ getAttribute: () => '4' }) } },
    isFullscreen: { value: false }, activeIndex: { value: 0 }, isPaused: { value: true }, startSlideshow: () => {}
  })
  vm.runInContext(presentation + '\nenterPresentationMode()', presentationContext)
  assert.equal(presentationContext.activeIndex.value, 4, `${file}: presentation starts at focused item`)

}
console.log('Catalogue remote: directional focus, legacy keys, scrolling, input/menu handling, dialogs, and slideshow controls passed')
