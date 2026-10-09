import { createApp } from 'vue'
import { FrappeUI } from 'frappe-ui'
import { primeServerTime, startServerTimeSync } from './services/serverTime'
import './index.css'

async function bootstrap() {
  // Longest the first render waits for server time; a slower sync keeps running in the background.
  const BOOT_SYNC_WAIT_MS = 2000
  try {
    // Includes public catalogue routes and any module-level date defaults.
    let timer
    const slow = new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error(`no response within ${BOOT_SYNC_WAIT_MS} ms`)), BOOT_SYNC_WAIT_MS)
    })
    await Promise.race([primeServerTime(), slow]).finally(() => clearTimeout(timer))
  } catch (error) {
    console.warn('[serverTime] Starting with computer time; synchronization will retry:', error)
  }
  const [{ default: App }, { default: router }] = await Promise.all([
    import('./App.vue'), import('./router'),
  ])
  const app = createApp(App)
  app.use(router)
  app.use(FrappeUI, { socketio: false })
  await router.isReady()
  app.mount('#app')
  const stopSync = startServerTimeSync()
  if (import.meta.hot) import.meta.hot.dispose(stopSync)
}

bootstrap()
