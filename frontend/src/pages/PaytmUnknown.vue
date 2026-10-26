<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-amber-500/30 px-6 py-2.5 shadow-sm">
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/')"
          class="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-normal uppercase tracking-tight">Paytm Unknown Payments</h1>
      </div>
      <div class="text-sm text-[var(--color-text-muted)]">Esc back · F2 from ledger · F3 to ledger · Ctrl+Enter create receipt</div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- LEFT: payments Paytm reported for orders the system did not create -->
      <aside class="flex w-[456px] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div class="flex gap-1 border-b border-[var(--color-border)] p-2">
          <button
            v-for="v in views"
            :key="v.id"
            @click="setView(v.id)"
            class="flex-1 rounded-md px-2 py-1 text-[0.95rem] font-bold uppercase"
            :class="view === v.id
              ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]'
              : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)]'"
          >{{ v.label }}</button>
        </div>

        <template v-if="view === 'log'">
          <div class="flex flex-col gap-2 border-b border-[var(--color-border)] p-3">
            <div class="flex items-center justify-between">
              <span class="text-[1.05rem] font-bold uppercase tracking-wide text-[var(--color-text-muted)]">Every webhook hit</span>
              <button
                @click="loadLogs"
                class="rounded-md px-2 py-0.5 text-[1.05rem] hover:bg-[var(--color-midlight)]"
                :disabled="logsLoading"
              >{{ logsLoading ? 'Loading…' : '↻ Refresh' }}</button>
            </div>
            <input
              v-model="logSearch"
              placeholder="Search order / ref / txn id / result / amount"
              class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-[1.05rem] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
            />
            <div class="flex flex-wrap gap-1">
              <button
                v-for="f in linkFilters"
                :key="f.id"
                @click="linkFilter = f.id"
                class="rounded-md px-2 py-0.5 text-[0.9rem] font-bold uppercase"
                :class="linkFilter === f.id
                  ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]'
                  : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)]'"
              >{{ f.label }} <span class="opacity-70">{{ linkCount(f.id) }}</span></button>
            </div>
          </div>

          <div class="flex-1 overflow-y-auto custom-scrollbar">
            <div v-if="!filteredLogs.length" class="p-6 text-center text-[1.05rem] text-[var(--color-text-muted)]">
              {{ logsLoading ? 'Loading…' : 'No webhook hits yet' }}
            </div>
            <div
              v-for="l in filteredLogs"
              :key="l.name"
              @click="selectLog(l)"
              class="flex cursor-pointer flex-col gap-1 border-b border-[var(--color-border)] px-3 py-2 transition-colors"
              :class="selectedLog?.name === l.name
                ? 'bg-[var(--color-focus)] text-[var(--color-text-on-focus)]'
                : 'hover:bg-[var(--color-midlight)]'"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="flex min-w-0 items-center gap-1.5">
                  <span v-if="l.pay_method" class="shrink-0 rounded border border-current px-1 text-[12px] font-bold uppercase opacity-75">{{ l.pay_method }}</span>
                  <span class="truncate font-mono text-[1.05rem]">{{ l.rrn || l.paytm_txn_id || l.order_id || '—' }}</span>
                </span>
                <span class="shrink-0 font-mono text-[1.2rem] font-bold">₹{{ fmt(l.amount) }}</span>
              </div>
              <div class="flex items-center justify-between gap-2 text-[0.9rem]">
                <span class="truncate opacity-75">{{ fmtDate(l.received_at) }} · {{ l.ref_name || l.order_id || l.name }}</span>
                <span class="flex shrink-0 gap-1">
                  <span
                    v-if="l.linked != null"
                    class="rounded px-1.5 py-0.5 font-bold uppercase text-white"
                    :class="l.linked ? 'bg-[var(--color-success)]' : 'bg-[var(--color-warning)]'"
                  >{{ l.linked ? '✓ Booked' : 'To book' }}</span>
                  <span class="rounded px-1.5 py-0.5 font-bold uppercase text-white" :class="resultClass(l.result)">{{ l.result }}</span>
                </span>
              </div>
              <div v-if="l.linked_to" class="truncate text-[0.9rem] opacity-75">{{ l.linked_doctype }} {{ l.linked_to }}</div>
            </div>
          </div>
        </template>

        <template v-else>
        <div class="flex flex-col gap-2 border-b border-[var(--color-border)] p-3">
          <div class="flex items-center justify-between">
            <span class="text-[1.05rem] font-bold uppercase tracking-wide text-[var(--color-text-muted)]">Unknown Payments</span>
            <button
              @click="loadRows"
              class="rounded-md px-2 py-0.5 text-[1.05rem] hover:bg-[var(--color-midlight)]"
              :disabled="loading"
            >{{ loading ? 'Loading…' : '↻ Refresh' }}</button>
          </div>
          <input
            v-model="search"
            placeholder="Search ref / txn id / amount"
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-[1.05rem] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
          />
          <div class="flex flex-wrap gap-1">
            <button
              v-for="s in statusFilters"
              :key="s"
              @click="statusFilter = s"
              class="rounded-md px-2 py-0.5 text-[0.9rem] font-bold uppercase"
              :class="statusFilter === s
                ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]'
                : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)]'"
            >{{ s }} <span class="opacity-70">{{ statusCount(s) }}</span></button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="!filteredRows.length" class="p-6 text-center text-[1.05rem] text-[var(--color-text-muted)]">
            {{ loading ? 'Loading…' : 'No unknown payments' }}
          </div>
          <div
            v-for="r in filteredRows"
            :key="r.name"
            @click="selectRow(r)"
            class="flex cursor-pointer flex-col gap-1 border-b border-[var(--color-border)] px-3 py-2 transition-colors"
            :class="selected?.name === r.name
              ? 'bg-[var(--color-focus)] text-[var(--color-text-on-focus)]'
              : 'hover:bg-[var(--color-midlight)]'"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="flex min-w-0 items-center gap-1.5">
                <span class="shrink-0 rounded border border-current px-1 text-[12px] font-bold uppercase opacity-75">{{ r.pay_method || 'Paytm' }}</span>
                <span class="truncate font-mono text-[1.05rem]">{{ r.rrn || r.paytm_txn_id }}</span>
              </span>
              <span class="shrink-0 font-mono text-[1.2rem] font-bold">₹{{ fmt(r.amount) }}</span>
            </div>
            <div class="flex items-center justify-between gap-2 text-[0.9rem]">
              <span class="truncate opacity-75">{{ fmtDate(r.received_at) }} · {{ r.name }}</span>
              <span
                class="shrink-0 rounded px-1.5 py-0.5 font-bold uppercase"
                :class="r.verified ? 'bg-[var(--color-success)] text-white' : 'bg-[var(--color-danger)] text-white'"
              >{{ r.verified ? 'Verified' : 'Unverified' }}</span>
            </div>
            <div v-if="r.status === 'Receipted'" class="text-[0.9rem] opacity-75">Receipt {{ r.payment_entry }} · {{ r.party }}</div>
            <div v-else class="flex justify-end gap-2 pt-0.5">
              <button
                @click.stop="removeRow(r)"
                :disabled="busy"
                class="rounded-md bg-[var(--color-danger)] px-3 py-1 text-[0.9rem] font-bold uppercase text-white disabled:opacity-50"
              >Delete</button>
              <button
                @click.stop="openReceipt(r)"
                class="rounded-md bg-[var(--color-success)] px-3 py-1 text-[0.9rem] font-bold uppercase text-white"
              >Create Receipt</button>
            </div>
          </div>
        </div>
        </template>
      </aside>

      <!-- RIGHT: receipt for the selected payment -->
      <main class="flex-1 overflow-y-auto p-6 custom-scrollbar">
        <template v-if="view === 'log'">
          <div v-if="!selectedLog" class="flex h-full items-center justify-center text-center text-[var(--color-text-muted)]">
            <div>
              <div class="text-lg font-bold uppercase">Select a webhook hit</div>
              <div class="text-sm">Every notification Paytm sent to the webhook, whether it matched a system order or not.</div>
            </div>
          </div>

          <div v-else class="mx-auto flex max-w-2xl flex-col gap-6">
            <section class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
              <div class="flex items-start justify-between gap-4">
                <div class="min-w-0">
                  <div class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Webhook · {{ selectedLog.name }}</div>
                  <div class="truncate font-mono text-xl font-bold">{{ selectedLog.rrn || selectedLog.paytm_txn_id || selectedLog.order_id || '—' }}</div>
                  <div class="text-sm text-[var(--color-text-muted)]">Received {{ fmtDate(selectedLog.received_at) }}</div>
                </div>
                <div class="flex flex-col items-end gap-1">
                  <span class="font-mono text-3xl font-black">₹{{ fmt(selectedLog.amount) }}</span>
                  <span class="rounded px-2 py-0.5 text-sm font-bold uppercase text-white" :class="resultClass(selectedLog.result)">{{ selectedLog.result }}</span>
                </div>
              </div>

              <dl class="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
                <dt class="text-[var(--color-text-muted)]">What happened</dt><dd>{{ resultText(selectedLog.result) }}</dd>
                <dt class="text-[var(--color-text-muted)]">Paytm status</dt><dd>{{ selectedLog.paytm_status || '—' }}</dd>
                <dt class="text-[var(--color-text-muted)]">Order id</dt><dd class="font-mono break-all">{{ selectedLog.order_id || '—' }}</dd>
                <dt class="text-[var(--color-text-muted)]">Bank ref (RRN)</dt><dd class="font-mono">{{ selectedLog.rrn || '—' }}</dd>
                <dt class="text-[var(--color-text-muted)]">Paytm txn id</dt><dd class="font-mono break-all">{{ selectedLog.paytm_txn_id || '—' }}</dd>
                <template v-if="selectedLog.tid">
                  <dt class="text-[var(--color-text-muted)]">Machine TID</dt><dd class="font-mono">{{ selectedLog.tid }}</dd>
                </template>
                <dt class="text-[var(--color-text-muted)]">Linked record</dt>
                <dd>
                  <a
                    v-if="selectedLog.ref_name"
                    :href="`/app/${slug(selectedLog.ref_doctype)}/${selectedLog.ref_name}`"
                    target="_blank"
                    class="font-bold text-[var(--color-info)] underline"
                  >{{ selectedLog.ref_name }}</a>
                  <span v-else>—</span>
                  <span v-if="selectedLog.ref_doctype" class="opacity-60"> ({{ selectedLog.ref_doctype }})</span>
                </dd>
                <dt class="text-[var(--color-text-muted)]">Booked in</dt>
                <dd :class="selectedLog.linked === 0 ? 'font-bold text-[var(--color-warning)]' : ''">
                  <a
                    v-if="selectedLog.linked_to"
                    :href="`/app/${slug(selectedLog.linked_doctype)}/${selectedLog.linked_to}`"
                    target="_blank"
                    class="font-bold text-[var(--color-info)] underline"
                  >{{ selectedLog.linked_to }}</a>
                  <span v-if="selectedLog.linked_doctype" class="opacity-60"> ({{ selectedLog.linked_doctype }})</span>
                  <span v-if="selectedLog.linked === 1"> ✓ booked</span>
                  <span v-else-if="selectedLog.linked === 0">{{ selectedLog.linked_to ? ' not submitted yet' : 'Not booked yet' }}</span>
                  <span v-else>No payment to book</span>
                </dd>
              </dl>

              <div class="flex flex-wrap justify-end gap-2">
                <button
                  v-if="selectedLog.ref_doctype === 'SSPL Paytm Unknown Payment' && selectedLog.ref_name"
                  @click="openUnknown(selectedLog.ref_name)"
                  class="rounded-lg bg-[var(--color-success)] px-4 py-2 font-bold text-white"
                >Open unknown payment</button>
                <button
                  @click="toggleLogPayload"
                  class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)]"
                >{{ showLogPayload ? 'Hide' : 'Show' }} Paytm payload</button>
              </div>
              <pre
                v-if="showLogPayload"
                class="max-h-96 overflow-auto rounded-lg bg-[var(--color-surface)] p-3 font-mono text-xs custom-scrollbar"
              >{{ logPayloadText }}</pre>
            </section>

            <div v-if="error" class="rounded-lg bg-[var(--color-danger)]/15 px-3 py-2 text-sm font-bold text-[var(--color-danger)]">{{ error }}</div>
          </div>
        </template>

        <template v-else>
        <div v-if="!selected" class="flex h-full items-center justify-center text-center text-[var(--color-text-muted)]">
          <div>
            <div class="text-lg font-bold uppercase">Select a payment</div>
            <div class="text-sm">Paytm payments that were not started from this system (static QR, soundbox, dashboard links) land here.</div>
          </div>
        </div>

        <div v-else class="mx-auto flex max-w-2xl flex-col gap-6">
          <!-- Payment -->
          <section class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Paytm {{ selected.pay_method || 'payment' }} · {{ selected.name }}</div>
                <div class="truncate font-mono text-xl font-bold">{{ selected.rrn || selected.paytm_txn_id }}</div>
                <div class="text-sm text-[var(--color-text-muted)]">Received {{ fmtDate(selected.received_at) }}</div>
              </div>
              <div class="flex flex-col items-end gap-1">
                <span class="font-mono text-3xl font-black">₹{{ fmt(selected.amount) }}</span>
                <span
                  class="rounded px-2 py-0.5 text-sm font-bold uppercase"
                  :class="selected.status === 'Receipted' ? 'bg-[var(--color-success)] text-white' : 'bg-[var(--color-warning)] text-white'"
                >{{ selected.status }}</span>
              </div>
            </div>

            <dl class="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
              <dt class="text-[var(--color-text-muted)]">Bank ref (RRN)</dt><dd class="font-mono">{{ selected.rrn || '—' }}</dd>
              <dt class="text-[var(--color-text-muted)]">Paytm txn id</dt><dd class="font-mono break-all">{{ selected.paytm_txn_id || '—' }}</dd>
              <dt class="text-[var(--color-text-muted)]">Paytm order id</dt><dd class="font-mono break-all">{{ selected.paytm_order_id || '—' }}</dd>
              <dt class="text-[var(--color-text-muted)]">Paytm txn date</dt><dd>{{ selected.txn_date || '—' }}</dd>
              <template v-if="selected.tid">
                <dt class="text-[var(--color-text-muted)]">Machine TID</dt><dd class="font-mono">{{ selected.tid }}</dd>
              </template>
              <dt class="text-[var(--color-text-muted)]">Verification</dt>
              <dd :class="selected.verified ? 'text-[var(--color-success)]' : 'font-bold text-[var(--color-danger)]'">{{ selected.verification || (selected.verified ? 'Verified' : 'Not verified') }}</dd>
            </dl>

            <div class="flex flex-wrap justify-end gap-2">
              <button
                v-if="selected.status === 'Open' && !selected.verified && selected.paytm_order_id && !selected.tid"
                @click="recheck(selected)"
                :disabled="busy"
                class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
              >Check with Paytm</button>
              <button
                @click="togglePayload"
                class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)]"
              >{{ showPayload ? 'Hide' : 'Show' }} Paytm payload</button>
            </div>
            <pre
              v-if="showPayload"
              class="max-h-72 overflow-auto rounded-lg bg-[var(--color-surface)] p-3 font-mono text-xs custom-scrollbar"
            >{{ payloadText }}</pre>
          </section>

          <!-- Done -->
          <section
            v-if="selected.status === 'Receipted'"
            class="flex flex-col gap-2 rounded-2xl border border-[var(--color-success)] bg-[var(--color-surface-raised)] p-5"
          >
            <h2 class="text-lg font-bold uppercase tracking-wide">Receipt</h2>
            <dl class="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
              <dt class="text-[var(--color-text-muted)]">Payment Entry</dt>
              <dd><a :href="`/app/payment-entry/${selected.payment_entry}`" target="_blank" class="font-bold text-[var(--color-info)] underline">{{ selected.payment_entry }}</a></dd>
              <dt class="text-[var(--color-text-muted)]">From ledger</dt><dd>{{ selected.party }} <span class="opacity-60">({{ selected.party_type }})</span></dd>
              <dt class="text-[var(--color-text-muted)]">To ledger</dt><dd>{{ selected.paid_to }}</dd>
              <dt class="text-[var(--color-text-muted)]">Reference no</dt><dd class="font-mono">{{ selected.reference_no }}</dd>
            </dl>
          </section>

          <!-- Create receipt -->
          <section
            v-else-if="receiptOpen"
            class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5"
          >
            <h2 class="text-lg font-bold uppercase tracking-wide">Create Receipt</h2>

            <div class="grid grid-cols-2 gap-4">
              <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                <span class="text-xs font-bold uppercase opacity-75">From Ledger <span class="normal-case opacity-75">(who paid · credit)</span></span>
                <input
                  ref="fromInput"
                  :value="form.party_label"
                  readonly
                  placeholder="Enter to search party / account"
                  @keydown.enter.prevent="openSearch('from')"
                  @click="openSearch('from')"
                  class="w-full cursor-pointer rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none"
                />
                <span v-if="form.party_type" class="text-xs opacity-75">{{ form.party_type }}</span>
              </label>
              <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                <span class="text-xs font-bold uppercase opacity-75">To Ledger <span class="normal-case opacity-75">(received in · debit)</span></span>
                <input
                  ref="toInput"
                  :value="form.paid_to"
                  readonly
                  placeholder="Enter to search account"
                  @keydown.enter.prevent="openSearch('to')"
                  @click="openSearch('to')"
                  class="w-full cursor-pointer rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none"
                />
              </label>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                <span class="text-xs font-bold uppercase opacity-75">Amount (₹)</span>
                <input
                  :value="fmt(selected.amount)"
                  readonly
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-right font-mono text-2xl font-bold text-[var(--color-text)] outline-none"
                />
              </label>
              <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                <span class="text-xs font-bold uppercase opacity-75">Reference No</span>
                <input
                  ref="refInput"
                  v-model="form.reference_no"
                  @keydown.enter.prevent="remarksInput?.focus()"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-lg text-[var(--color-text)] outline-none"
                />
              </label>
            </div>

            <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
              <span class="text-xs font-bold uppercase opacity-75">Remarks <span class="normal-case opacity-75">(optional, goes on the Payment Entry)</span></span>
              <input
                ref="remarksInput"
                v-model="form.remarks"
                maxlength="140"
                @keydown.enter.prevent="createReceipt"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none"
              />
            </label>

            <div class="text-sm text-[var(--color-text-muted)]">
              Posted on {{ (selected.txn_date || selected.received_at || '').slice(0, 10) }} (Paytm txn date)
              · {{ defaultCompany || 'default company' }}
              · Cost center {{ defaultCostCenter || '—' }}
            </div>

            <div class="flex items-center justify-between gap-4">
              <span v-if="!selected.verified" class="text-sm font-bold text-[var(--color-danger)]">Not verified by Paytm: check the Paytm dashboard before receipting.</span>
              <span v-else></span>
              <button
                @click="createReceipt"
                :disabled="creating"
                class="shrink-0 rounded-xl bg-[var(--color-success)] px-6 py-2.5 text-lg font-black uppercase text-white shadow-sm transition-opacity disabled:opacity-50"
              >{{ creating ? 'Creating…' : 'Create Receipt' }}</button>
            </div>
          </section>

          <div v-else-if="selected.status === 'Open'" class="flex justify-end">
            <button
              @click="openReceipt(selected)"
              class="rounded-xl bg-[var(--color-success)] px-6 py-2.5 text-lg font-black uppercase text-white"
            >Create Receipt</button>
          </div>

          <div v-if="error" class="rounded-lg bg-[var(--color-danger)]/15 px-3 py-2 text-sm font-bold text-[var(--color-danger)]">{{ error }}</div>
        </div>
        </template>
      </main>
    </div>

    <CustomerSearchModal
      :show="showSearch"
      :title="searchTarget === 'from' ? 'From Ledger' : 'To Ledger'"
      :subtitle="searchTarget === 'from' ? 'Who paid (credit)' : 'Account the money came into (debit)'"
      :allowedTypes="searchTarget === 'from' ? ['Customer', 'Supplier', 'Employee', 'Account'] : ['Account']"
      :initialType="searchTarget === 'from' ? 'All' : 'Account'"
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
import { frappeGet, frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import { getFrappeSocket } from '../services/frappeSocket.js'

const router = useRouter()
const API = 'ssplbilling.api.paytm_unknown_api'
const POLL_MS = 30000

const rows = ref([])
const loading = ref(false)
const search = ref('')
const statusFilters = ['Open', 'Receipted', 'All']
const statusFilter = ref('Open')
const selected = ref(null)
const busy = ref(false)
const error = ref('')
const upiAccount = ref('')
const defaultCompany = localStorage.getItem('wb-company') || ''
const defaultCostCenter = localStorage.getItem('wb-cost-center') || ''

const receiptOpen = ref(false)
const creating = ref(false)
const form = reactive({ party_type: '', party: '', party_label: '', paid_to: '', reference_no: '', remarks: '' })

const showPayload = ref(false)
const payloadText = ref('')

const showSearch = ref(false)
const searchTarget = ref('from')

// Webhook Log view: every notification payment_webhook() received
const views = [{ id: 'unknown', label: 'Unknown Payments' }, { id: 'log', label: 'Webhook Log' }]
const view = ref('unknown')
const logs = ref([])
const logsLoading = ref(false)
const logSearch = ref('')
// linked: 1 booked (submitted invoice / receipt), 0 paid but not booked yet, null no payment to book
const linkFilters = [
  { id: 'all', label: 'All' },
  { id: 'todo', label: 'To book' },
  { id: 'booked', label: 'Booked' },
  { id: 'none', label: 'No payment' },
]
const linkFilter = ref('all')
const linkMatch = (l, f) =>
  f === 'all' || (f === 'booked' ? l.linked === 1 : f === 'todo' ? l.linked === 0 : l.linked == null)
const selectedLog = ref(null)
const showLogPayload = ref(false)
const logPayloadText = ref('')
const RESULT_TEXT = {
  matched: 'Matched a system order (EDC / QR / link); its status was re-read from Paytm',
  recorded: 'Not a system order: kept as an unknown payment',
  duplicate: 'Same payment already kept as an unknown payment',
  known: 'Payment of a system order, matched by txn id / RRN',
  'not paid': 'Paytm reports the payment as not successful: ignored',
  rejected: 'MID or checksum mismatch: ignored (see Error Log)',
  unreadable: 'No amount or reference in the payload: ignored (see Error Log)',
  error: 'Failed while recording (see Error Log)',
}

const fromInput = ref(null)
const toInput = ref(null)
const refInput = ref(null)
const remarksInput = ref(null)

const fmt = (v) => Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fmtDate = (v) => (v || '').slice(0, 16)

const filteredRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (statusFilter.value !== 'All' && r.status !== statusFilter.value) return false
    if (!q) return true
    return [r.name, r.rrn, r.paytm_txn_id, r.paytm_order_id, r.payment_entry, r.party, String(r.amount)]
      .some((v) => (v || '').toLowerCase().includes(q))
  })
})

