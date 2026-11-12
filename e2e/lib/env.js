// Loads e2e/.env (written by scripts/seed.py) and guards against running on a live site.
const fs = require('node:fs')
const path = require('node:path')

const ENV_FILE = path.join(__dirname, '..', '.env')

function load() {
  const values = {}
  if (fs.existsSync(ENV_FILE)) {
    for (const line of fs.readFileSync(ENV_FILE, 'utf8').split('\n')) {
      const at = line.indexOf('=')
      if (at > 0 && !line.trimStart().startsWith('#')) values[line.slice(0, at).trim()] = line.slice(at + 1)
    }
  }
  // Real environment variables win, so CI can inject them without a file
  for (const key of Object.keys(process.env)) {
    if (key.startsWith('E2E_')) values[key] = process.env[key]
  }
  return values
}

const env = load()

function requireEnv() {
  const missing = ['E2E_BASE_URL', 'E2E_USER', 'E2E_PASSWORD', 'E2E_SERIES_EXEMPT'].filter(k => !env[k])
  if (missing.length) {
    throw new Error(`Missing ${missing.join(', ')}. Run "npm run seed" in e2e/ first (it writes e2e/.env).`)
  }
  // The bot creates and deletes documents: only ever on a local dev site unless told otherwise.
  const host = new URL(env.E2E_BASE_URL).hostname
  const local = host === 'localhost' || host === '127.0.0.1' || host.endsWith('.localhost') || host.endsWith('.local')
  if (!local && env.E2E_ALLOW_REMOTE !== '1') {
    throw new Error(`Refusing to run against ${host}: not a local dev site. Set E2E_ALLOW_REMOTE=1 to override.`)
  }
  return env
}

module.exports = { env, requireEnv }
