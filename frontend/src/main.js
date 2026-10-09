import { createApp } from 'vue'
import { FrappeUI } from 'frappe-ui'
import { primeServerTime, startServerTimeSync } from './services/serverTime'
import './index.css'

async function bootstrap() {
  const root = document.querySelector('#app')
  root.textContent = 'Connecting to server…'
  try {
    // Includes public catalogue routes and any module-level date defaults.
    await primeServerTime()
  } catch (error) {
    root.textContent = 'Unable to synchronize server time. Check your connection and retry. '
    const retry = document.createElement('button')
    retry.textContent = 'Retry'
    retry.onclick = bootstrap
    root.appendChild(retry)
    return
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
