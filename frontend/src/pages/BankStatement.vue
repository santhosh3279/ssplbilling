<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-2.5 shadow-sm">
      <div class="flex items-center gap-3">
        <button
          @click="goBack"
          class="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-normal uppercase tracking-tight">Bank Statement</h1>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <label class="flex items-center gap-2 text-xs font-bold uppercase text-[var(--color-text-muted)]">
          Bank Ledger
          <select
            v-model="bankAccount"
            @change="onBankChange"
            class="min-w-[18rem] rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-[1.05rem] normal-case text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
          >
            <option value="">Select bank ledger…</option>
            <optgroup v-for="g in bankGroups" :key="g.company" :label="g.company">
              <option v-for="a in g.accounts" :key="a.name" :value="a.name">
                {{ a.name }}{{ a.pending ? ` (${a.pending} pending)` : '' }}
              </option>
            </optgroup>
          </select>
        </label>
        <label class="flex items-center gap-1 text-xs font-bold uppercase text-[var(--color-text-muted)]" title="Days a voucher's date may differ from the statement date for an amount match">
          ± Days
          <input
            v-model.number="windowDays"
            type="number"
            min="0"
            max="15"
            @change="saveWindow"
            class="w-16 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1.5 text-center text-[1.05rem] text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
          />
        </label>
        <button
          @click="fileInput?.click()"
          :disabled="!bankAccount"
          class="rounded-lg bg-[var(--color-highlight)] px-4 py-1.5 text-[1.05rem] font-bold uppercase text-[var(--color-text-on-highlight)] disabled:opacity-50"
        >Upload Excel</button>
        <button
          @click="pdfInput?.click()"
          :disabled="!bankAccount || busy"
          class="rounded-lg bg-[var(--color-highlight)] px-4 py-1.5 text-[1.05rem] font-bold uppercase text-[var(--color-text-on-highlight)] disabled:opacity-50"
        >{{ readingPdf ? 'Reading…' : 'Upload PDF' }}</button>
        <button
          @click="runRematch"
          :disabled="!bankAccount || busy"
          title="Match Pending lines again (e.g. after vouchers were booked elsewhere)"
          class="rounded-lg bg-[var(--color-surface-raised)] px-3 py-1.5 text-[1.05rem] font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
        >↻ Re-match</button>
        <input ref="fileInput" type="file" accept=".xlsx,.xls,.csv" class="hidden" @change="onFile" />
        <input ref="pdfInput" type="file" accept=".pdf,application/pdf" class="hidden" @change="onPdf" />
      </div>
      <div class="w-full text-right text-sm text-[var(--color-text-muted)] xl:w-auto">Esc back · ↑↓ line · F2 counter ledger · Ctrl+Enter post</div>
    </header>

    <div v-if="notice" class="flex items-center justify-between gap-4 border-b border-[var(--color-border)] bg-[var(--color-success)]/15 px-6 py-2 text-sm font-bold">
      <span>{{ notice }}</span>
      <button @click="notice = ''" class="opacity-60 hover:opacity-100">✕</button>
    </div>
    <div v-if="error" class="flex items-center justify-between gap-4 border-b border-[var(--color-border)] bg-[var(--color-danger)]/15 px-6 py-2 text-sm font-bold text-[var(--color-danger)]">
      <span class="whitespace-pre-wrap">{{ error }}</span>
      <button @click="error = ''" class="opacity-60 hover:opacity-100">✕</button>
    </div>

    <!-- Column mapping for an uploaded file -->
    <main v-if="upload" class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      <div class="mx-auto flex max-w-6xl flex-col gap-5">
        <section class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Map statement columns · {{ bankAccount }}</div>
              <div class="text-xl font-bold">{{ upload.fileName }}</div>
            </div>
            <div class="flex items-center gap-2">
              <label v-if="upload.sheetNames.length > 1" class="flex items-center gap-2 text-xs font-bold uppercase text-[var(--color-text-muted)]">
                Sheet
                <select
                  v-model="upload.sheet"
                  @change="loadSheet"
                  class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
                >
                  <option v-for="s in upload.sheetNames" :key="s" :value="s">{{ s }}</option>
                </select>
              </label>
              <label class="flex items-center gap-2 text-xs font-bold uppercase text-[var(--color-text-muted)]">
                Header row
                <input
                  v-model.number="upload.headerRow"
                  type="number"
                  min="1"
                  :max="upload.grid.length"
                  @change="applyHeaderRow(false)"
                  class="w-20 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-center text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
                />
              </label>
            </div>
          </div>

          <div class="flex gap-1">
            <button
              v-for="m in amountModes"
              :key="m.id"
              @click="map.mode = m.id"
              class="rounded-md px-3 py-1 text-[0.95rem] font-bold uppercase"
              :class="map.mode === m.id
                ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]'
                : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)]'"
            >{{ m.label }}</button>
          </div>

          <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
            <label
              v-for="f in visibleFields"
              :key="f.id"
              class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]"
            >
              <span class="text-xs font-bold uppercase opacity-75">{{ f.label }}<span v-if="f.required" class="text-[var(--color-danger)]"> *</span></span>
              <select
                v-model.number="map[f.id]"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-[var(--color-text)] outline-none"
              >
                <option :value="-1">— none —</option>
                <option v-for="(h, i) in upload.headers" :key="i" :value="i">{{ h || `Column ${i + 1}` }}</option>
              </select>
            </label>
          </div>
          <div class="text-sm text-[var(--color-text-muted)]">
            Columns not mapped here are kept with the line and written into the voucher remarks.
            Dates are read day-first (dd/mm/yyyy).
          </div>
        </section>

        <section class="flex flex-col gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex flex-wrap gap-4 text-sm">
              <span><b>{{ parsed.valid.length }}</b> lines</span>
              <span>{{ parsed.from }} → {{ parsed.to }}</span>
              <span class="text-[var(--color-success)]">Deposits ₹{{ fmt(parsed.deposits) }}</span>
              <span class="text-[var(--color-danger)]">Withdrawals ₹{{ fmt(parsed.withdrawals) }}</span>
              <span v-if="parsed.skipped" class="text-[var(--color-text-muted)]">{{ parsed.skipped }} rows skipped (no date / no amount)</span>
            </div>
            <div class="flex gap-2">
              <button
                @click="upload = null"
                class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)]"
              >Cancel</button>
              <button
                @click="doImport"
                :disabled="!mapReady || !parsed.valid.length || busy"
                class="rounded-xl bg-[var(--color-success)] px-6 py-2 text-lg font-black uppercase text-white disabled:opacity-50"
              >{{ busy ? 'Importing…' : `Import & Match ${parsed.valid.length}` }}</button>
            </div>
          </div>
          <div v-if="!mapReady" class="text-sm font-bold text-[var(--color-danger)]">Map the date column and the amount column(s).</div>
          <div class="max-h-[50vh] overflow-auto rounded-lg border border-[var(--color-border)] custom-scrollbar">
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-[var(--color-surface)] text-xs uppercase text-[var(--color-text-muted)]">
                <tr>
                  <th class="px-2 py-1.5 text-left">Date</th>
                  <th class="px-2 py-1.5 text-left">Narration</th>
                  <th class="px-2 py-1.5 text-left">Ref</th>
                  <th class="px-2 py-1.5 text-right">Withdrawal</th>
                  <th class="px-2 py-1.5 text-right">Deposit</th>
                  <th class="px-2 py-1.5 text-right">Balance</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, i) in parsed.valid.slice(0, 200)" :key="i" class="border-t border-[var(--color-border)]">
                  <td class="whitespace-nowrap px-2 py-1 font-mono">{{ r.posting_date }}</td>
                  <td class="px-2 py-1">{{ r.description }}</td>
                  <td class="px-2 py-1 font-mono">{{ r.reference_no }}</td>
                  <td class="px-2 py-1 text-right font-mono text-[var(--color-danger)]">{{ r.withdrawal ? fmt(r.withdrawal) : '' }}</td>
                  <td class="px-2 py-1 text-right font-mono text-[var(--color-success)]">{{ r.deposit ? fmt(r.deposit) : '' }}</td>
                  <td class="px-2 py-1 text-right font-mono">{{ r.balance != null ? fmt(r.balance) : '' }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="parsed.valid.length > 200" class="p-2 text-center text-sm text-[var(--color-text-muted)]">… {{ parsed.valid.length - 200 }} more</div>
          </div>
        </section>
      </div>
    </main>

    <div v-else class="flex flex-1 overflow-hidden">
      <!-- LEFT: statement lines of the bank ledger -->
      <aside class="flex w-[480px] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div class="flex gap-1 border-b border-[var(--color-border)] p-2">
          <button
            v-for="s in statusFilters"
            :key="s"
            @click="statusFilter = s"
            class="flex-1 rounded-md px-1 py-1 text-[0.9rem] font-bold uppercase"
            :class="statusFilter === s
              ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]'
              : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)]'"
          >{{ s }} <span class="opacity-70">{{ statusCount(s) }}</span></button>
        </div>
        <div class="flex flex-col gap-2 border-b border-[var(--color-border)] p-3">
          <div class="flex items-center gap-1">
            <input
              type="date"
              v-model="fromDate"
              @change="loadEntries"
              class="min-w-0 flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1.5 text-[1rem] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
            />
            <span class="text-[var(--color-text-muted)]">→</span>
            <input
              type="date"
              v-model="toDate"
              @change="loadEntries"
              class="min-w-0 flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1.5 text-[1rem] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
            />
            <button
              @click="clearDates"
              :disabled="!fromDate && !toDate"
              class="rounded-md bg-[var(--color-surface-raised)] px-2 py-1.5 text-[0.9rem] font-bold uppercase hover:bg-[var(--color-midlight)] disabled:opacity-50"
            >All</button>
          </div>
          <div class="flex items-center gap-1">
            <input
              v-model="search"
              placeholder="Search narration / ref / amount / voucher"
              class="min-w-0 flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-[1.05rem] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
            />
            <button
              @click="loadEntries"
              :disabled="loading || !bankAccount"
              class="shrink-0 rounded-lg bg-[var(--color-surface-raised)] px-3 py-1.5 text-[1.05rem] font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
            >{{ loading ? '…' : '↻' }}</button>
          </div>
          <div v-if="statusFilter === 'Pending' && filteredRows.length" class="flex justify-between text-sm text-[var(--color-text-muted)]">
            <span>In ₹{{ fmt(sum(filteredRows, 'deposit')) }}</span>
            <span>Out ₹{{ fmt(sum(filteredRows, 'withdrawal')) }}</span>
          </div>
        </div>
        <div ref="listEl" class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="!bankAccount" class="p-6 text-center text-[1.05rem] text-[var(--color-text-muted)]">Select a bank ledger</div>
          <div v-else-if="!filteredRows.length" class="p-6 text-center text-[1.05rem] text-[var(--color-text-muted)]">
            {{ loading ? 'Loading…' : rows.length ? 'Nothing here' : 'No statement uploaded for this ledger yet' }}
          </div>
          <div
            v-for="r in filteredRows"
            :key="r.name"
            :data-name="r.name"
            @click="selectRow(r)"
            class="flex cursor-pointer flex-col gap-1 border-b border-[var(--color-border)] px-3 py-2 transition-colors"
            :class="selected?.name === r.name
              ? 'bg-[var(--color-focus)] text-[var(--color-text-on-focus)]'
              : 'hover:bg-[var(--color-midlight)]'"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="shrink-0 font-mono text-[0.95rem] opacity-75">{{ fmtDay(r.posting_date) }}</span>
              <span
                class="shrink-0 font-mono text-[1.2rem] font-bold"
                :class="selected?.name === r.name ? '' : r.deposit ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'"
              >{{ r.deposit ? '+' : '−' }}₹{{ fmt(r.deposit || r.withdrawal) }}</span>
            </div>
            <div class="line-clamp-2 text-[0.95rem]">{{ r.description || '—' }}</div>
            <div class="flex items-center justify-between gap-2 text-[0.85rem]">
              <span class="truncate font-mono opacity-75">{{ r.reference_no || r.name }}</span>
              <span class="flex shrink-0 items-center gap-1">
                <span v-if="r.voucher_no" class="truncate opacity-75">{{ r.voucher_no }}</span>
                <span class="rounded px-1.5 py-0.5 font-bold uppercase text-white" :class="statusClass(r.status)">{{ r.status }}</span>
              </span>
            </div>
          </div>
        </div>
      </aside>

      <!-- RIGHT: the selected line -->
      <main class="flex-1 overflow-y-auto p-6 custom-scrollbar">
        <div v-if="!selected" class="flex h-full items-center justify-center text-center text-[var(--color-text-muted)]">
          <div class="max-w-md">
            <div class="text-lg font-bold uppercase">{{ bankAccount ? 'Select a statement line' : 'Select a bank ledger' }}</div>
            <div class="text-sm">
              Upload the bank's Excel or PDF: lines already in the ledger are matched to their voucher, the rest stay
              Pending until you post them against a counter ledger.
            </div>
          </div>
        </div>
        <div v-else class="mx-auto flex max-w-2xl flex-col gap-6">
          <section class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="text-xs font-bold uppercase text-[var(--color-text-muted)]">{{ selected.deposit ? 'Deposit' : 'Withdrawal' }} · {{ selected.name }}</div>
                <div class="text-xl font-bold">{{ fmtDay(selected.posting_date) }}</div>
                <div class="font-mono text-sm text-[var(--color-text-muted)]">{{ selected.reference_no || 'No reference no' }}</div>
              </div>
              <div class="flex flex-col items-end gap-1">
                <span
                  class="font-mono text-3xl font-black"
                  :class="selected.deposit ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'"
                >{{ selected.deposit ? '+' : '−' }}₹{{ fmt(selected.deposit || selected.withdrawal) }}</span>
                <span class="rounded px-2 py-0.5 text-sm font-bold uppercase text-white" :class="statusClass(selected.status)">{{ selected.status }}</span>
              </div>
            </div>
            <div class="whitespace-pre-wrap rounded-lg bg-[var(--color-surface)] px-3 py-2">{{ selected.description || '—' }}</div>
            <dl class="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
              <template v-if="selected.balance != null">
                <dt class="text-[var(--color-text-muted)]">Balance</dt><dd class="font-mono">₹{{ fmt(selected.balance) }}</dd>
              </template>
              <template v-for="(v, k) in extraOf(selected)" :key="k">
                <dt class="text-[var(--color-text-muted)]">{{ k }}</dt><dd class="break-all">{{ v }}</dd>
              </template>
              <template v-if="selected.voucher_no">
                <dt class="text-[var(--color-text-muted)]">{{ selected.voucher_type }}</dt>
                <dd>
                  <a :href="`/app/${slug(selected.voucher_type)}/${selected.voucher_no}`" target="_blank" class="font-bold text-[var(--color-info)] underline">{{ selected.voucher_no }}</a>
                  <span v-if="selected.match_basis" class="opacity-60"> ({{ selected.match_basis }})</span>
                </dd>
              </template>
              <template v-if="selected.counter_party">
                <dt class="text-[var(--color-text-muted)]">Counter ledger</dt>
                <dd>{{ selected.counter_party }} <span class="opacity-60">({{ selected.counter_party_type }})</span></dd>
              </template>
              <dt class="text-[var(--color-text-muted)]">Imported</dt><dd>{{ selected.import_batch || '—' }}</dd>
            </dl>
            <div class="flex flex-wrap justify-end gap-2">
              <button
                v-if="selected.status === 'Matched'"
                @click="doUnmatch(selected)"
                :disabled="busy"
                class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
              >Wrong match · Unmatch</button>
              <button
                v-if="selected.status === 'Ignored'"
                @click="doIgnore(selected, 0)"
                :disabled="busy"
                class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
              >Back to Pending</button>
              <template v-if="selected.status === 'Pending'">
                <button
                  @click="doDelete(selected)"
                  :disabled="busy"
                  class="rounded-lg bg-[var(--color-danger)] px-4 py-2 font-bold text-white disabled:opacity-50"
                >Delete</button>
                <button
                  @click="doIgnore(selected, 1)"
                  :disabled="busy"
                  title="Nothing to book for this line"
                  class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
                >Ignore</button>
              </template>
            </div>
          </section>

          <!-- Post a voucher for a Pending line -->
          <section
            v-if="selected.status === 'Pending'"
            class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5"
          >
            <h2 class="text-lg font-bold uppercase tracking-wide">Post Entry</h2>
            <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
              <span class="text-xs font-bold uppercase opacity-75">
                Counter Ledger
                <span class="normal-case opacity-75">({{ selected.deposit ? 'who paid us · credit' : 'who we paid · debit' }})</span>
              </span>
              <input
                ref="counterInput"
                :value="form.label"
                readonly
                placeholder="Enter to search customer / supplier / employee / account"
                @keydown.enter.prevent="showSearch = true"
                @click="showSearch = true"
                class="w-full cursor-pointer rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none"
              />
              <span v-if="form.type" class="text-xs opacity-75">{{ form.type }}</span>
            </label>
            <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
              <span class="text-xs font-bold uppercase opacity-75">Remarks <span class="normal-case opacity-75">(optional, added after the statement details)</span></span>
              <input
                ref="remarksInput"
                v-model="form.remarks"
                maxlength="140"
                @keydown.enter.prevent="postSelected"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none"
              />
            </label>
            <div class="text-sm text-[var(--color-text-muted)]">
              <template v-if="form.type">Creates <b class="text-[var(--color-text)]">{{ voucherPreview }}</b> · </template>
              posted on {{ fmtDay(selected.posting_date) }} in {{ selected.company }}
              · ref {{ selected.reference_no || selected.name }}
            </div>
            <div class="flex justify-end">
              <button
                @click="postSelected"
                :disabled="posting || !form.counter"
                class="rounded-xl bg-[var(--color-success)] px-6 py-2.5 text-lg font-black uppercase text-white shadow-sm transition-opacity disabled:opacity-50"
              >{{ posting ? 'Posting…' : 'Post' }}</button>
            </div>
          </section>
        </div>
      </main>
    </div>

    <CustomerSearchModal
      :show="showSearch"
      title="Counter Ledger"
      :subtitle="selected?.deposit ? 'Who paid this deposit (credit)' : 'Who this withdrawal was paid to (debit)'"
      :allowedTypes="['Customer', 'Supplier', 'Employee', 'Account']"
      initialType="All"
      :skipDateFilter="true"
      :hideSecondary="true"
      @close="showSearch = false"
      @select="onSelect"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as XLSX from 'xlsx'
