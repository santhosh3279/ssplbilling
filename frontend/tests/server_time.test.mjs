import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile, readdir } from 'node:fs/promises'

const source = await readFile(new URL('../src/services/serverTime.js', import.meta.url), 'utf8')
let moduleId = 0
async function clock(t, data = { epoch_ms: Date.parse('2026-10-09T18:29:59Z'), timezone: 'Asia/Kolkata' }) {
  let tick = 1000
  t.mock.method(performance, 'now', () => tick)
  t.mock.method(globalThis, 'fetch', async () => ({ ok: true, json: async () => ({ message: data }) }))
  const api = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}#${moduleId++}`)
  return { ...api, advance: ms => { tick += ms } }
}

test('server time is unavailable until synchronization succeeds', async t => {
  const c = await clock(t)
  assert.equal(c.isServerTimePrimed(), false)
  assert.throws(c.serverToday, /not synchronized/)
  assert.throws(c.serverNow, /not synchronized/)
  await c.primeServerTime()
  assert.equal(c.isServerTimePrimed(), true)
  assert.equal(c.serverToday(), '2026-10-09')
  assert.equal(c.serverNowTime(), '23:59:59')
})

test('computer clock changes do not change server time; elapsed time crosses server midnight', async t => {
  const c = await clock(t)
  t.mock.method(Date, 'now', () => Date.parse('1990-01-01T00:00:00Z'))
  await c.primeServerTime()
  Date.now.mock.mockImplementation(() => Date.parse('2099-01-01T00:00:00Z'))
  assert.equal(c.serverToday(), '2026-10-09')
  c.advance(2000)
  assert.equal(c.serverToday(), '2026-10-10')
  assert.equal(c.serverNowTime(), '00:00:01')
})

test('server timezone determines calendar fields and date navigation', async t => {
  const c = await clock(t, { epoch_ms: Date.parse('2027-01-01T02:00:00Z'), timezone: 'America/New_York' })
  await c.primeServerTime()
  assert.equal(c.serverToday(), '2026-12-31')
  assert.equal(c.serverNowTime(), '21:00:00')
  const calendar = c.serverCalendarDate()
  assert.equal(calendar.getFullYear(), 2026)
  assert.equal(calendar.getMonth(), 11)
  assert.equal(c.toLocalISO(calendar), '2026-12-31')
  calendar.setDate(calendar.getDate() + 1)
  assert.equal(c.toLocalISO(calendar), '2027-01-01')
  const leapDay = c.parseCalendarDate('2028-02-29')
  leapDay.setDate(leapDay.getDate() + 1)
  assert.equal(c.toLocalISO(leapDay), '2028-03-01')
})

test('failed initial synchronization never falls back and can be retried', async t => {
  const c = await clock(t)
  fetch.mock.mockImplementation(async () => { throw new Error('offline') })
  await assert.rejects(c.primeServerTime(), /offline/)
  assert.equal(c.isServerTimePrimed(), false)
  assert.throws(c.serverNow, /not synchronized/)
  fetch.mock.mockImplementation(async () => ({ ok: true, json: async () => ({ epoch_ms: 1791568800000, timezone: 'UTC' }) }))
  await c.primeServerTime()
  assert.equal(c.isServerTimePrimed(), true)
})

test('invalid epochs, missing zones, invalid zones and HTTP failures cannot initialize the clock', async t => {
  for (const data of [ {}, { datetime: '2026-01-01 12:00:00' }, { epoch_ms: -1, timezone: 'UTC' },
    { epoch_ms: 1791568800000 }, { epoch_ms: 1791568800000, timezone: 'Invalid/Zone' } ]) {
    const c = await clock(t, data)
    await assert.rejects(c.primeServerTime())
    assert.equal(c.isServerTimePrimed(), false)
  }
  const c = await clock(t)
  fetch.mock.mockImplementation(async () => ({ ok: false, status: 503 }))
  await assert.rejects(c.primeServerTime(), /503/)
})