const filteredLogs = computed(() => {
  const q = logSearch.value.trim().toLowerCase()
  return logs.value.filter((l) => {
    if (!linkMatch(l, linkFilter.value)) return false
    if (!q) return true
    return [l.name, l.result, l.order_id, l.rrn, l.paytm_txn_id, l.ref_name, l.linked_to, l.tid, String(l.amount)]
      .some((v) => (v || '').toLowerCase().includes(q))
  })
})

const linkCount = (f) => logs.value.filter((l) => linkMatch(l, f)).length

function resultClass(result) {
  if (result === 'matched' || result === 'recorded') return 'bg-[var(--color-success)]'
  if (result === 'duplicate' || result === 'known') return 'bg-[var(--color-info)]'
  if (result === 'not paid') return 'bg-[var(--color-warning)]'
  return 'bg-[var(--color-danger)]'
}
const resultText = (result) => RESULT_TEXT[result] || result || '—'
const slug = (doctype) => (doctype || '').toLowerCase().replace(/ /g, '-')

async function loadLogs() {
  logsLoading.value = true
  try {
    logs.value = (await frappeGet(`${API}.get_webhook_logs`, { limit: 500 })) || []
    if (selectedLog.value) selectedLog.value = logs.value.find((l) => l.name === selectedLog.value.name) || null
  } catch (e) {
    error.value = e.message
  } finally {
    logsLoading.value = false
  }
}

