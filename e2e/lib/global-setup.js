// Logs the bot in once and saves the session; every test starts already signed in.
const fs = require('node:fs')
const path = require('node:path')
const { chromium } = require('@playwright/test')
const { requireEnv } = require('./env')

const STATE_FILE = path.join(__dirname, '..', '.auth', 'state.json')

module.exports = async config => {
  const env = requireEnv()
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true })
  const browser = await chromium.launch(config.projects[0].use.launchOptions)
  const page = await browser.newPage({ baseURL: env.E2E_BASE_URL })
  await page.goto('/frontend/login')
  await page.getByPlaceholder('user@company.com').fill(env.E2E_USER)
  await page.locator('input[type=password]').fill(env.E2E_PASSWORD)
  await page.keyboard.press('Enter')
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30_000 }).catch(() => {
    throw new Error(`Login failed for ${env.E2E_USER}. Re-run "npm run seed" to reset the bot's password.`)
  })
  await page.context().storageState({ path: STATE_FILE })
  await browser.close()
}

module.exports.STATE_FILE = STATE_FILE
