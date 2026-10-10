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

// Self-host the OCR engine (worker, wasm core, English model) used by the barcode
// scanner, so phones on the LAN never need the tesseract CDN. Served from public/ocr.
const OCR_ASSETS = {
  'worker.min.js': 'node_modules/tesseract.js/dist/worker.min.js',
  'tesseract-core-lstm.wasm.js': 'node_modules/tesseract.js-core/tesseract-core-lstm.wasm.js',
  'tesseract-core-simd-lstm.wasm.js': 'node_modules/tesseract.js-core/tesseract-core-simd-lstm.wasm.js',
  'tesseract-core-relaxedsimd-lstm.wasm.js': 'node_modules/tesseract.js-core/tesseract-core-relaxedsimd-lstm.wasm.js',
  'eng.traineddata.gz': 'node_modules/@tesseract.js-data/eng/4.0.0_best_int/eng.traineddata.gz',
}
fs.mkdirSync('public/ocr', { recursive: true })
for (const [name, src] of Object.entries(OCR_ASSETS)) {
  if (!fs.existsSync(`public/ocr/${name}`) && fs.existsSync(src)) fs.copyFileSync(src, `public/ocr/${name}`)
}

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  // Dev server serves from root; production assets live under Frappe's asset path
  base: command === 'build' ? '/assets/ssplbilling/frontend/' : '/',
  plugins: [vue()],
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false,
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false,
  },
  server: {
    port: 8080,
    host: true,
    // `VITE_HTTPS=1 yarn dev` serves https with Vite's self-signed cert. Phones only
    // allow live camera video (Stock Check barcode scanner) on https pages.
    https: process.env.VITE_HTTPS === '1',
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
    // www/frontend.py reads this to find the entry and the chunks to preload.
    manifest: true,
    target: 'es2020',
  },
  esbuild: {
    target: 'es2020',
  },
  optimizeDeps: {
    include: ['frappe-ui > feather-icons', 'showdown', 'engine.io-client', 'exceljs', 'debug'],
  },
}))
