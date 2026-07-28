<template>
  <li>
    <div
      class="flex items-center gap-1.5 rounded px-2 py-1.5 cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
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
      <span v-if="balanceText" class="ml-auto shrink-0 pl-2 font-mono text-xs" :class="node.balance > 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'">
        {{ balanceText }}
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
import { frappeGet } from '../api.js'

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
</script>
