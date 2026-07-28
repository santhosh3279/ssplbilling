<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <header class="shrink-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center gap-4">
        <button
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
          @click="router.push('/')"
        >
          &larr; Dashboard
        </button>
        <div>
          <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Chart of Accounts</h1>
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">Account Tree</p>
        </div>
      </div>
      <div class="relative w-72">
        <input
          v-model="searchQuery"
          @input="onSearch"
          type="text"
          placeholder="Search accounts..."
          class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1.5 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
        />
        <ul
          v-if="searchResults.length"
          class="absolute z-20 mt-1 max-h-64 w-full overflow-y-auto rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg"
        >
          <li
            v-for="r in searchResults"
            :key="r.name"
            class="cursor-pointer px-3 py-1.5 text-sm hover:bg-[var(--color-surface-raised)]"
            @click="selectFromSearch(r.name)"
          >
            {{ r.name }}
          </li>
        </ul>
      </div>
    </header>

    <main class="flex-1 overflow-hidden p-6" style="zoom: 1.5">
      <div class="mx-auto grid h-full max-w-6xl grid-cols-1 gap-6 md:grid-cols-[1fr_360px]">
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm overflow-y-auto">
          <div v-if="isLoading" class="flex h-full items-center justify-center text-[var(--color-text-muted)]">
            <span class="text-sm animate-pulse">Loading accounts...</span>
          </div>
          <ul v-else class="list-none">
            <AccountTreeNode
              v-for="node in roots"
              :key="node.value"
              :node="node"
              :level="0"
              :selected="selectedAccount"
              :company="company"
              @select="onSelect"
            />
          </ul>
        </section>

        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm overflow-y-auto">
          <h2 class="text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)] mb-4">Account Detail</h2>
          <div v-if="!selectedAccount" class="text-sm italic text-[var(--color-text-muted)]">
            Select an account to view details.
          </div>
          <div v-else-if="detailLoading" class="text-sm text-[var(--color-text-muted)] animate-pulse">Loading...</div>
          <dl v-else-if="detail" class="space-y-3 text-sm">
            <div>
              <dt class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Account Name</dt>
              <dd class="font-semibold">{{ detail.name }}</dd>
            </div>
            <div>
              <dt class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Parent Account</dt>
              <dd>{{ detail.parent_account || '—' }}</dd>
            </div>
            <div v-if="balance !== null">
              <dt class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Balance</dt>
              <dd class="font-mono font-bold" :class="balance > 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'">
                {{ formatCurrency(Math.abs(balance)) }} {{ balance > 0 ? 'Dr' : 'Cr' }}
              </dd>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <dt class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Root Type</dt>
                <dd>{{ detail.root_type || '—' }}</dd>
              </div>
              <div>
                <dt class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Account Type</dt>
                <dd>{{ detail.account_type || '—' }}</dd>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <dt class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Company</dt>
                <dd>{{ detail.company || '—' }}</dd>
              </div>
              <div>
                <dt class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Currency</dt>
                <dd>{{ detail.account_currency || '—' }}</dd>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <dt class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Group</dt>
                <dd>{{ detail.is_group ? 'Yes' : 'No' }}</dd>
              </div>
              <div>
                <dt class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Disabled</dt>
                <dd>{{ detail.disabled ? 'Yes' : 'No' }}</dd>
              </div>
            </div>
          </dl>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import AccountTreeNode from '../components/AccountTreeNode.vue'

const router = useRouter()
const isLoading = ref(true)
const roots = ref([])
const company = ref(localStorage.getItem('wb-company') || '')

const searchQuery = ref('')
const searchResults = ref([])
let searchTimer = null

const selectedAccount = ref('')
const detail = ref(null)
const detailLoading = ref(false)
const balance = ref(null)

function formatCurrency(val) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(val || 0)
}

onMounted(loadRoots)

async function loadRoots() {
  isLoading.value = true
  try {
    if (company.value) {
      const rootAccounts = await frappeGet('erpnext.accounts.utils.get_children', {
        doctype: 'Account',
        parent: '',
        company: company.value,
        is_root: true,
      })
      roots.value = rootAccounts.length
        ? await frappeGet('erpnext.accounts.utils.get_account_balances', {
            accounts: rootAccounts,
            company: company.value,
            include_default_fb_balances: true,
          })
        : rootAccounts
    } else {
      roots.value = await frappeGet('frappe.desk.treeview.get_children', {
        doctype: 'Account',
        parent: '',
      })
    }
  } catch (e) {
    console.error('Failed to load account roots', e)
  } finally {
    isLoading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  const q = searchQuery.value.trim()
  if (!q) {
    searchResults.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      searchResults.value = await frappeGet('frappe.client.get_list', {
        doctype: 'Account',
        filters: JSON.stringify([['name', 'like', `%${q}%`]]),
        fields: JSON.stringify(['name']),
        limit_page_length: 20,
      })
    } catch (e) {
      console.error('Account search failed', e)
    }
  }, 250)
}

function selectFromSearch(name) {
  searchQuery.value = ''
  searchResults.value = []
  onSelect(name)
}

async function onSelect(name) {
  selectedAccount.value = name
  detailLoading.value = true
  detail.value = null
  balance.value = null
  try {
    detail.value = await frappeGet('frappe.client.get', { doctype: 'Account', name })
    if (company.value && detail.value) {
      const [result] = await frappeGet('erpnext.accounts.utils.get_account_balances', {
        accounts: [{ value: name, account_currency: detail.value.account_currency }],
        company: company.value,
        include_default_fb_balances: true,
      })
      balance.value = result?.balance ?? null
    }
  } catch (e) {
    console.error('Failed to load account detail', e)
  } finally {
    detailLoading.value = false
  }
}
</script>
