<template>
  <div class="flex min-h-screen items-center justify-center bg-[var(--color-bg)]">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="mb-8 text-center">
        <div class="mb-2 text-3xl font-bold text-[var(--color-text)]">SSPL<span class="font-light text-[var(--color-text-muted)]">Billing</span></div>
        <p class="text-sm text-[var(--color-text-muted)]">Sign in to your account</p>
      </div>

      <!-- Login Card -->
      <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
        <!-- Error -->
        <div v-if="errorMsg" class="mb-4 rounded-lg bg-[var(--color-danger)]/20 px-4 py-2.5 text-sm text-[var(--color-danger)]">
          {{ errorMsg }}
        </div>

        <!-- Email -->
        <div class="mb-4 flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-[var(--color-text-muted)]">Email or Username</label>
          <input
            ref="emailInput"
            v-model="email"
            type="text"
            class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-sm text-[var(--color-text)] outline-none transition focus:border-[var(--color-info)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)]"
            placeholder="user@company.com"
            @keydown.enter="focusPassword"
          />
        </div>

        <!-- Password -->
        <div class="mb-6 flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-[var(--color-text-muted)]">Password</label>
          <input
            ref="passwordInput"
            v-model="password"
            type="password"
            class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-sm text-[var(--color-text)] outline-none transition focus:border-[var(--color-info)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)]"
            placeholder="••••••••"
            @keydown.enter="handleLogin"
          />
        </div>

        <!-- Login Button -->
        <button
          class="w-full rounded-lg bg-[var(--color-info)] py-2.5 text-sm font-semibold text-[var(--color-text-on-highlight)] transition hover:bg-[var(--color-info)] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="loading"
          @click="handleLogin"
        >
          {{ loading ? 'Signing in…' : 'Sign In' }}
        </button>
      </div>

      <p class="mt-6 text-center text-xs text-[var(--color-text-muted)]">
        Powered by ERPNext
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { session } from '../session'
import { dashboardApi } from '../services/dashboard'
import { frappeGet } from '../api.js'

const SETTINGS_CACHE_KEY = 'wb-settings-v2'

const router = useRouter()

const email = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)
const emailInput = ref(null)
const passwordInput = ref(null)

function focusPassword() {
  passwordInput.value?.focus()
}

async function handleLogin() {
  errorMsg.value = ''
  if (!email.value.trim()) { errorMsg.value = 'Email is required'; return }
  if (!password.value) { errorMsg.value = 'Password is required'; return }

  loading.value = true
  try {
    await session.login(email.value.trim(), password.value)
    
    // Clear old settings keys
    ;['wb-general-settings-v1', 'wb-general-settings-v2', 'wb-billing-settings-v2'].forEach(k => localStorage.removeItem(k))
    
    // Pre-load billing settings into localStorage
    try {
      const settings = await dashboardApi.getBillingSettings()
      if (settings) {
        localStorage.setItem(SETTINGS_CACHE_KEY, JSON.stringify({ data: settings, ts: Date.now() }))
        if (settings.wb_theme) {
          const t = settings.wb_theme.toLowerCase() === 'dark' ? 'dark' : 'light'
          localStorage.setItem('wb-theme', t)
          localStorage.setItem('Session_Theme', t)
        }
        if (settings.default_zoom) {
          localStorage.setItem('wb-zoom', settings.default_zoom)
        }
        if (settings.float_precision !== undefined && settings.float_precision !== null) {
          localStorage.setItem('wb-precision', String(settings.float_precision))
        }
        // Save tax_type_incl from first series
        const firstSeries = (settings.billing_series || [])[0]
        if (firstSeries) {
          localStorage.setItem('wb-tax-type-incl', firstSeries.tax_type_incl ? '1' : '0')
        }
      }
      
      // Also pre-load opening_cash
      const today = new Date().toLocaleDateString('en-CA')
      const openingRes = await frappeGet('ssplbilling.api.cahierlog_api.get_opening_total', { date: today })
      if (openingRes) {
        const boxCash = String(openingRes.total || 0)
        localStorage.setItem('opening_cash', boxCash)
        localStorage.setItem('wb-opening-box-cash', boxCash)
      }
    } catch (e) {
      console.warn('[Login] Failed to preload data:', e)
    }
    
    router.push('/')
  } catch (e) {
    errorMsg.value = e.message || 'Invalid email or password'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // If already logged in, redirect to dashboard
  if (session.isLoggedIn.value) {
    router.push('/')
    return
  }
  emailInput.value?.focus()
})
</script>
