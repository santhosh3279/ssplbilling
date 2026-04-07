<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-900">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="mb-8 text-center">
        <div class="mb-2 text-3xl font-bold text-slate-100">SSPL<span class="font-light text-slate-400">Billing</span></div>
        <p class="text-sm text-slate-500">Sign in to your account</p>
      </div>

      <!-- Login Card -->
      <div class="rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-sm">
        <!-- Error -->
        <div v-if="errorMsg" class="mb-4 rounded-lg bg-red-900/20 px-4 py-2.5 text-sm text-red-400">
          {{ errorMsg }}
        </div>

        <!-- Email -->
        <div class="mb-4 flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-slate-400">Email or Username</label>
          <input
            ref="emailInput"
            v-model="email"
            type="text"
            class="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2.5 text-sm text-slate-200 outline-none transition focus:border-blue-500 disabled:bg-slate-900 disabled:text-slate-500"
            placeholder="user@company.com"
            @keydown.enter="focusPassword"
          />
        </div>

        <!-- Password -->
        <div class="mb-6 flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-slate-400">Password</label>
          <input
            ref="passwordInput"
            v-model="password"
            type="password"
            class="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2.5 text-sm text-slate-200 outline-none transition focus:border-blue-500 disabled:bg-slate-900 disabled:text-slate-500"
            placeholder="••••••••"
            @keydown.enter="handleLogin"
          />
        </div>

        <!-- Login Button -->
        <button
          class="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="loading"
          @click="handleLogin"
        >
          {{ loading ? 'Signing in…' : 'Sign In' }}
        </button>
      </div>

      <p class="mt-6 text-center text-xs text-slate-500">
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
