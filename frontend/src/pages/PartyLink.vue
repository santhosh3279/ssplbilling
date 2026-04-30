<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] text-[13px]">
    <!-- HEADER -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            @click="$router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← Dashboard
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-semibold text-[var(--color-text)]">
            Party Link Management
          </h1>
        </div>
      </div>
    </header>

    <!-- CONTENT -->
    <main class="flex-1 p-6">
      <div class="mx-auto max-w-4xl">
        
        <!-- CREATE NEW LINK CARD -->
        <div class="mb-6 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 class="mb-4 text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Create New Link</h2>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Primary Party -->
            <div>
              <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Primary Party (e.g. Customer)</label>
              <div class="flex gap-2 mb-2">
                <select v-model="form.primary_role" class="w-1/3 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-xs outline-none focus:border-[var(--color-info)]">
                  <option value="Customer">Customer</option>
                  <option value="Supplier">Supplier</option>
                </select>
                <div class="relative flex-1">
                  <input 
                    v-model="primaryQuery" 
                    @input="search('primary')"
                    placeholder="Search party..."
                    class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-xs outline-none focus:border-[var(--color-info)]"
                  />
                  <div v-if="primaryOptions.length" class="absolute left-0 right-0 top-full z-50 mt-1 max-h-48 overflow-y-auto rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
                    <div 
                      v-for="opt in primaryOptions" :key="opt.name"
                      @click="selectParty('primary', opt)"
                      class="cursor-pointer px-3 py-2 text-xs hover:bg-[var(--color-info)] hover:text-white"
                    >
                      <div class="font-bold">{{ opt.name }}</div>
                      <div class="text-[10px] opacity-70">{{ opt.customer_name || opt.supplier_name }}</div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="form.primary_party" class="rounded bg-[var(--color-info)]/10 px-3 py-1 text-xs font-semibold text-[var(--color-info)] flex justify-between items-center">
                <span>{{ form.primary_party }}</span>
                <button @click="form.primary_party = ''" class="hover:text-red-500">✕</button>
              </div>
            </div>

            <!-- Secondary Party -->
            <div>
              <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Secondary Party (e.g. Supplier)</label>
              <div class="flex gap-2 mb-2">
                <select v-model="form.secondary_role" class="w-1/3 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-xs outline-none focus:border-[var(--color-info)]">
                  <option value="Supplier">Supplier</option>
                  <option value="Customer">Customer</option>
                </select>
                <div class="relative flex-1">
                  <input 
                    v-model="secondaryQuery" 
                    @input="search('secondary')"
                    placeholder="Search party..."
                    class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-xs outline-none focus:border-[var(--color-info)]"
                  />
                  <div v-if="secondaryOptions.length" class="absolute left-0 right-0 top-full z-50 mt-1 max-h-48 overflow-y-auto rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
                    <div 
                      v-for="opt in secondaryOptions" :key="opt.name"
                      @click="selectParty('secondary', opt)"
                      class="cursor-pointer px-3 py-2 text-xs hover:bg-[var(--color-info)] hover:text-white"
                    >
                      <div class="font-bold">{{ opt.name }}</div>
                      <div class="text-[10px] opacity-70">{{ opt.customer_name || opt.supplier_name }}</div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="form.secondary_party" class="rounded bg-[var(--color-info)]/10 px-3 py-1 text-xs font-semibold text-[var(--color-info)] flex justify-between items-center">
                <span>{{ form.secondary_party }}</span>
                <button @click="form.secondary_party = ''" class="hover:text-red-500">✕</button>
              </div>
            </div>
          </div>

          <div class="mt-6 flex justify-end">
            <button 
              @click="createLink"
              :disabled="!form.primary_party || !form.secondary_party || loading"
              class="rounded bg-[var(--color-info)] px-6 py-2 text-xs font-bold text-white hover:bg-[var(--color-info)]/90 disabled:opacity-50"
            >
              {{ loading ? 'Creating...' : 'Create Link' }}
            </button>
          </div>
        </div>

        <!-- EXISTING LINKS TABLE -->
        <div class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface-raised)] px-6 py-3">
            <h2 class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Existing Links</h2>
            <button @click="fetchLinks" class="text-[10px] text-[var(--color-info)] hover:underline">Refresh</button>
          </div>
          
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface)]/50 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-3">Primary Party</th>
                  <th class="px-6 py-3">Role</th>
                  <th class="px-6 py-2 text-center text-[var(--color-border)]">➔</th>
                  <th class="px-6 py-3">Secondary Party</th>
                  <th class="px-6 py-3">Role</th>
                  <th class="px-6 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr v-if="links.length === 0" class="text-center text-[var(--color-text-muted)]">
                  <td colspan="6" class="py-8 italic">No party links found.</td>
                </tr>
                <tr v-for="link in links" :key="link.name" class="hover:bg-[var(--color-surface-raised)] transition-colors">
                  <td class="px-6 py-3 font-medium">{{ link.primary_party }}</td>
                  <td class="px-6 py-3">
                    <span class="rounded bg-gray-100 px-2 py-0.5 text-[10px] text-gray-600">{{ link.primary_role }}</span>
                  </td>
                  <td class="px-6 py-3 text-center text-[var(--color-border)]">➔</td>
                  <td class="px-6 py-3 font-medium">{{ link.secondary_party }}</td>
                  <td class="px-6 py-3">
                    <span class="rounded bg-gray-100 px-2 py-0.5 text-[10px] text-gray-600">{{ link.secondary_role }}</span>
                  </td>
                  <td class="px-6 py-3 text-right">
                    <button @click="deleteLink(link.name)" class="text-xs font-bold text-red-500 hover:text-red-700">Delete</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { frappeGet, frappePost } from '../api'

