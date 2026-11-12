const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { defineConfig } = require('@playwright/test')
const { requireEnv } = require('./lib/env')

const env = requireEnv()

// Chromium needs a few system libraries. The proper fix is `sudo npx playwright install-deps chromium`;
// without root, libraries unpacked under ~/.cache/playwright-libs (or E2E_EXTRA_LIB_PATH) are used.
const extraLibs = env.E2E_EXTRA_LIB_PATH || path.join(os.homedir(), '.cache/playwright-libs/root/usr/lib/x86_64-linux-gnu')
const launchEnv = fs.existsSync(extraLibs)
  ? { ...process.env, LD_LIBRARY_PATH: [extraLibs, process.env.LD_LIBRARY_PATH].filter(Boolean).join(':') }
  : undefined

module.exports = defineConfig({
  testDir: './tests',
  globalSetup: require.resolve('./lib/global-setup.js'),
  // One bot user on one site: bills are made one at a time, like one operator
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: env.E2E_BASE_URL,
    storageState: path.join(__dirname, '.auth', 'state.json'),
    viewport: { width: 1920, height: 1080 },
    actionTimeout: 15_000,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    launchOptions: launchEnv ? { env: launchEnv } : {},
  },
})
