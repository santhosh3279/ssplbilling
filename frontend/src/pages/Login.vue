<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="mb-8 text-center">
        <div class="mb-2 text-3xl font-bold text-gray-900">SSPL<span class="font-light text-gray-400">Billing</span></div>
        <p class="text-sm text-gray-500">Sign in to your account</p>
      </div>

      <!-- Login Card -->
      <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <!-- Error -->
        <div v-if="errorMsg" class="mb-4 rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-600">
          {{ errorMsg }}
        </div>

        <!-- Email -->
        <div class="mb-4 flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-gray-600">Email or Username</label>
          <input
            ref="emailInput"
            v-model="email"
            type="text"
            class="rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="user@company.com"
            @keydown.enter="focusPassword"
          />
        </div>

        <!-- Password -->
        <div class="mb-6 flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-gray-600">Password</label>
          <input
            ref="passwordInput"
            v-model="password"
            type="password"
            class="rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
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

      <p class="mt-6 text-center text-xs text-gray-400">
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

const BILLING_SETTINGS_CACHE_KEY = 'wb-billing-settings-v2'

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
    
    // Pre-load billing settings into localStorage
    try {
      const settings = await dashboardApi.getBillingSettings()
      if (settings) {
        localStorage.setItem(BILLING_SETTINGS_CACHE_KEY, JSON.stringify({ data: settings, ts: Date.now() }))
        if (settings.default_zoom) {
          localStorage.setItem('wb-zoom', settings.default_zoom)
        }
      }
    } catch (e) {
      console.warn('[Login] Failed to preload billing settings:', e)
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
