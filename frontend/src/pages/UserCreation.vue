<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] font-sans text-[var(--color-text)]">
    <!-- Existing customer users (styled like the Item_Invoice_Template sidebar); picking one opens it for editing -->
    <aside
      class="flex shrink-0 flex-col overflow-hidden border-r border-[var(--color-border)] bg-[var(--color-bg)] transition-all duration-300 ease-in-out"
      :class="isSidebarCollapsed ? 'w-0 border-r-0' : 'w-[20%] min-w-[16rem] xl:w-[15%]'"
    >
      <div :class="isSidebarCollapsed ? 'invisible opacity-0' : 'visible opacity-100'" class="flex h-full flex-col transition-opacity duration-200">
        <div class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)] p-2 text-center">
          <div class="text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Customer Users</div>
        </div>

        <div class="flex flex-col gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/20 p-3">
          <div class="group relative">
            <input v-model="userQuery" type="text" autocomplete="off" placeholder="Search users..."
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-10 pr-3 text-[15px] font-bold text-[var(--color-text)] placeholder-[var(--color-text-muted)] outline-none transition-all focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/10"
              @keydown.down.prevent="focusUserRow(0)" />
            <svg class="absolute left-3.5 top-2.5 text-[var(--color-text-muted)] transition-colors group-focus-within:text-[var(--color-info)]" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </div>
          <button type="button" :disabled="isSaving" @click="resetForm"
            class="w-full rounded-xl border py-1.5 text-[15px] font-bold uppercase transition-all disabled:opacity-50"
            :class="editingUser ? 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)]' : 'border-[var(--color-info)] bg-[var(--color-info)]/20 text-[var(--color-info)] shadow-sm'">
            + New User
          </button>
        </div>

        <div class="scrollbar-none flex-1 overflow-y-auto">
          <div v-if="isLoadingUsers" class="p-4 text-center text-lg text-[var(--color-text-muted)]">Loading...</div>
          <div v-else-if="usersError" role="alert" class="p-4 text-center text-lg text-[var(--color-danger)]">{{ usersError }}</div>
          <div v-else-if="!filteredUsers.length" class="p-4 text-center text-lg italic text-[var(--color-text-muted)]">No users found</div>
          <template v-else>
          <div v-for="(u, idx) in filteredUsers" :key="u.user"
            :ref="el => { userRowRefs[idx] = el }"
            tabindex="0"
            class="group cursor-pointer border-b border-[var(--color-border)] px-2 py-1 outline-none transition-colors focus:border-l-2 focus:border-l-[var(--color-focus)] focus:bg-[var(--color-focus)]"
            :class="{ 'border-l-2 border-l-[var(--color-focus)] bg-[var(--color-focus)]': editingUser === u.user }"
            @click="selectUser(u)"
            @keydown.enter="selectUser(u)"
            @keydown.up.prevent="focusUserRow(idx - 1)"
            @keydown.down.prevent="focusUserRow(idx + 1)"
          >
            <div class="flex min-w-0 items-center gap-1.5">
              <span class="h-2 w-2 shrink-0 rounded-full" :class="u.enabled ? 'bg-[var(--color-success)]' : 'bg-[var(--color-danger)]'"
                :title="u.enabled ? 'Enabled' : 'Disabled'"></span>
              <span class="truncate font-mono text-xl group-focus:font-bold group-focus:text-[var(--color-text-on-focus)]"
                :class="editingUser === u.user ? 'font-bold text-[var(--color-text-on-focus)]' : 'text-[var(--color-highlight)]'">{{ u.user }}</span>
            </div>
            <div class="truncate text-lg group-focus:text-[var(--color-text-on-focus)]"
              :class="editingUser === u.user ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">
              {{ u.customer_name || u.customer }}
            </div>
          </div>
          </template>
        </div>
      </div>
    </aside>

    <div class="flex flex-1 flex-col overflow-hidden">
      <div class="flex items-center gap-3 border-b border-[var(--color-border)]/60 bg-[var(--color-surface-raised)]/60 px-4 py-2">
        <button type="button" class="mr-1 flex items-center justify-center rounded p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-raised)]"
          :title="isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'" @click="isSidebarCollapsed = !isSidebarCollapsed">
          <svg v-if="isSidebarCollapsed" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 6 12 11 7"></polyline><polyline points="18 17 13 12 18 7"></polyline></svg>
        </button>
        <button type="button" class="rounded px-2 py-1 text-2xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]" @click="router.push('/')">&larr; Back</button>
        <span class="text-2xl text-[var(--color-border)]">|</span>
        <span class="text-2xl font-semibold text-[var(--color-text)]">{{ editingUser ? `Edit ${editingUser}` : 'Create Customer User' }}</span>
      </div>

    <main class="flex-1 overflow-y-auto p-6">
      <form class="mx-auto max-w-xl space-y-5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6" @submit.prevent="submitForm">
        <div>
          <label for="username" class="mb-1 block text-sm font-semibold">Username (login email)</label>
          <div class="flex rounded border border-[var(--color-border)] bg-[var(--color-bg)] focus-within:border-[var(--color-info)]">
            <input id="username" v-model.trim="username" type="text" autocomplete="off" required :disabled="isSaving || !!createdUser"
              class="min-w-0 flex-1 rounded-l bg-transparent px-3 py-2 focus:outline-none" @input="stripEmailDomain" />
            <span class="flex items-center border-l border-[var(--color-border)] px-3 text-sm text-[var(--color-text-muted)]">{{ loginDomain }}</span>
          </div>
          <p v-if="username" class="mt-1 text-xs text-[var(--color-text-muted)]">Login: {{ loginEmail }}</p>
        </div>
        <div ref="customerBox" class="relative">
          <label for="customer" class="mb-1 block text-sm font-semibold">Linked Customer</label>
          <input id="customer" v-model="customerQuery" type="text" autocomplete="off"
            :placeholder="isLoadingCustomers ? 'Loading customers...' : 'Search customer by name or ID'"
            :disabled="isLoadingCustomers || isSaving || !!createdUser"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 focus:border-[var(--color-info)] focus:outline-none"
            @focus="showCustomerList = true" @input="onCustomerInput" @keydown="onCustomerKeydown" />
          <ul v-if="showCustomerList && filteredCustomers.length"
            class="absolute z-20 mt-1 max-h-64 w-full overflow-y-auto rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
            <li v-for="(item, i) in filteredCustomers" :key="item.name"
              class="cursor-pointer px-3 py-1.5 text-sm"
              :class="i === activeCustomerIdx ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'hover:bg-[var(--color-surface-raised)]'"
              @mousedown.prevent="selectCustomer(item)" @mouseenter="activeCustomerIdx = i">
              {{ item.customer_name || item.name }} <span class="opacity-70">({{ item.name }})</span>
            </li>
          </ul>
          <p v-if="showCustomerList && customerQuery && !filteredCustomers.length && !isLoadingCustomers"
            class="mt-1 text-xs text-[var(--color-text-muted)]">No matching customer.</p>
        </div>

        <!-- Price list + mobile for the selected customer (catalogue orders price from this list) -->
        <!-- Enter inside this panel must not submit the Create User form -->
        <div v-if="customer" class="space-y-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-4" @keydown.enter.prevent>
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-bold">Customer Pricing</h2>
            <span class="text-xs text-[var(--color-text-muted)]">{{ customer }}</span>
          </div>
          <p v-if="isLoadingPricing" class="text-sm text-[var(--color-text-muted)]">Loading...</p>
          <template v-else>
            <DropdownField v-model="pricing.price_list" :options="priceLists" label="Price List" placeholder="Select a price list" />
            <div>
              <label for="customer-mobile" class="mb-1 block text-sm font-semibold text-[var(--color-text-muted)]">Mobile Number</label>
              <input id="customer-mobile" v-model.trim="pricing.mobile_no" type="tel" inputmode="numeric" maxlength="10" autocomplete="off"
                title="Click to use this mobile number as the password"
                @click="useMobileAsPassword" @input="syncMobilePassword"
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm focus:border-[var(--color-info)] focus:outline-none" />
            </div>
            <p v-if="pricingError" role="alert" class="text-sm text-[var(--color-danger)]">{{ pricingError }}</p>
            <p v-if="pricingSaved" role="status" class="text-sm text-[var(--color-success)]">{{ pricingSaved }}</p>
            <button type="button" :disabled="isSavingPricing || !pricingDirty"
              class="rounded border border-[var(--color-info)] px-4 py-1.5 text-sm font-semibold text-[var(--color-info)] disabled:opacity-50"
              @click="savePricing">
              {{ isSavingPricing ? 'Saving...' : 'Save Price List & Mobile' }}
            </button>
          </template>
        </div>

        <div v-if="!createdUser">
          <label for="password" class="mb-1 block text-sm font-semibold">Password</label>
          <input id="password" v-model="password" type="password" autocomplete="new-password" :required="!editingUser" :disabled="isSaving"
            @input="passwordFromMobile = false"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 focus:border-[var(--color-info)] focus:outline-none" />
          <p class="mt-1 text-xs text-[var(--color-text-muted)]">
            {{ editingUser ? 'Leave blank to keep the current password. ' : '' }}The site's password policy applies.
          </p>
        </div>

        <p v-if="error" role="alert" class="rounded border border-[var(--color-danger)] p-3 text-sm text-[var(--color-danger)]">{{ error }}</p>
        <p v-if="success" role="status" class="rounded border border-[var(--color-success)] p-3 text-sm text-[var(--color-success)]">{{ success }}</p>

        <button type="submit" :disabled="isSaving || isLoadingCustomers || (!!success && !editingUser)"
          class="rounded bg-[var(--color-info)] px-4 py-2 font-semibold text-[var(--color-text-on-highlight)] disabled:opacity-50">
          {{ isSaving ? 'Saving...' : editingUser ? 'Save Changes' : createdUser ? 'Retry Customer Link' : 'Create User' }}
        </button>
        <button v-if="success && !editingUser" type="button" class="ml-3 rounded border border-[var(--color-border)] px-4 py-2" @click="resetForm">Create Another</button>
      </form>
    </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { getCachedList } from '../services/masterCache.js'
