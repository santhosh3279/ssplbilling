<template>
  <div class="fixed inset-0 flex flex-col overflow-y-auto bg-[var(--color-bg)] text-[var(--color-text)]">
    <header class="shrink-0 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 pb-4 pt-[max(1rem,env(safe-area-inset-top))] shadow-sm">
      <div class="flex items-center gap-3">
        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--color-highlight)] text-sm font-bold text-[var(--color-text-on-highlight)]">
          {{ userInitials }}
        </div>
        <div class="min-w-0 flex-1">
          <div class="truncate text-base font-semibold">{{ session.fullName.value || 'User' }}</div>
          <div class="truncate text-xs text-[var(--color-text-muted)]">{{ session.user.value }}</div>
        </div>
        <span v-if="syncing" class="text-xs font-semibold text-[var(--color-info)] animate-pulse">Syncing…</span>
        <button
          type="button"
          class="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm text-[var(--color-text-muted)] active:bg-[var(--color-surface-raised)]"
          @click="handleLogout"
        >Logout</button>
      </div>

      <!-- Admin: Inherit User Settings -->
      <div v-if="isActualAdmin" class="mt-4">
        <label for="md-inherit-user" class="mb-1 block text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
          Inherit Settings
        </label>
        <select
          id="md-inherit-user"
          v-model="selectedUser"
          :disabled="syncing"
          class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2.5 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
          @change="handleUserChange"
        >
          <option v-for="u in inheritUsersOptions" :key="u.value" :value="u.value">{{ u.label }}</option>
        </select>
        <div v-if="selectedUser !== session.user.value" class="mt-1.5 text-xs font-medium italic text-[var(--color-warning)]">
          Previewing User Mode
        </div>
      </div>
    </header>

    <main class="flex-1 px-4 py-5">
      <div class="grid grid-cols-2 gap-4">
        <button
          v-for="t in tiles"
          :key="t.id"
          type="button"
          class="flex flex-col items-center justify-center gap-2 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-6 text-center shadow-sm active:scale-[0.98] active:bg-[var(--color-surface-raised)]"
          @click="router.push(t.path)"
        >
          <span class="text-4xl">{{ t.icon }}</span>
          <span class="text-base font-semibold">{{ t.name }}</span>
          <span class="text-xs text-[var(--color-text-muted)]">{{ t.desc }}</span>
        </button>
      </div>
    </main>

    <footer class="shrink-0 px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-2 text-center">
      <button type="button" class="text-sm text-[var(--color-text-muted)] underline" @click="openDesktopView">
        Desktop view
      </button>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { session } from '../session'
import { dashboardApi } from '../services/dashboard'
import { fetchSettings, syncSettings, loadAllowedTiles, TILE_CACHE_KEY } from '../services/settingsSync.js'
import { canAccessRoute } from '../composables/usePermission'
import { DESKTOP_VIEW_KEY } from '../utils/device'

const router = useRouter()

const isActualAdmin = computed(() => ['Administrator', 'admin'].includes(session.user.value))

const userInitials = computed(() => {
  const name = String(session.fullName.value || session.user.value || 'U')
  return name.split(' ').map(w => w[0] || '').join('').toUpperCase().slice(0, 2) || 'U'
})

// ==================== TILES ====================
const MOBILE_TILES = [
  { id: 'mobile-bill', route: 'MobileBill', path: '/mobile-bill', name: 'Mobile Bill', desc: 'Phone billing with camera scan', icon: '📱' },
  { id: 'cashier-mobile', route: 'CashierMobile', path: '/cashier-mobile', name: 'Cashier', desc: 'Settle draft bills', icon: '🏧' },
  { id: 'item-barcode', route: 'ItemBarcode', path: '/item-barcode', name: 'Item Barcodes', desc: 'Scan & add barcodes to items', icon: '🏷️' },
  { id: 'stock-check', route: 'StockCheck', path: '/stock-check', name: 'Stock Check', desc: 'Stock & selling price lookup', icon: '🔍' },
  { id: 'ai-chat', route: 'AiChat', path: '/ai-chat-mobile', name: 'AI Chat', desc: 'Ask about sales & stock', icon: '🤖' },
]

// canAccessRoute reads the role / tile-access / license keys from localStorage,
// so bump this after a sync to re-evaluate the tile list.
const permissionTrigger = ref(0)
const tiles = computed(() => {
  permissionTrigger.value
  // Stock Check is a public page: always shown
  return MOBILE_TILES.filter(t => t.id === 'stock-check' || canAccessRoute(t.route))
})

// ==================== INHERIT USER ====================
const selectedUser = ref(localStorage.getItem('wb-inherited-user') || session.user.value)
const allUsers = ref([])
const syncing = ref(false)

const inheritUsersOptions = computed(() => {
  const options = [{ value: session.user.value, label: `Me (${session.fullName.value || session.user.value})` }]
  if (Array.isArray(allUsers.value)) {
    allUsers.value.forEach(u => {
      if (u.value !== session.user.value) options.push(u)
    })
  }
  return options
})

async function handleUserChange() {
  if (selectedUser.value === session.user.value) {
    localStorage.removeItem('wb-inherited-user')
  } else {
    localStorage.setItem('wb-inherited-user', selectedUser.value)
  }
  syncing.value = true
  try {
    await syncSettings(selectedUser.value)
  } finally {
    syncing.value = false
  }
  window.location.reload()
}

function openDesktopView() {
  // Session-scoped: the next tab / app launch on this phone opens the mobile dashboard again
  sessionStorage.setItem(DESKTOP_VIEW_KEY, '1')
  router.push('/')
}

async function handleLogout() {
  localStorage.removeItem('wb-inherited-user')
  localStorage.removeItem(TILE_CACHE_KEY)
  await session.logout()
  router.push('/login')
}

onMounted(async () => {
  if (isActualAdmin.value) {
    dashboardApi.getAllUsers()
      .then(users => { allUsers.value = users })
      .catch(e => console.warn('[MobileDashboard] getAllUsers failed:', e))
  }
  // Phones land here instead of Dashboard, so this page owns the settings / role /
  // tile-access sync that every other page and usePermission read from localStorage.
  syncing.value = true
  try {
    await Promise.all([
      fetchSettings(selectedUser.value),
      loadAllowedTiles(selectedUser.value !== session.user.value ? selectedUser.value : null),
    ])
  } finally {
    syncing.value = false
    permissionTrigger.value++
  }
})
</script>
