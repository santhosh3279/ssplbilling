<template>
  <li>
    <div
      class="group flex items-center gap-1.5 rounded px-2 py-1.5 cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
      :class="selected === node.value ? 'bg-[var(--color-surface-raised)] text-[var(--color-highlight)]' : 'text-[var(--color-text)]'"
      :style="{ paddingLeft: (level * 18 + 8) + 'px' }"
      @click="onRowClick"
    >
      <span
        class="flex h-4 w-4 shrink-0 items-center justify-center text-[var(--color-text-muted)]"
        @click.stop="toggle"
      >
        <svg v-if="node.expandable" class="h-3 w-3 transition-transform" :class="expanded ? 'rotate-90' : ''" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </span>
      <span v-if="loading" class="text-xs text-[var(--color-text-muted)] animate-pulse">...</span>
      <span class="text-sm truncate" :class="node.expandable ? 'font-semibold' : ''">{{ node.title || node.value }}</span>

      <span class="ml-auto flex shrink-0 items-center gap-2 pl-2">
        <span class="hidden items-center gap-1 group-hover:flex">
          <button
            @click.stop="onEdit"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--color-text-muted)] hover:border-[var(--color-info)] hover:text-[var(--color-info)] transition-colors"
            title="Edit Account"
          >Edit</button>
          <button
            v-if="node.expandable"
            @click.stop="onAddChild"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--color-text-muted)] hover:border-[var(--color-success)] hover:text-[var(--color-success)] transition-colors"
            title="Add Child Account"
          >+ Child</button>
          <button
            @click.stop="onViewLedger"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--color-text-muted)] hover:border-[var(--color-highlight)] hover:text-[var(--color-highlight)] transition-colors"
            title="View Ledger"
          >Ledger</button>
        </span>
        <span v-if="balanceText" class="font-mono text-xs font-bold" :class="node.balance > 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'">
          {{ balanceText }}
        </span>
      </span>
    </div>

    <ul v-if="expanded && children.length" class="list-none">
      <AccountTreeNode
        v-for="child in children"
        :key="child.value"
        :node="child"
        :level="level + 1"
        :selected="selected"
        :company="company"
        @select="(v) => emit('select', v)"
      />
    </ul>
    <div v-else-if="expanded && !loading && !children.length" class="text-xs italic text-[var(--color-text-muted)]" :style="{ paddingLeft: (level * 18 + 32) + 'px' }">
      No accounts
    </div>
  </li>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'

const router = useRouter()

const props = defineProps({
  node: { type: Object, required: true },
  level: { type: Number, default: 0 },
  selected: { type: String, default: '' },
  company: { type: String, default: '' },
})

const emit = defineEmits(['select'])

const expanded = ref(false)
const loading = ref(false)
const children = ref([])
let loaded = false

function formatCurrency(val) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(val || 0)
}

const balanceText = computed(() => {
  if (props.node.balance === undefined || props.node.balance === null) return ''
  const drCr = props.node.balance > 0 ? 'Dr' : 'Cr'
  return `${formatCurrency(Math.abs(props.node.balance))} ${drCr}`
})

async function toggle() {
  if (!props.node.expandable) return
  expanded.value = !expanded.value
  if (expanded.value && !loaded) {
    loading.value = true
    try {
      if (props.company) {
        const kids = await frappeGet('erpnext.accounts.utils.get_children', {
          doctype: 'Account',
          parent: props.node.value,
          company: props.company,
        })
        children.value = kids.length
          ? await frappeGet('erpnext.accounts.utils.get_account_balances', {
              accounts: kids,
              company: props.company,
              include_default_fb_balances: true,
            })
          : kids
      } else {
        children.value = await frappeGet('frappe.desk.treeview.get_children', {
          doctype: 'Account',
          parent: props.node.value,
        })
      }
      loaded = true
    } catch (e) {
      console.error('Failed to load child accounts', e)
    } finally {
      loading.value = false
    }
  }
}

function onRowClick() {
  emit('select', props.node.value)
  if (props.node.expandable) toggle()
}

function onEdit() {
  window.open(`/app/account/${encodeURIComponent(props.node.value)}`, '_blank')
}

function onAddChild() {
  const params = new URLSearchParams({ parent_account: props.node.value })
  if (props.company) params.set('company', props.company)
  window.open(`/app/account/new?${params}`, '_blank')
}

function onViewLedger() {
  router.push({
    name: 'GeneralLedger',
    query: { party: props.node.value, party_type: 'Account', label: props.node.title || props.node.value },
  })
}
</script>