import DropdownField from '../components/DropdownField.vue'

const router = useRouter()
const username = ref('')
const password = ref('')
const customer = ref('')
const customers = ref([])
const createdUser = ref('')
const isLoadingCustomers = ref(false)
const isSaving = ref(false)
const error = ref('')
const success = ref('')

// Logins are always on this domain; the field takes only the part before @.
const LOGIN_DOMAIN = '@ctr.com'
// An edited user keeps its own domain; new users get LOGIN_DOMAIN.
const loginDomain = ref(LOGIN_DOMAIN)
const loginEmail = computed(() => username.value ? `${username.value}${loginDomain.value}` : '')

function stripEmailDomain() {
  // A pasted full address keeps only its local part.
  const at = username.value.indexOf('@')
  if (at !== -1) username.value = username.value.slice(0, at)
}

// Clicking the customer's mobile number copies it into the password; while the
// password is that copy, editing the mobile keeps them in step.
const passwordFromMobile = ref(false)

function useMobileAsPassword() {
  if (createdUser.value || !pricing.value.mobile_no) return
  password.value = pricing.value.mobile_no
  passwordFromMobile.value = true
}

function syncMobilePassword() {
  if (passwordFromMobile.value && !createdUser.value) password.value = pricing.value.mobile_no
}

// ── Searchable customer box ──
const customerBox = ref(null)
const customerQuery = ref('')
const showCustomerList = ref(false)
const activeCustomerIdx = ref(0)
const CUSTOMER_LIST_LIMIT = 50