test('failed refresh retains the last server anchor and later refresh corrects it', async t => {
  const c = await clock(t)
  await c.primeServerTime()
  fetch.mock.mockImplementation(async () => { throw new Error('offline') })
  c.advance(2000)
  await assert.rejects(c.primeServerTime())
  assert.equal(c.serverToday(), '2026-10-10')
  fetch.mock.mockImplementation(async () => ({ ok: true, json: async () => ({ epoch_ms: Date.parse('2026-10-11T12:00:00Z'), timezone: 'UTC' }) }))
  await c.primeServerTime()
  assert.equal(c.serverToday(), '2026-10-11')
  assert.equal(c.serverNowTime(), '12:00:00')
})

test('concurrent refreshes share one uncached request', async t => {
  const c = await clock(t)
  await Promise.all([c.primeServerTime(), c.primeServerTime()])
  assert.equal(fetch.mock.callCount(), 1)
  assert.equal(fetch.mock.calls[0].arguments[1].cache, 'no-store')
})

test('refresh runs periodically and after focus/visibility changes, and cleans up', async t => {
  const c = await clock(t)
  const win = new EventTarget()
  const doc = new EventTarget()
  doc.visibilityState = 'visible'
  globalThis.window = win
  globalThis.document = doc
  t.after(() => { delete globalThis.window; delete globalThis.document })
  let interval
  t.mock.method(globalThis, 'setInterval', (callback, ms) => {
    assert.equal(ms, 60000)
    interval = callback
    return 42
  })
  t.mock.method(globalThis, 'clearInterval', id => assert.equal(id, 42))
  const stop = c.startServerTimeSync()
  win.dispatchEvent(new Event('focus'))
  await c.primeServerTime()
  doc.dispatchEvent(new Event('visibilitychange'))
  await c.primeServerTime()
  interval()
  await c.primeServerTime()
  assert.equal(fetch.mock.callCount(), 3)
  stop()
  win.dispatchEvent(new Event('focus'))
  doc.dispatchEvent(new Event('visibilitychange'))
  assert.equal(fetch.mock.callCount(), 3)
})

test('app source cannot reintroduce computer-clock reads', async () => {
  async function inspect(directory) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const path = new URL(entry.name + (entry.isDirectory() ? '/' : ''), directory)
      if (entry.isDirectory()) await inspect(path)
      else if (/\.(js|vue)$/.test(entry.name)) {
        const text = await readFile(path, 'utf8')
        assert.doesNotMatch(text, /\bDate\.now\s*\(|new\s+Date\s*\(\s*\)/, path.pathname)
      }
    }
  }
  await inspect(new URL('../src/', import.meta.url))
})

test('startup waits for server time before loading routes, and offers retry on failure', async t => {
  const { runInNewContext } = await import('node:vm')
  const main = await readFile(new URL('../src/main.js', import.meta.url), 'utf8')
  const script = main.replace(/^import .*\n/gm, '')
    .replaceAll('import(', 'load(')
    .replace(/  if \(import.meta.hot\).*\n/, '')
    .replace(/bootstrap\(\)\s*$/, 'globalThis.boot = bootstrap()')
  let resolveSync
  let sync = new Promise(resolve => { resolveSync = resolve })
  let loads = 0
  let mounts = 0
  const root = { textContent: '', appendChild(button) { this.retry = button } }
  const context = {
    document: { querySelector: () => root, createElement: () => ({}) },
    primeServerTime: () => sync,
    startServerTimeSync: () => () => {},
    FrappeUI: {},
    createApp: () => ({ use() {}, mount() { mounts++ } }),
    load: async () => { loads++; return { default: { isReady: async () => {} } } },
  }
  runInNewContext(script, context)
  assert.equal(loads, 0)
  assert.equal(mounts, 0)
  resolveSync()
  await context.boot
  assert.equal(loads, 2)
  assert.equal(mounts, 1)
  sync = Promise.reject(new Error('offline'))
  runInNewContext(script, context)
  await context.boot
  assert.match(root.textContent, /Unable to synchronize/)
  assert.equal(mounts, 1)
  assert.equal(root.retry.textContent, 'Retry')
  sync = Promise.resolve()
  await root.retry.onclick()
  assert.equal(mounts, 2)
})
