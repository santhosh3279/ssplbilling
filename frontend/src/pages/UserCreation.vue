<template>
  <div class="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)]">
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
      <div class="flex items-center gap-4">
        <button type="button" class="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)]" @click="router.push('/ssplbillingsettings')">← Settings</button>
        <h1 class="text-lg font-bold">Create Customer User</h1>
      </div>
    </header>

    <main class="mx-auto max-w-xl p-6">
      <form class="space-y-5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6" @submit.prevent="createUser">
        <div>
          <label for="username" class="mb-1 block text-sm font-semibold">Username (login email)</label>
          <input id="username" v-model.trim="username" type="email" autocomplete="off" required :disabled="isSaving || !!createdUser"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 focus:border-[var(--color-info)] focus:outline-none" />
        </div>
        <div v-if="!createdUser">
          <label for="password" class="mb-1 block text-sm font-semibold">Password</label>
          <input id="password" v-model="password" type="password" autocomplete="new-password" required :disabled="isSaving"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 focus:border-[var(--color-info)] focus:outline-none" />
          <p class="mt-1 text-xs text-[var(--color-text-muted)]">The site's password policy applies.</p>
        </div>
        <div>
          <label for="customer" class="mb-1 block text-sm font-semibold">Linked Customer</label>
          <select id="customer" v-model="customer" required :disabled="isLoadingCustomers || isSaving || !!createdUser"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 focus:border-[var(--color-info)] focus:outline-none">
            <option value="">{{ isLoadingCustomers ? 'Loading customers...' : 'Select a customer' }}</option>
            <option v-for="item in customers" :key="item.name" :value="item.name">{{ item.customer_name || item.name }} ({{ item.name }})</option>
          </select>
        </div>

        <p v-if="error" role="alert" class="rounded border border-[var(--color-danger)] p-3 text-sm text-[var(--color-danger)]">{{ error }}</p>
        <p v-if="success" role="status" class="rounded border border-[var(--color-success)] p-3 text-sm text-[var(--color-success)]">{{ success }}</p>

        <button type="submit" :disabled="isSaving || isLoadingCustomers || !!success"
          class="rounded bg-[var(--color-info)] px-4 py-2 font-semibold text-[var(--color-text-on-highlight)] disabled:opacity-50">
          {{ isSaving ? 'Saving...' : createdUser ? 'Retry Customer Link' : 'Create User' }}
        </button>
        <button v-if="success" type="button" class="ml-3 rounded border border-[var(--color-border)] px-4 py-2" @click="resetForm">Create Another</button>
      </form>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

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

async function createUser() {
  if (isSaving.value || success.value) return
  error.value = ''
  isSaving.value = true
  try {
    if (!createdUser.value) {
      const login = username.value.trim()
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
  createdUser.value = ''
  error.value = ''
  success.value = ''
}

onMounted(loadCustomers)
</script>