const filteredCustomers = computed(() => {
  const terms = customerQuery.value.trim().toLowerCase().split(/\s+/).filter(Boolean)
  const rows = terms.length
    ? customers.value.filter((c) => {
      const hay = `${c.customer_name || ''} ${c.name}`.toLowerCase()
      return terms.every(t => hay.includes(t))
    })
    : customers.value
  return rows.slice(0, CUSTOMER_LIST_LIMIT)
})

function customerLabel(c) {
  return c.customer_name && c.customer_name !== c.name ? `${c.customer_name} (${c.name})` : c.name
}

function onCustomerInput() {
  showCustomerList.value = true
  activeCustomerIdx.value = 0
  // Typing again un-picks the customer until one is chosen from the list.
  if (customer.value) {
    customer.value = ''
    resetPricing()
  }
}

function onCustomerKeydown(e) {
  const n = filteredCustomers.value.length
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    showCustomerList.value = true
    if (n) activeCustomerIdx.value = (activeCustomerIdx.value + 1) % n
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (n) activeCustomerIdx.value = (activeCustomerIdx.value - 1 + n) % n
  } else if (e.key === 'Enter') {
    if (showCustomerList.value && n) {
      e.preventDefault()
      selectCustomer(filteredCustomers.value[activeCustomerIdx.value])
    }
  } else if (e.key === 'Escape') {
    showCustomerList.value = false
  }
}