function setView(v) {
  if (view.value === v) return
  view.value = v
  error.value = ''
  if (v === 'log') loadLogs()
  else loadRows()
}

function selectLog(l) {
  if (selectedLog.value?.name === l.name) return
  error.value = ''
  showLogPayload.value = false
  logPayloadText.value = ''
  selectedLog.value = l
}

async function toggleLogPayload() {
  showLogPayload.value = !showLogPayload.value
  if (!showLogPayload.value || logPayloadText.value) return
  try {
    const doc = await frappeGet(`${API}.get_webhook_log`, { name: selectedLog.value.name })
    try {
      logPayloadText.value = JSON.stringify(JSON.parse(doc.payload), null, 2)
    } catch {
      logPayloadText.value = doc.payload || '(empty)'
    }
  } catch (e) {
    error.value = e.message
  }
}

async function openUnknown(name) {
  view.value = 'unknown'
  error.value = ''
  statusFilter.value = 'All'
  await loadRows()
  const r = rows.value.find((x) => x.name === name)
  if (r) selectRow(r)
  else error.value = `${name} is no longer listed (deleted?)`
}

function statusCount(s) {
  return s === 'All' ? rows.value.length : rows.value.filter((r) => r.status === s).length
}

async function loadRows() {
  loading.value = true
  try {
    const res = await frappeGet(`${API}.get_unknown_payments`, { limit: 500 })
    rows.value = res.rows || []
    upiAccount.value = res.upi_account || ''
    if (selected.value) selected.value = rows.value.find((r) => r.name === selected.value.name) || null
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function resetForm(r) {
  Object.assign(form, {
    party_type: '',
    party: '',
    party_label: '',
    paid_to: upiAccount.value,
    reference_no: r.rrn || r.paytm_txn_id || '',
    remarks: '',
  })
}

function selectRow(r) {
  if (selected.value?.name === r.name) return
  error.value = ''
  showPayload.value = false
  payloadText.value = ''
  receiptOpen.value = false
  selected.value = r
}

function openReceipt(r) {
  selectRow(r)
  resetForm(r)
  receiptOpen.value = true
  nextTick(() => fromInput.value?.focus())
}

async function togglePayload() {
  showPayload.value = !showPayload.value
  if (!showPayload.value || payloadText.value) return
  try {
    const doc = await frappeGet(`${API}.get_unknown_payment`, { name: selected.value.name })
    try {
      payloadText.value = JSON.stringify(JSON.parse(doc.payload), null, 2)
    } catch {
      payloadText.value = doc.payload || '(empty)'
    }
  } catch (e) {
    error.value = e.message
  }
}

function openSearch(target) {
  searchTarget.value = target
  showSearch.value = true
}

function onSelect(item) {
  showSearch.value = false
  if (searchTarget.value === 'from') {
    form.party = item.name
    form.party_type = item.type && item.type !== 'Account' ? item.type : 'Account'
    form.party_label = item.label || item.customer_name || item.supplier_name || item.employee_name || item.account_name || item.name
    nextTick(() => (form.paid_to ? refInput : toInput).value?.focus())
  } else {
    form.paid_to = item.name
    nextTick(() => refInput.value?.focus())
  }
}

async function createReceipt() {
  const r = selected.value
  if (!r || !receiptOpen.value || creating.value) return
  error.value = ''
  if (!form.party) { error.value = 'Select the From ledger'; return fromInput.value?.focus() }
  if (!form.paid_to) { error.value = 'Select the To ledger'; return toInput.value?.focus() }
  if (!form.reference_no.trim()) { error.value = 'Enter the reference number'; return refInput.value?.focus() }
  let allowUnverified = 0
  if (!r.verified) {
    if (!confirm(`₹${fmt(r.amount)} is NOT verified by Paytm.\n\nCreate the receipt only if you have seen this payment in the Paytm dashboard. Continue?`)) return
    allowUnverified = 1
  }
  creating.value = true
  try {
    const res = await frappePost(`${API}.create_receipt`, {
      name: r.name,
      party_type: form.party_type,
      party: form.party,
      paid_to: form.paid_to,
      reference_no: form.reference_no.trim(),
      remarks: form.remarks,
      allow_unverified: allowUnverified,
      // Same defaults the Payment / Receipt page books with
      company: localStorage.getItem('wb-company') || null,
      cost_center: localStorage.getItem('wb-cost-center') || null,
    }, { silent: true })
    Object.assign(r, res)
    receiptOpen.value = false
  } catch (e) {
    error.value = e.message
    loadRows()
  } finally {
    creating.value = false
  }
}

async function removeRow(r) {
  if (!confirm(`Delete the Paytm payment ₹${fmt(r.amount)} (${r.rrn || r.paytm_txn_id})?\n\nNo receipt will be made for it.`)) return
  busy.value = true
  error.value = ''
  try {
    await frappePost(`${API}.delete_unknown_payment`, { name: r.name }, { silent: true })
    rows.value = rows.value.filter((x) => x.name !== r.name)
    if (selected.value?.name === r.name) {
      selected.value = null
      receiptOpen.value = false
    }
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function recheck(r) {
  busy.value = true
  error.value = ''
  try {
    const doc = await frappePost(`${API}.recheck_unknown_payment`, { name: r.name }, { silent: true })
    for (const k of Object.keys(r)) if (k in doc) r[k] = doc[k]
    if (receiptOpen.value && !form.reference_no) form.reference_no = r.rrn || r.paytm_txn_id || ''
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

let pollTimer = null
function onSocket() {
  loadRows()
}
function onLogSocket() {
  if (view.value === 'log') loadLogs()
}
function refresh() {
  if (view.value === 'log') loadLogs()
  else loadRows()
}

function onKeydown(e) {
  if (showSearch.value) return
  if (e.key === 'Escape') { e.preventDefault(); router.push('/') }
  else if (e.key === 'F2' && receiptOpen.value) { e.preventDefault(); openSearch('from') }
  else if (e.key === 'F3' && receiptOpen.value) { e.preventDefault(); openSearch('to') }
  else if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); createReceipt() }
}

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  getFrappeSocket()?.on('paytm_unknown_payment', onSocket)
  getFrappeSocket()?.on('paytm_webhook_log', onLogSocket)
  await loadRows()
  pollTimer = setInterval(() => { if (!document.hidden) refresh() }, POLL_MS)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  getFrappeSocket()?.off('paytm_unknown_payment', onSocket)
  getFrappeSocket()?.off('paytm_webhook_log', onLogSocket)
  clearInterval(pollTimer)
})
</script>
