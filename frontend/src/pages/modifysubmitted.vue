<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)] font-sans select-none overflow-hidden">
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button
          @click="$router.push('/')"
          class="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-info)] transition-all shadow-sm active:scale-95"
          title="Back to Dashboard (Esc)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
        </button>
        <div>
          <h1 class="text-xl font-black uppercase tracking-wider text-[var(--color-text)] flex items-center gap-2">
            <span>Modify Submitted Bill Date</span>
            <span class="text-xs px-2 py-0.5 rounded-md bg-[var(--color-info)]/15 text-[var(--color-info)] font-bold tracking-widest uppercase">
              Submitted Only
            </span>
          </h1>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <span class="text-xs font-mono text-[var(--color-text-muted)] bg-[var(--color-surface-raised)] px-2.5 py-1 rounded-lg border border-[var(--color-border)]">
          F8 or Enter to Save
        </span>
      </div>
    </header>

    <!-- BODY CONTAINER -->
    <main class="flex-1 overflow-y-auto custom-scrollbar p-6 lg:p-8">
      <div class="max-w-4xl mx-auto space-y-6">

        <!-- SEARCH / FETCH CARD -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <label class="block text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-2">
            Enter Invoice Number
          </label>
          <div class="flex items-center gap-3">
            <div class="relative flex-1">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-[var(--color-text-muted)] pointer-events-none">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </span>
              <input
                ref="invoiceInputRef"
                v-model="invoiceNo"
                @keydown.enter.prevent="handleFetch"
                type="text"
                placeholder="e.g. CTRG08392 or PO01052"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-11 pr-10 text-lg font-mono font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:ring-2 focus:ring-[var(--color-info)]/20 transition-all placeholder:text-[var(--color-text-muted)]/50 uppercase"
                :disabled="loadingFetch || loadingUpdate"
              />
              <button
                v-if="invoiceNo"
                @click="clearAll"
                type="button"
                class="absolute inset-y-0 right-0 flex items-center pr-3 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
                title="Clear"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <button
              @click="handleFetch"
              :disabled="!invoiceNo.trim() || loadingFetch"
              class="flex items-center gap-2 rounded-xl bg-[var(--color-info)] hover:brightness-110 active:scale-95 px-6 py-3 text-base font-bold text-[var(--color-text-on-highlight)] transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <svg v-if="loadingFetch" class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <span>{{ loadingFetch ? 'Fetching...' : 'Fetch' }}</span>
            </button>
          </div>

          <!-- Error message -->
          <div
            v-if="fetchError"
            class="mt-4 rounded-xl bg-[var(--color-danger)]/15 border border-[var(--color-danger)]/40 p-4 text-[var(--color-danger)] text-sm font-semibold flex items-start gap-3"
          >
            <svg class="shrink-0 mt-0.5" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <div class="flex-1 leading-relaxed">{{ fetchError }}</div>
          </div>

          <!-- Success message -->
          <div
            v-if="updateSuccessMessage"
            class="mt-4 rounded-xl bg-[var(--color-success)]/15 border border-[var(--color-success)]/40 p-4 text-[var(--color-success)] text-sm font-semibold flex items-start gap-3"
          >
            <svg class="shrink-0 mt-0.5" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <div class="flex-1 leading-relaxed">{{ updateSuccessMessage }}</div>
          </div>
        </div>

        <!-- INVOICE DETAILS & DATE MODIFICATION (Rendered once invoice is loaded) -->
        <div v-if="invoice" class="space-y-6">

          <!-- INVOICE SUMMARY HEADER -->
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div class="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-[var(--color-border)]">
              <div class="flex items-center gap-3">
                <div class="p-3 rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-info)]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <span class="text-2xl font-black font-mono tracking-tight text-[var(--color-text)]">
                      {{ invoice.name }}
                    </span>
                    <span class="px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider rounded-md bg-[var(--color-success)]/20 text-[var(--color-success)] border border-[var(--color-success)]/30">
                      Submitted
                    </span>
                    <span class="px-2 py-0.5 text-xs font-semibold rounded-md bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] border border-[var(--color-border)]">
                      {{ invoice.doctype }}
                    </span>
                  </div>
                  <p class="text-sm font-semibold text-[var(--color-text-muted)] mt-0.5">
                    {{ invoice.party_name || invoice.party }}
                  </p>
                </div>
              </div>

              <!-- Grand total -->
              <div class="text-right">
                <div class="text-xs uppercase tracking-widest text-[var(--color-text-muted)] font-bold">Grand Total</div>
                <div class="text-3xl font-black font-mono text-[var(--color-success)]">
                  ₹{{ fmtCurrency(invoice.grand_total) }}
                </div>
              </div>
            </div>

            <!-- Meta metrics row -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-5">
              <div class="p-3 rounded-xl bg-[var(--color-surface-raised)]/60 border border-[var(--color-border)]">
                <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Items Count</div>
                <div class="text-lg font-bold font-mono text-[var(--color-text)] mt-0.5">{{ invoice.item_count }} Items</div>
              </div>
              <div class="p-3 rounded-xl bg-[var(--color-surface-raised)]/60 border border-[var(--color-border)]">
                <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Outstanding</div>
                <div class="text-lg font-bold font-mono text-[var(--color-text)] mt-0.5">₹{{ fmtCurrency(invoice.outstanding_amount) }}</div>
              </div>
              <div class="p-3 rounded-xl bg-[var(--color-surface-raised)]/60 border border-[var(--color-border)]">
                <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Posting Time</div>
                <div class="text-lg font-bold font-mono text-[var(--color-text)] mt-0.5">{{ formatTime(invoice.posting_time) }}</div>
              </div>
              <div class="p-3 rounded-xl bg-[var(--color-surface-raised)]/60 border border-[var(--color-border)]">
                <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Company</div>
                <div class="text-sm font-bold text-[var(--color-text)] truncate mt-0.5" :title="invoice.company">{{ invoice.company }}</div>
              </div>
            </div>
          </div>

          <!-- DATE MODIFICATION CARD -->
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <h2 class="text-base font-black uppercase tracking-wider text-[var(--color-text)] mb-6 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-info)]">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              <span>Bill Date Configuration</span>
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

              <!-- CURRENT BILL DATE DISPLAY -->
              <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)]/60 p-5 flex flex-col justify-between">
                <div>
                  <span class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] block mb-1">
                    Current Bill Date
                  </span>
                  <div class="text-2xl font-black font-mono text-[var(--color-text)] mt-1">
                    {{ formatDateLong(invoice.posting_date) }}
                  </div>
                  <div class="text-sm font-mono text-[var(--color-text-muted)] mt-1">
                    ISO: {{ invoice.posting_date }}
                  </div>
                </div>
                <div class="mt-4 pt-3 border-t border-[var(--color-border)] text-xs text-[var(--color-text-muted)] flex items-center gap-1.5">
                  <span class="inline-block w-2 h-2 rounded-full bg-[var(--color-success)]"></span>
                  Active in Database
                </div>
              </div>

              <!-- NEW BILL DATE CONTROLLER -->
              <div class="rounded-xl border-2 p-5 flex flex-col justify-between transition-colors"
                :class="isDateChanged ? 'border-[var(--color-info)] bg-[var(--color-info)]/5' : 'border-[var(--color-border)] bg-[var(--color-bg)]/30'"
              >
                <div>
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold uppercase tracking-widest text-[var(--color-info)]">
                      New Bill Date
                    </span>
                    <span
                      v-if="isDateChanged"
                      class="text-xs font-bold px-2 py-0.5 rounded-full bg-[var(--color-info)] text-[var(--color-text-on-highlight)] font-mono"
                    >
                      {{ dateDiffLabel }}
                    </span>
                    <span v-else class="text-xs text-[var(--color-text-muted)] italic">
                      No change selected
                    </span>
                  </div>

                  <!-- Date adjustment bar with arrows and calendar picker -->
                  <div class="flex items-center gap-2 mt-2">
                    <!-- Left Arrow (Previous Day) -->
                    <button
                      type="button"
                      @click="adjustDate(-1)"
                      class="h-12 w-12 shrink-0 rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text)] hover:border-[var(--color-info)] hover:bg-[var(--color-surface)] active:scale-95 transition-all flex items-center justify-center cursor-pointer shadow-sm"
                      title="Move 1 Day Back (Left Arrow)"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m15 18-6-6 6-6"/>
                      </svg>
                    </button>

                    <!-- Date input with native calendar picker -->
                    <div class="relative flex-1">
                      <input
                        ref="newDateInputRef"
                        v-model="newBillDate"
                        type="date"
                        class="w-full h-12 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 text-lg font-mono font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:ring-2 focus:ring-[var(--color-info)]/20 transition-all cursor-pointer shadow-inner"
                      />
                    </div>

                    <!-- Right Arrow (Next Day) -->
                    <button
                      type="button"
                      @click="adjustDate(1)"
                      class="h-12 w-12 shrink-0 rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text)] hover:border-[var(--color-info)] hover:bg-[var(--color-surface)] active:scale-95 transition-all flex items-center justify-center cursor-pointer shadow-sm"
                      title="Move 1 Day Forward (Right Arrow)"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m9 18 6-6-6-6"/>
                      </svg>
                    </button>
                  </div>

                  <!-- Quick date preset buttons -->
                  <div class="flex items-center gap-2 mt-3">
                    <button
                      type="button"
                      @click="setPreset('today')"
                      class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-all cursor-pointer"
                    >
                      Today
                    </button>
                    <button
                      type="button"
                      @click="setPreset('yesterday')"
                      class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-all cursor-pointer"
                    >
                      Yesterday
                    </button>
                    <button
                      v-if="isDateChanged"
                      type="button"
                      @click="resetToOriginal"
                      class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-[var(--color-surface-raised)] hover:bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-warning)] transition-all cursor-pointer ml-auto"
                    >
                      Reset
                    </button>
                  </div>
                </div>

                <div class="mt-4 pt-3 border-t border-[var(--color-border)]">
                  <div class="text-xs font-semibold text-[var(--color-text-muted)] flex items-center justify-between">
                    <span>Target: {{ formatDateLong(newBillDate) }}</span>
                    <span class="font-mono">{{ newBillDate }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- ACTION BUTTON: CHANGE DATE -->
            <div class="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-[var(--color-border)]">
              <div class="text-xs text-[var(--color-text-muted)] flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="16" x2="12" y2="12"/>
                  <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                <span>Updates Invoice, GL entries, stock ledger, and payment ledger in database.</span>
              </div>

              <button
                @click="handleChangeDate"
                :disabled="!isDateChanged || loadingUpdate"
                class="w-full sm:w-auto flex items-center justify-center gap-2.5 rounded-xl bg-[var(--color-success)] hover:brightness-110 active:scale-95 px-8 py-3.5 text-base font-black uppercase tracking-wider text-[var(--color-text-on-highlight)] transition-all shadow-lg shadow-[var(--color-success)]/20 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none cursor-pointer"
              >
                <svg v-if="loadingUpdate" class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span>{{ loadingUpdate ? 'Updating Database...' : 'Change Date' }}</span>
              </button>
            </div>
          </div>

          <!-- ITEMS PREVIEW (Confirmation Table) -->
          <div v-if="invoice.items?.length" class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-bold uppercase tracking-wider text-[var(--color-text)]">
                Items Summary ({{ invoice.item_count }} total)
              </h3>
              <span class="text-xs text-[var(--color-text-muted)]">Showing first {{ invoice.items.length }} items</span>
            </div>

            <div class="overflow-x-auto rounded-xl border border-[var(--color-border)]">
              <table class="w-full text-left text-sm">
                <thead>
                  <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                    <th class="py-2.5 px-3">Item Code</th>
                    <th class="py-2.5 px-3">Item Name</th>
                    <th class="py-2.5 px-3 text-right">Qty</th>
                    <th class="py-2.5 px-3 text-right">Rate</th>
                    <th class="py-2.5 px-3 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)] font-mono">
                  <tr v-for="item in invoice.items" :key="item.item_code" class="hover:bg-[var(--color-surface-raised)]/50 transition-colors">
                    <td class="py-2 px-3 text-[var(--color-info)] font-bold">{{ item.item_code }}</td>
                    <td class="py-2 px-3 font-sans text-[var(--color-text)]">{{ item.item_name }}</td>
                    <td class="py-2 px-3 text-right text-[var(--color-text)]">{{ item.qty }} {{ item.uom }}</td>
                    <td class="py-2 px-3 text-right text-[var(--color-text-muted)]">₹{{ fmtCurrency(item.rate) }}</td>
                    <td class="py-2 px-3 text-right font-bold text-[var(--color-text)]">₹{{ fmtCurrency(item.amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { fetchSubmittedInvoice, modifySubmittedBillDate } from '../api'

const router = useRouter()

// State
const invoiceNo = ref('')
const invoiceInputRef = ref(null)
const newDateInputRef = ref(null)

const loadingFetch = ref(false)
const loadingUpdate = ref(false)
const fetchError = ref('')
const updateSuccessMessage = ref('')

const invoice = ref(null)
const newBillDate = ref('')

// Helpers
function pad(n) {
  return String(n).padStart(2, '0')
}

function toLocalISO(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function fmtCurrency(val) {
  return Number(val || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatDateLong(dateStr) {
  if (!dateStr) return '—'
  const [y, m, d] = dateStr.split('-').map(Number)
  const dt = new Date(y, m - 1, d)
  if (isNaN(dt)) return dateStr
  return dt.toLocaleDateString('en-IN', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function formatTime(timeStr) {
  if (!timeStr) return '—'
  const parts = String(timeStr).split(':')
  if (parts.length >= 2) {
    let hours = parseInt(parts[0], 10)
    const minutes = parts[1]
    const ampm = hours >= 12 ? 'PM' : 'AM'
    hours = hours % 12 || 12
    return `${hours}:${minutes} ${ampm}`
  }
  return timeStr
}

// Computed
const isDateChanged = computed(() => {
  if (!invoice.value || !newBillDate.value) return false
  return invoice.value.posting_date !== newBillDate.value
})

const dateDiffLabel = computed(() => {
  if (!invoice.value?.posting_date || !newBillDate.value) return ''
  const [y1, m1, d1] = invoice.value.posting_date.split('-').map(Number)
  const [y2, m2, d2] = newBillDate.value.split('-').map(Number)
  const t1 = new Date(y1, m1 - 1, d1).getTime()
  const t2 = new Date(y2, m2 - 1, d2).getTime()
  const diffDays = Math.round((t2 - t1) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Same Day'
  if (diffDays > 0) return `+${diffDays} day${diffDays > 1 ? 's' : ''}`
  return `${diffDays} day${diffDays < -1 ? 's' : ''}`
})

// Actions
async function handleFetch() {
  const query = invoiceNo.value.trim()
  if (!query) return

  fetchError.value = ''
  updateSuccessMessage.value = ''
  loadingFetch.value = true

  try {
    const res = await fetchSubmittedInvoice(query)
    invoice.value = res
    newBillDate.value = res.posting_date || ''
    await nextTick()
    newDateInputRef.value?.focus()
  } catch (err) {
    invoice.value = null
    fetchError.value = err.message || 'Failed to fetch submitted invoice.'
  } finally {
    loadingFetch.value = false
  }
}

function adjustDate(days) {
  if (!newBillDate.value) return
  const [y, m, d] = newBillDate.value.split('-').map(Number)
  const dt = new Date(y, m - 1, d)
  dt.setDate(dt.getDate() + days)
  newBillDate.value = toLocalISO(dt)
}

function setPreset(preset) {
  const now = new Date()
  if (preset === 'today') {
    newBillDate.value = toLocalISO(now)
  } else if (preset === 'yesterday') {
    now.setDate(now.getDate() - 1)
    newBillDate.value = toLocalISO(now)
  }
}

function resetToOriginal() {
  if (invoice.value?.posting_date) {
    newBillDate.value = invoice.value.posting_date
  }
}

function clearAll() {
  invoiceNo.value = ''
  invoice.value = null
  fetchError.value = ''
  updateSuccessMessage.value = ''
  newBillDate.value = ''
  nextTick(() => {
    invoiceInputRef.value?.focus()
  })
}

async function handleChangeDate() {
  if (!invoice.value || !isDateChanged.value || loadingUpdate.value) return

  loadingUpdate.value = true
  fetchError.value = ''
  updateSuccessMessage.value = ''

  try {
    const res = await modifySubmittedBillDate(
      invoice.value.name,
      newBillDate.value,
      invoice.value.doctype || 'Sales Invoice'
    )

    updateSuccessMessage.value = res.message || `Bill date successfully modified to ${newBillDate.value}.`
    // Update local state to reflect new date
    invoice.value.posting_date = newBillDate.value
  } catch (err) {
    fetchError.value = err.message || 'Failed to update bill date.'
  } finally {
    loadingUpdate.value = false
  }
}

// Global Keyboard shortcuts
function handleKeyDown(e) {
  if (e.key === 'Escape') {
    if (invoice.value) {
      clearAll()
    } else {
      router.push('/')
    }
  } else if (e.key === 'F8') {
    e.preventDefault()
    if (isDateChanged.value && !loadingUpdate.value) {
      handleChangeDate()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  nextTick(() => {
    invoiceInputRef.value?.focus()
  })
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 9999px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}
</style>