function selectCustomer(c) {
  if (!c) return
  customer.value = c.name
  customerQuery.value = customerLabel(c)
  showCustomerList.value = false
  loadPricing(c.name)
}

function onClickOutside(e) {
  if (customerBox.value && !customerBox.value.contains(e.target)) showCustomerList.value = false
}

// ── Customer price list + mobile ──
const priceLists = ref([])
const pricing = ref({ price_list: '', mobile_no: '' })
const loadedPricing = ref({ price_list: '', mobile_no: '' })
const isLoadingPricing = ref(false)
const isSavingPricing = ref(false)
const pricingError = ref('')
const pricingSaved = ref('')

const pricingDirty = computed(() =>
  pricing.value.price_list !== loadedPricing.value.price_list ||
  pricing.value.mobile_no !== loadedPricing.value.mobile_no
)

function resetPricing() {
  // A password copied from the previous customer's mobile doesn't carry over.
  if (passwordFromMobile.value) {
    password.value = ''
    passwordFromMobile.value = false
  }
  pricing.value = { price_list: '', mobile_no: '' }
  loadedPricing.value = { price_list: '', mobile_no: '' }
  pricingError.value = ''
  pricingSaved.value = ''
}

function applyPricing(res) {
  const next = { price_list: res?.default_price_list || '', mobile_no: res?.mobile_no || '' }
  pricing.value = { ...next }
  loadedPricing.value = { ...next }
}

async function loadPriceLists() {
  try {
    const rows = await getCachedList({
      doctype: 'Price List',
      fields: ['name'],
      filters: { enabled: 1, selling: 1 },
      order_by: 'name asc',
      limit_page_length: 0,
    })
    priceLists.value = (rows || []).map(r => r.name)
  } catch (e) {
    pricingError.value = 'Could not load price lists: ' + e.message
  }
}

async function loadPricing(name) {
  resetPricing()
  isLoadingPricing.value = true
  try {
    const res = await frappeGet('ssplbilling.api.customersearch_api.get_customer_price_setting', { customer: name })
    if (customer.value === name) applyPricing(res)
  } catch (e) {
    if (customer.value === name) pricingError.value = 'Could not load customer pricing: ' + e.message
  } finally {
    if (customer.value === name) isLoadingPricing.value = false
  }
}

async function savePricing() {
  pricingError.value = ''
  pricingSaved.value = ''
  const priceList = (pricing.value.price_list || '').trim()
  const mobile = (pricing.value.mobile_no || '').trim()
  if (priceList && !priceLists.value.includes(priceList)) {
    pricingError.value = 'Pick a price list from the list.'
    return
  }
  if (mobile && !/^\d{10}$/.test(mobile)) {
    pricingError.value = 'Mobile number must be 10 digits.'
    return
  }
  const name = customer.value
  isSavingPricing.value = true
  try {
    const res = await frappePost('ssplbilling.api.customersearch_api.set_customer_price_setting', {
      customer: name,
      price_list: priceList,
      mobile_no: mobile,
    }, { silent: true })
    if (customer.value === name) {
      applyPricing(res)
      pricingSaved.value = 'Price list and mobile saved.'
    }
  } catch (e) {
    pricingError.value = 'Could not save: ' + e.message
  } finally {
    isSavingPricing.value = false
  }
}

async function loadCustomers() {
  isLoadingCustomers.value = true
  try {
    customers.value = await frappeGet('frappe.client.get_list', {
      doctype: 'Customer',
      fields: ['name', 'customer_name'],
      limit_page_length: 0,
      order_by: 'customer_name asc',
    })
  } catch (e) {
    error.value = 'Could not load customers: ' + e.message
  } finally {
    isLoadingCustomers.value = false
  }
}

// ── Existing users (left panel) ──
const users = ref([])
const userQuery = ref('')
const isLoadingUsers = ref(false)
const usersError = ref('')
// Login of the user open for editing; '' means the form creates a new user.
const editingUser = ref('')
// Customer the edited user was loaded with; the link is rewritten only when this changes.
const editingCustomer = ref('')
const isSidebarCollapsed = ref(false)
const userRowRefs = ref([])