import { frappeGet, frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'

const router = useRouter()
const API = 'ssplbilling.api.bank_statement_api'
const LS_ACCOUNT = 'wb-bankstmt-account'
const LS_WINDOW = 'wb-bankstmt-window'
const LS_MAP = 'wb-bankstmt-map:'

const lsGet = (k) => { try { return localStorage.getItem(k) } catch { return null } }
const lsSet = (k, v) => { try { localStorage.setItem(k, v) } catch { /* private window */ } }

const accounts = ref([])
const bankAccount = ref('')
const windowDays = ref(Number(lsGet(LS_WINDOW) ?? 3))
const rows = ref([])
const loading = ref(false)
const busy = ref(false)
const posting = ref(false)
const error = ref('')
const notice = ref('')
const search = ref('')
const fromDate = ref('')
const toDate = ref('')
const statusFilters = ['Pending', 'Matched', 'Posted', 'Ignored', 'All']
const statusFilter = ref('Pending')
const selected = ref(null)
const form = reactive({ type: '', counter: '', label: '', remarks: '' })
const showSearch = ref(false)
const fileInput = ref(null)
const pdfInput = ref(null)
const readingPdf = ref(false)
const counterInput = ref(null)
const remarksInput = ref(null)
const listEl = ref(null)

const fmt = (v) => Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fmtDay = (v) => {
  const [y, m, d] = String(v || '').slice(0, 10).split('-')
  return d ? `${d}-${m}-${y}` : '—'
}
const slug = (doctype) => (doctype || '').toLowerCase().replace(/ /g, '-')
const sum = (list, key) => list.reduce((t, r) => t + Number(r[key] || 0), 0)
const statusClass = (s) => ({
  Pending: 'bg-[var(--color-warning)]',
  Matched: 'bg-[var(--color-info)]',
  Posted: 'bg-[var(--color-success)]',
  Ignored: 'bg-[var(--color-text-muted)]',
}[s] || 'bg-[var(--color-text-muted)]')

const bankGroups = computed(() => {
  const groups = {}
  for (const a of accounts.value) (groups[a.company] ||= []).push(a)
  return Object.entries(groups).map(([company, list]) => ({ company, accounts: list }))
})

const filteredRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (statusFilter.value !== 'All' && r.status !== statusFilter.value) return false
    if (!q) return true
    return [r.name, r.description, r.reference_no, r.voucher_no, r.counter_party, r.row_data, String(r.deposit || r.withdrawal)]
      .some((v) => (v || '').toLowerCase().includes(q))
  })
})
const statusCount = (s) => (s === 'All' ? rows.value.length : rows.value.filter((r) => r.status === s).length)

