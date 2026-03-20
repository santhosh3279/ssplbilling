import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import fs from 'fs'
import { getProxyOptions } from 'frappe-ui/src/utils/vite-dev-server'

// Try to load site config, fallback to defaults if not available
let webserver_port = 8000
let socketio_port = 9000

try {
  const siteConfig = JSON.parse(fs.readFileSync('../../../sites/common_site_config.json', 'utf-8'))
  webserver_port = siteConfig.webserver_port || 8000
  socketio_port = siteConfig.socketio_port || 9000
} catch (e) {
  // Use defaults if config doesn't exist (e.g., during Docker build)
  console.log('Using default ports (site config not found)')
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8080,
    host: true,
    proxy: {
      // Frappe backend
      ...getProxyOptions({ port: webserver_port }),
      // Socket.IO (dynamic from config)
      '^/socket.io': {
        target: `http://localhost:${socketio_port}`,
        ws: true,
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: '../ssplbilling/public/frontend',  // FIXED: Hardcoded relative path
    emptyOutDir: true,
    target: 'es2020',
  },
  esbuild: {
    target: 'es2020',
  },
  optimizeDeps: {
    include: ['frappe-ui > feather-icons', 'showdown', 'engine.io-client', 'exceljs'],
  },
})