function focusUserRow(idx) {
  if (idx < 0 || idx >= filteredUsers.value.length) return
  userRowRefs.value[idx]?.focus()
}

const filteredUsers = computed(() => {
  const terms = userQuery.value.trim().toLowerCase().split(/\s+/).filter(Boolean)
  if (!terms.length) return users.value
  return users.value.filter((u) => {
    const hay = `${u.user} ${u.customer} ${u.customer_name || ''}`.toLowerCase()
    return terms.every(t => hay.includes(t))
  })
})

async function loadUsers() {
  isLoadingUsers.value = true
  usersError.value = ''
  try {
    users.value = await frappeGet('ssplbilling.api.customersearch_api.get_customer_users') || []
  } catch (e) {
    usersError.value = 'Could not load users: ' + e.message
  } finally {
    isLoadingUsers.value = false
  }
}

function splitLogin(login) {
  const at = login.indexOf('@')
  return at === -1 ? [login, ''] : [login.slice(0, at), login.slice(at)]
}

function selectUser(u) {
  if (isSaving.value) return
  resetForm()
  editingUser.value = u.user
  editingCustomer.value = u.customer
  ;[username.value, loginDomain.value] = splitLogin(u.user)
  selectCustomer(customers.value.find(c => c.name === u.customer) || { name: u.customer, customer_name: u.customer_name })
}

function submitForm() {
  return editingUser.value ? saveUser() : createUser()
}

async function saveUser() {
  if (isSaving.value) return
  error.value = ''
  success.value = ''
  if (!username.value || !customer.value) {
    error.value = 'Enter a username and linked customer.'
    return
  }
  isSaving.value = true
  try {
    const res = await frappePost('ssplbilling.api.customersearch_api.update_customer_user', {
      user: editingUser.value,
      new_user: loginEmail.value,
      customer: customer.value !== editingCustomer.value ? customer.value : '',
      password: password.value || '',
    }, { silent: true })
    editingUser.value = res.user
    editingCustomer.value = res.customer || customer.value
    ;[username.value, loginDomain.value] = splitLogin(res.user)
    password.value = ''
    passwordFromMobile.value = false
    success.value = `User ${res.user} saved.`
    loadUsers()
  } catch (e) {
    error.value = 'Could not save user: ' + e.message
  } finally {
    isSaving.value = false
  }
}

async function createUser() {
  if (isSaving.value || success.value) return
  error.value = ''
  isSaving.value = true
  try {
    if (!createdUser.value) {
      const login = loginEmail.value
      if (!login || !password.value || !customer.value) {
        throw new Error('Enter a username, password, and linked customer.')
      }
      const user = await frappePost('frappe.client.insert', {
        doc: {
          doctype: 'User',
          email: login,
          first_name: login.split('@')[0],
          new_password: password.value,
          user_type: 'Website User',
          enabled: 1,
          send_welcome_email: 0,
        },
      }, { silent: true })
      createdUser.value = user.name
      password.value = ''
    }

    await frappePost('frappe.client.insert', {
      doc: {
        doctype: 'User Permission',
        user: createdUser.value,
        allow: 'Customer',
        for_value: customer.value,
        apply_to_all_doctypes: 1,
      },
    }, { silent: true })
    success.value = `User ${createdUser.value} created and linked to customer ${customer.value}.`
    loadUsers()
  } catch (e) {
    error.value = createdUser.value
      ? `User ${createdUser.value} was created, but the customer link failed: ${e.message}. Retry the customer link.`
      : 'Could not create user: ' + e.message
  } finally {
    isSaving.value = false
  }
}

function resetForm() {
  username.value = ''
  password.value = ''
  customer.value = ''
  customerQuery.value = ''
  passwordFromMobile.value = false
  resetPricing()
  createdUser.value = ''
  editingUser.value = ''
  editingCustomer.value = ''
  loginDomain.value = LOGIN_DOMAIN
  error.value = ''
  success.value = ''
}

onMounted(() => {
  loadCustomers()
  loadPriceLists()
  loadUsers()
  document.addEventListener('mousedown', onClickOutside)
})
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>