const links = ref([])
const loading = ref(false)
const primaryQuery = ref('')
const secondaryQuery = ref('')
const primaryOptions = ref([])
const secondaryOptions = ref([])

const form = reactive({
  primary_party: '',
  primary_role: 'Customer',
  secondary_party: '',
  secondary_role: 'Supplier'
})

async function fetchLinks() {
  try {
    links.value = await frappeGet('ssplbilling.api.party_link_api.get_party_links')
  } catch (err) {
    console.error(err)
  }
}

async function search(type) {
  const query = type === 'primary' ? primaryQuery.value : secondaryQuery.value
  const doctype = type === 'primary' ? form.primary_role : form.secondary_role
  
  if (query.length < 2) {
    if (type === 'primary') primaryOptions.value = []
    else secondaryOptions.value = []
    return
  }
  
  try {
    const opts = await frappeGet('ssplbilling.api.party_link_api.search_parties', {
      doctype,
      query
    })
    if (type === 'primary') primaryOptions.value = opts
    else secondaryOptions.value = opts
  } catch (err) {
    console.error(err)
  }
}

function selectParty(type, party) {
  if (type === 'primary') {
    form.primary_party = party.name
    primaryOptions.value = []
    primaryQuery.value = ''
  } else {
    form.secondary_party = party.name
    secondaryOptions.value = []
    secondaryQuery.value = ''
  }
}

async function createLink() {
  if (!form.primary_party || !form.secondary_party) return
  
  loading.value = true
  try {
    await frappePost('ssplbilling.api.party_link_api.add_party_link', {
      primary_party: form.primary_party,
      primary_role: form.primary_role,
      secondary_party: form.secondary_party,
      secondary_role: form.secondary_role
    })
    
    // Reset form
    form.primary_party = ''
    form.secondary_party = ''
    
    // Refresh links
    await fetchLinks()
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function deleteLink(name) {
  if (!confirm('Are you sure you want to delete this link?')) return
  
  try {
    await frappePost('ssplbilling.api.party_link_api.remove_party_link', { name })
    await fetchLinks()
  } catch (err) {
    console.error(err)
  }
}

onMounted(() => {
  fetchLinks()
})
</script>