function extraOf(r) {
  try { return r.row_data ? JSON.parse(r.row_data) : {} } catch { return {} }
}

const voucherPreview = computed(() => {
  if (!selected.value || !form.type) return ''
  if (form.type === 'Account') return 'Journal Entry'
  return `Payment Entry (${selected.value.deposit ? 'Receive from' : 'Pay to'} ${form.type})`
})

async function loadAccounts() {
  try {
    accounts.value = (await frappeGet(`${API}.get_bank_accounts`)) || []
  } catch (e) {
    error.value = e.message
  }
}

async function loadEntries() {
  if (!bankAccount.value) { rows.value = []; return }
  loading.value = true
  try {
    const params = { bank_account: bankAccount.value }
    if (fromDate.value && toDate.value) Object.assign(params, { from_date: fromDate.value, to_date: toDate.value })
    rows.value = ((await frappeGet(`${API}.get_entries`, params)) || []).reverse()
    if (selected.value) selected.value = rows.value.find((r) => r.name === selected.value.name) || null
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function onBankChange() {
  lsSet(LS_ACCOUNT, bankAccount.value)
  selected.value = null
  error.value = ''
  loadEntries()
}
function saveWindow() {
  windowDays.value = Math.max(0, Math.min(15, Number(windowDays.value) || 0))
  lsSet(LS_WINDOW, String(windowDays.value))
}
function clearDates() {
  fromDate.value = ''
  toDate.value = ''
  loadEntries()
}

function resetForm() {
  Object.assign(form, { type: '', counter: '', label: '', remarks: '' })
}
function selectRow(r) {
  if (selected.value?.name === r.name) return
  error.value = ''
  selected.value = r
  resetForm()
}
function moveSelection(step) {
  const list = filteredRows.value
  if (!list.length) return
  const i = list.findIndex((r) => r.name === selected.value?.name)
  const next = list[Math.max(0, Math.min(list.length - 1, i < 0 ? 0 : i + step))]
  selectRow(next)
  nextTick(() => listEl.value?.querySelector(`[data-name="${next.name}"]`)?.scrollIntoView({ block: 'nearest' }))
}

function onSelect(item) {
  showSearch.value = false
  form.counter = item.name
  form.type = item.type && item.type !== 'Account' ? item.type : 'Account'
  form.label = item.label || item.customer_name || item.supplier_name || item.employee_name || item.account_name || item.name
  nextTick(() => remarksInput.value?.focus())
}

async function postSelected() {
  const r = selected.value
  if (!r || r.status !== 'Pending' || posting.value) return
  error.value = ''
  if (!form.counter) { error.value = 'Select the counter ledger'; return counterInput.value?.focus() }
  posting.value = true
  try {
    const res = await frappePost(`${API}.post_entry`, {
      name: r.name,
      counter_type: form.type,
      counter: form.counter,
      remarks: form.remarks,
      cost_center: lsGet('wb-cost-center') || null,
    }, { silent: true })
    const list = filteredRows.value
    const nextPending = list.slice(list.findIndex((x) => x.name === r.name) + 1).find((x) => x.status === 'Pending')
    Object.assign(r, res)
    notice.value = `${r.name} posted as ${res.voucher_type} ${res.voucher_no}`
    bumpPending(-1)
    // One by one: straight on to the next Pending line
    if (nextPending) {
      selectRow(nextPending)
      nextTick(() => counterInput.value?.focus())
    }
  } catch (e) {
    error.value = e.message
    loadEntries()
  } finally {
    posting.value = false
  }
}

function bumpPending(by) {
  const a = accounts.value.find((x) => x.name === bankAccount.value)
  if (a) a.pending = Math.max(0, (a.pending || 0) + by)
}

async function changeStatus(method, params, r, pendingDelta) {
  busy.value = true
  error.value = ''
  try {
    const res = await frappePost(`${API}.${method}`, params, { silent: true })
    Object.assign(r, res)
    bumpPending(pendingDelta)
  } catch (e) {
    error.value = e.message
    loadEntries()
  } finally {
    busy.value = false
  }
}
const doIgnore = (r, ignored) => changeStatus('set_ignored', { name: r.name, ignored }, r, ignored ? -1 : 1)
const doUnmatch = (r) => changeStatus('unmatch', { name: r.name }, r, 1)

async function doDelete(r) {
  if (!confirm(`Delete statement line ${r.name} (₹${fmt(r.deposit || r.withdrawal)})?\n\nUploading the statement again brings it back.`)) return
  busy.value = true
  error.value = ''
  try {
    await frappePost(`${API}.delete_entries`, { names: [r.name] }, { silent: true })
    rows.value = rows.value.filter((x) => x.name !== r.name)
    if (selected.value?.name === r.name) selected.value = null
    bumpPending(-1)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function runRematch() {
  busy.value = true
  error.value = ''
  try {
    const params = { bank_account: bankAccount.value, window: windowDays.value }
    if (fromDate.value && toDate.value) Object.assign(params, { from_date: fromDate.value, to_date: toDate.value })
    const res = await frappePost(`${API}.rematch`, params, { silent: true })
    notice.value = `Re-match: ${res.matched} matched, ${res.reopened} reopened (voucher cancelled), ${res.pending ?? 0} still pending`
    await Promise.all([loadEntries(), loadAccounts()])
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

// ── Excel upload & column mapping ──────────────────────────────────────────

const FIELDS = [
  { id: 'date', label: 'Date', required: true },
  { id: 'description', label: 'Narration' },
  { id: 'reference', label: 'Ref / Cheque No' },
  { id: 'withdrawal', label: 'Withdrawal (Dr)', mode: 'split' },
  { id: 'deposit', label: 'Deposit (Cr)', mode: 'split' },
  { id: 'amount', label: 'Amount', mode: 'single' },
  { id: 'drcr', label: 'Dr / Cr', mode: 'single' },
  { id: 'balance', label: 'Balance' },
]
const amountModes = [
  { id: 'split', label: 'Withdrawal & Deposit columns' },
  { id: 'single', label: 'Amount + Dr/Cr column' },
]
// Header text patterns, most specific first; a column is claimed by the first field that takes it
const GUESS = [
  ['drcr', /^(dr\s*\/\s*cr|cr\s*\/\s*dr|debit\s*\/\s*credit|txn type|type|cr\/dr)$/i],
  ['date', /^(txn|tran|transaction|posting|post)\.?\s*date$/i],
  ['date', /^date$/i],
  ['date', /date/i],
  ['withdrawal', /withdraw|debit|^dr\.?$|dr\.? amount|paid out/i],
  ['deposit', /deposit|credit|^cr\.?$|cr\.? amount|paid in/i],
  ['balance', /balance/i],
  ['reference', /chq|cheque|ref|utr|instrument/i],
  ['description', /narration|description|particular|remark|details/i],
  ['amount', /amount/i],
]
const MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, sept: 9, oct: 10, nov: 11, dec: 12 }

const upload = ref(null)
const map = reactive({ mode: 'split', date: -1, description: -1, reference: -1, withdrawal: -1, deposit: -1, amount: -1, drcr: -1, balance: -1 })
const visibleFields = computed(() => FIELDS.filter((f) => !f.mode || f.mode === map.mode))
const mapReady = computed(() =>
  map.date >= 0 && (map.mode === 'split' ? map.withdrawal >= 0 || map.deposit >= 0 : map.amount >= 0))

const pad = (n) => String(n).padStart(2, '0')
function isoDate(y, m, d) {
  if (y < 100) y += 2000
  if (m < 1 || m > 12 || d < 1 || d > 31 || y < 1990 || y > 2100) return null
  const dt = new Date(y, m - 1, d)
  return dt.getMonth() === m - 1 ? `${y}-${pad(m)}-${pad(d)}` : null
}
// Indian statements are day-first; Excel stores real dates as serial numbers
function parseDate(v) {
  if (v == null || v === '') return null
  if (typeof v === 'number') {
    if (v < 20000 || v > 80000) return null
    const d = XLSX.SSF.parse_date_code(v)
    return d ? isoDate(d.y, d.m, d.d) : null
  }
  if (v instanceof Date) return isoDate(v.getFullYear(), v.getMonth() + 1, v.getDate())
  const s = String(v).trim()
  let m = s.match(/^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})/)
  if (m) return isoDate(+m[1], +m[2], +m[3])
  m = s.match(/^(\d{1,2})[-/. ](\d{1,2})[-/. ](\d{2}|\d{4})(?!\d)/)
  if (m) return isoDate(+m[3], +m[2], +m[1])
  m = s.match(/^(\d{1,2})[-/. ]([A-Za-z]{3,9})[-/., ]+(\d{2}|\d{4})(?!\d)/)
  if (m) {
    const mon = MONTHS[m[2].toLowerCase().slice(0, 4)] || MONTHS[m[2].toLowerCase().slice(0, 3)]
    if (mon) return isoDate(+m[3], mon, +m[1])
  }
  return null
}
// "1,23,456.00 Cr", "(500.00)", "-500", "₹ 1,000" → signed number
function parseAmount(v) {
  if (typeof v === 'number') return v
  const s = String(v ?? '').trim()
  if (!s) return 0
  const neg = /^\(.*\)$/.test(s) || /^-/.test(s) || /\bdr\.?$/i.test(s)
  const n = parseFloat(s.replace(/[^0-9.]/g, ''))
  return isNaN(n) ? 0 : neg ? -n : n
}
const cellText = (v) => (v == null ? '' : String(v).replace(/\s+/g, ' ').trim())
const round2 = (n) => Math.round(n * 100) / 100

const parsed = computed(() => {
  const out = { valid: [], skipped: 0, deposits: 0, withdrawals: 0, from: '', to: '' }
  const u = upload.value
  if (!u || !mapReady.value) return out
  const mapped = new Set(FIELDS.filter((f) => !f.mode || f.mode === map.mode).map((f) => map[f.id]).filter((i) => i >= 0))
  const textCols = new Set([map.description, map.reference].filter((i) => i >= 0))
  const headerKey = u.headers.join('|')
  for (const line of u.grid.slice(u.headerRow)) {
    if (!line.some((c) => cellText(c))) continue
    // PDF narration wraps onto rows of its own: text only in narration / ref joins the line above
    const prev = out.valid[out.valid.length - 1]
    if (u.pdf && prev && line.map(cellText).join('|') !== headerKey
      && line.every((c, i) => !cellText(c) || textCols.has(i))) {
      if (map.description >= 0 && cellText(line[map.description])) prev.description = `${prev.description} ${cellText(line[map.description])}`.trim()
      if (map.reference >= 0 && cellText(line[map.reference])) prev.reference_no = `${prev.reference_no}${cellText(line[map.reference])}`
      continue
    }
    const date = parseDate(line[map.date])
    let withdrawal = 0
    let deposit = 0
    if (map.mode === 'split') {
      withdrawal = map.withdrawal >= 0 ? Math.abs(parseAmount(line[map.withdrawal])) : 0
      deposit = map.deposit >= 0 ? Math.abs(parseAmount(line[map.deposit])) : 0
    } else {
      const amt = parseAmount(line[map.amount])
      const side = map.drcr >= 0 ? cellText(line[map.drcr]).toLowerCase() : ''
      const isOut = side ? /^(d|w)/.test(side) : amt < 0
      if (isOut) withdrawal = Math.abs(amt)
      else deposit = Math.abs(amt)
    }
    withdrawal = round2(withdrawal)
    deposit = round2(deposit)
    if (!date || !withdrawal === !deposit) { out.skipped++; continue }
    const extra = {}
    u.headers.forEach((h, i) => {
      if (mapped.has(i) || !h) return
      const raw = line[i]
      const val = /date/i.test(h) && typeof raw === 'number' ? parseDate(raw) || raw : cellText(raw)
      if (val !== '' && val != null) extra[h] = String(val)
    })
    const balRaw = map.balance >= 0 ? line[map.balance] : ''
    out.valid.push({
      posting_date: date,
      description: map.description >= 0 ? cellText(line[map.description]) : '',
      reference_no: map.reference >= 0 ? cellText(line[map.reference]) : '',
      withdrawal,
      deposit,
      balance: cellText(balRaw) ? round2(parseAmount(balRaw)) : null,
      extra,
    })
    out.withdrawals += withdrawal
    out.deposits += deposit
  }
  const dates = out.valid.map((r) => r.posting_date).sort()
  out.from = dates.length ? fmtDay(dates[0]) : '—'
  out.to = dates.length ? fmtDay(dates[dates.length - 1]) : '—'
  return out
})

async function onFile(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  error.value = ''
  try {
    const wb = XLSX.read(await file.arrayBuffer(), { type: 'array', raw: true })
    upload.value = { fileName: file.name, wb, sheetNames: wb.SheetNames, sheet: wb.SheetNames[0], grid: [], headers: [], headerRow: 1 }
    loadSheet()
  } catch (err) {
    error.value = `Could not read ${file.name}: ${err.message}`
  }
}

// A PDF's tables are read on the server (pdfplumber); its grid of cell text then maps like a sheet
async function onPdf(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  error.value = ''
  readingPdf.value = true
  try {
    const content = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = () => reject(reader.error)
      reader.readAsDataURL(file)
    })
    let password = ''
    let grid = null
    while (!grid) {
      try {
        grid = await frappePost(`${API}.read_pdf`, { content, password }, { silent: true })
      } catch (err) {
        // Bank PDFs are often locked (DOB / customer id): ask until right or cancelled
        if (!/PDF password/i.test(err.message)) throw err
        password = prompt(`${/wrong/i.test(err.message) ? 'Wrong password. ' : ''}Password for ${file.name}:`, '')
        if (password == null) return
      }
    }
    upload.value = { fileName: file.name, pdf: true, wb: null, sheetNames: [], sheet: '', grid: [], headers: [], headerRow: 1 }
    setGrid(grid)
  } catch (err) {
    error.value = `Could not read ${file.name}: ${err.message.split('\n').pop()}`
  } finally {
    readingPdf.value = false
  }
}

function loadSheet() {
  const u = upload.value
  setGrid(XLSX.utils.sheet_to_json(u.wb.Sheets[u.sheet], { header: 1, raw: true, defval: '' }))
}

function setGrid(grid) {
  const u = upload.value
  u.grid = grid
  u.headerRow = detectHeaderRow(u.grid)
  applyHeaderRow(true)
}

// The header is the row (of the first 40) whose cells look most like column titles
function detectHeaderRow(grid) {
  let best = 0
  let bestScore = 0
  grid.slice(0, 40).forEach((line, i) => {
    const cells = line.map(cellText)
    const score = cells.filter((c) => c && c.length < 40 && GUESS.some(([, re]) => re.test(c))).length
    if (cells.some((c) => /date/i.test(c)) && score > bestScore) {
      best = i
      bestScore = score
    }
  })
  return best + 1
}

function applyHeaderRow(useSaved) {
  const u = upload.value
  u.headerRow = Math.max(1, Math.min(u.grid.length || 1, Number(u.headerRow) || 1))
  u.headers = (u.grid[u.headerRow - 1] || []).map(cellText)
  for (const f of FIELDS) map[f.id] = -1
  // A layout saved for this bank ledger wins when its column titles are all still there
  let saved = null
  if (useSaved) {
    try { saved = JSON.parse(lsGet(LS_MAP + bankAccount.value) || 'null') } catch { saved = null }
  }
  if (saved && Object.entries(saved.cols || {}).every(([, h]) => u.headers.includes(h))) {
    map.mode = saved.mode || 'split'
    for (const [id, h] of Object.entries(saved.cols)) map[id] = u.headers.indexOf(h)
    return
  }
  const taken = new Set()
  for (const [id, re] of GUESS) {
    if (map[id] >= 0) continue
    const i = u.headers.findIndex((h, idx) => h && !taken.has(idx) && re.test(h))
    if (i >= 0) { map[id] = i; taken.add(i) }
  }
  map.mode = map.withdrawal >= 0 || map.deposit >= 0 ? 'split' : 'single'
}

function saveMapping() {
  const cols = {}
  for (const f of visibleFields.value) if (map[f.id] >= 0) cols[f.id] = upload.value.headers[map[f.id]]
  lsSet(LS_MAP + bankAccount.value, JSON.stringify({ mode: map.mode, cols }))
}

async function doImport() {
  if (!mapReady.value || busy.value) return
  busy.value = true
  error.value = ''
  try {
    saveMapping()
    const res = await frappePost(`${API}.import_statement`, {
      bank_account: bankAccount.value,
      rows: parsed.value.valid,
      file_name: upload.value.fileName,
      window: windowDays.value,
    }, { silent: true })
    notice.value =
      `${res.inserted} new lines (${res.duplicates} already imported, ${res.skipped} skipped) · ` +
      `${res.matched ?? 0} matched to the ledger · ${res.pending ?? 0} pending`
    upload.value = null
    statusFilter.value = 'Pending'
    fromDate.value = res.from_date || ''
    toDate.value = res.to_date || ''
    await Promise.all([loadEntries(), loadAccounts()])
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

function goBack() {
  if (upload.value) upload.value = null
  else router.push('/')
}

function onKeydown(e) {
  if (showSearch.value) return
  const typing = ['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName) && document.activeElement !== counterInput.value
  if (e.key === 'Escape') { e.preventDefault(); goBack() }
  else if (upload.value) return
  else if (e.key === 'F2' && selected.value?.status === 'Pending') { e.preventDefault(); showSearch.value = true }
  else if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); postSelected() }
  else if (!typing && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
    e.preventDefault()
    moveSelection(e.key === 'ArrowDown' ? 1 : -1)
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  await loadAccounts()
  const last = lsGet(LS_ACCOUNT)
  if (last && accounts.value.some((a) => a.name === last)) {
    bankAccount.value = last
    loadEntries()
  }
})
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>
