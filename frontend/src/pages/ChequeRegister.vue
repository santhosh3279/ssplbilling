<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-sm shrink-0">
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/')"
          class="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-normal uppercase tracking-tight">Cheque Register</h1>
      </div>

      <button
        @click="openNewCheque"
        class="rounded-xl bg-[var(--color-highlight)] px-6 py-2.5 text-sm font-black uppercase tracking-widest text-[var(--color-text-on-highlight)] shadow-md hover:brightness-105 active:scale-95 transition-all"
      >
        + New Cheque
      </button>
    </header>

    <main class="flex-1 overflow-hidden p-6 flex flex-col gap-5">
      <!-- Summary Cards -->
      <div class="grid grid-cols-4 gap-6 shrink-0">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
          <span class="text-[15px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Cheques in Hand (Pending Received)</span>
          <div class="flex items-baseline justify-between mt-1">
            <span class="text-[45px] font-mono font-black text-[var(--color-success)]">₹{{ fmt(summary.received_total) }}</span>
            <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Count: {{ summary.received_count }}</span>
          </div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
          <span class="text-[15px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Cheques Issued (Pending Presentation)</span>
          <div class="flex items-baseline justify-between mt-1">
            <span class="text-[45px] font-mono font-black text-[var(--color-danger)]">₹{{ fmt(summary.issued_total) }}</span>
            <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Count: {{ summary.issued_count }}</span>
          </div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
          <span class="text-[15px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Cheque Due Today</span>
          <div class="flex items-baseline justify-between mt-1">
            <span class="text-[45px] font-mono font-black text-[var(--color-warning)]">₹{{ fmt(summary.due_today_total) }}</span>
            <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Count: {{ summary.due_today_count }}</span>
          </div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
          <div class="flex items-baseline justify-between gap-2">
            <span class="text-[15px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Bank Balance</span>
            <span class="text-[1.125rem] font-bold text-[var(--color-text-muted)] uppercase tracking-wider truncate" :title="bankName">{{ bankName || '—' }}</span>
          </div>
          <div class="flex flex-col mt-1">
            <span class="text-[45px] font-mono font-black text-[var(--color-info)]">₹{{ fmt(bankBalance) }}</span>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex items-center justify-between shrink-0">
        <div class="flex gap-2">
          <button
            v-for="s in STATUSES"
            :key="s"
            @click="statusFilter = s; loadCheques()"
            class="px-2 py-[3px] rounded-xl text-[18px] font-black uppercase tracking-widest border transition-all"
            :class="statusFilter === s
              ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] border-[var(--color-highlight)] shadow-md'
              : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] border-[var(--color-border)] hover:border-[var(--color-highlight)]'"
          >
            {{ s }}
          </button>
        </div>
        <div class="flex items-center gap-3">
          <select
            v-model="directionFilter"
            @change="loadCheques"
            class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-1.5 text-xs font-black uppercase tracking-widest text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
          >
            <option value="All">All Directions</option>
            <option value="Received">Received</option>
            <option value="Issued">Issued</option>
          </select>
          <button
            @click="loadCheques"
            class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-1.5 text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)] hover:border-[var(--color-highlight)] transition-all"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="flex-1 min-h-0 rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden flex flex-col">
        <div v-if="isLoading" class="flex-1 flex flex-col items-center justify-center gap-4">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-highlight)] border-t-transparent"></div>
          <p class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Loading cheques...</p>
        </div>
        <div v-else-if="cheques.length === 0" class="flex-1 flex flex-col items-center justify-center gap-3">
          <div class="text-6xl">🏦</div>
          <p class="text-xs italic text-[var(--color-text-muted)]">No {{ statusFilter === 'All' ? '' : statusFilter.toLowerCase() + ' ' }}cheques found.</p>
        </div>
        <div v-else class="flex-1 overflow-y-auto custom-scrollbar">
          <table class="w-full text-[18px]">
            <thead class="sticky top-0 bg-[var(--color-surface-raised)] z-10">
              <tr class="font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="px-4 py-3 text-left">Cheque No</th>
                <th class="px-4 py-3 text-left">Direction</th>
                <th class="px-4 py-3 text-left">Party</th>
                <th class="px-4 py-3 text-left">Ledger Type</th>
                <th class="px-4 py-3 text-left">Bank</th>
                <th class="px-4 py-3 text-center">Cheque Date</th>
                <th class="px-4 py-3 text-right">Amount</th>
                <th class="px-4 py-3 text-center">Status</th>
                <th class="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(chq, idx) in cheques" :key="chq.name">
                <!-- Today's Header -->
                <tr v-if="idx === 0 && chq.cheque_date === getTodayIST()" class="bg-[var(--color-warning)]/15 pointer-events-none">
                  <td colspan="9" class="px-4 py-2.5 text-xs font-black uppercase tracking-widest text-[var(--color-warning)]">
                    ⭐ Today's Cheques (Due Today)
                  </td>
                </tr>
                <!-- Other Header -->
                <tr v-if="idx > 0 && cheques[idx-1].cheque_date === getTodayIST() && chq.cheque_date !== getTodayIST()" class="bg-[var(--color-surface-raised)]/50 pointer-events-none border-t border-[var(--color-border)]">
                  <td colspan="9" class="px-4 py-2.5 text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                    Other Cheques
                  </td>
                </tr>
                <!-- Main Cheque Row -->
                <tr
                  :ref="el => setRowRef(el, chq.name)"
                  @click="selectedChequeName = chq.name"
                  class="border-t border-[var(--color-border)]/60 hover:bg-[var(--color-surface-raised)]/40 transition-colors cursor-pointer scroll-mt-[52px]"
                  :class="[
                    selectedChequeName === chq.name ? 'bg-[var(--color-focus)] text-[var(--color-text-on-focus)]' : '',
                    chq.cheque_date === getTodayIST() && selectedChequeName !== chq.name ? 'bg-[var(--color-warning)]/5 border-l-4 border-l-[var(--color-warning)] shadow-inner' : ''
                  ]"
                >
                  <td class="px-4 py-3 font-mono font-bold">{{ chq.cheque_no }}</td>
                  <td class="px-4 py-3">
                    <span
                      class="px-2 py-0.5 rounded font-black uppercase tracking-widest"
                      :class="chq.direction === 'Received' ? 'bg-[var(--color-success)]/10 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/10 text-[var(--color-danger)]'"
                    >
                      {{ chq.direction === 'Received' ? '⬇ Received' : '⬆ Issued' }}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="font-bold">{{ chq.party_name || chq.party }}</div>
                  </td>
                  <td class="px-4 py-3 text-[var(--color-text-muted)] uppercase tracking-wider">
                    {{ chq.party_type }}
                  </td>
                  <td class="px-4 py-3 text-[var(--color-text-muted)]">{{ chq.bank_name || '—' }}</td>
                  <td class="px-4 py-3 text-center font-semibold" :class="isPostDated(chq) ? 'text-[var(--color-warning)]' : ''">
                    {{ formatDate(chq.cheque_date) }}
                    <div v-if="isPostDated(chq)" class="font-black uppercase tracking-widest text-[var(--color-warning)]">Post-dated</div>
                  </td>
                  <td class="px-4 py-3 text-right font-mono font-black">₹{{ fmt(chq.amount) }}</td>
                  <td class="px-4 py-3 text-center">
                    <span
                      class="px-2.5 py-0.5 rounded-full font-black uppercase tracking-widest"
                      :class="STATUS_CLASSES[chq.status] || ''"
                    >
                      {{ chq.status }}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex justify-end gap-2">
                      <button
                        v-if="chq.status === 'Pending'"
                        @click="openSettle(chq)"
                        class="rounded-lg bg-[var(--color-success)] px-2.5 py-1 text-xs font-black uppercase tracking-widest text-white shadow-sm hover:brightness-110 active:scale-95 transition-all"
                      >
                        Settle
                      </button>
                      <button
                        v-if="chq.status === 'Pending'"
                        @click="markBounced(chq)"
                        class="rounded-lg bg-[var(--color-danger)]/10 px-2.5 py-1 text-xs font-black uppercase tracking-widest text-[var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white active:scale-95 transition-all"
                      >
                        Bounce
                      </button>
                      <button
                        v-if="chq.status === 'Pending'"
                        @click="markCancelled(chq)"
                        class="rounded-lg border border-[var(--color-border)] px-2.5 py-1 text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)] hover:border-[var(--color-danger)] hover:text-[var(--color-danger)] active:scale-95 transition-all"
                      >
                        Cancel
                      </button>
                      <button
                        @click="triggerPrint(chq)"
                        class="rounded-lg border border-[var(--color-border)] px-2.5 py-1 text-xs font-black text-[var(--color-text-muted)] hover:border-[var(--color-highlight)] hover:text-[var(--color-highlight)] active:scale-95 transition-all"
                        title="Print Cheque"
                      >
                        🖨
                      </button>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <!-- ═══ New Cheque Modal ═══ -->
    <div v-if="showNewModal" class="fixed inset-0 z-40 flex items-center justify-center bg-black/50" @keydown.esc.prevent.stop="showWarningModal = true">
      <div class="w-[560px] rounded-3xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div class="border-b border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface)]">
          <div class="text-xl font-bold">New Cheque Entry</div>
          <div class="text-sm text-[var(--color-text-muted)]">Settles the party ledger now; bank ledger only on clearance day</div>
        </div>

        <div class="px-6 py-5 space-y-4">
          <!-- Direction toggle -->
          <div class="grid grid-cols-2 gap-3">
            <button
              ref="receivedBtnRef"
              @click="setDirection('Received')"
              @keydown.right.prevent="setDirection('Issued'); focusIssuedBtn()"
              @keydown.enter.prevent="showPartySearch = true"
              class="py-3 rounded-2xl border text-sm font-black uppercase tracking-widest transition-all focus:outline-none focus:ring-4 focus:ring-[var(--color-highlight)]"
              :class="newForm.direction === 'Received'
                ? 'bg-[var(--color-success)] text-white border-[var(--color-success)] shadow-md'
                : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] border-[var(--color-border)]'"
            >
              ⬇ Received
            </button>
            <button
              ref="issuedBtnRef"
              @click="setDirection('Issued')"
              @keydown.left.prevent="setDirection('Received'); focusReceivedBtn()"
              @keydown.enter.prevent="showPartySearch = true"
              class="py-3 rounded-2xl border text-sm font-black uppercase tracking-widest transition-all focus:outline-none focus:ring-4 focus:ring-[var(--color-highlight)]"
              :class="newForm.direction === 'Issued'
                ? 'bg-[var(--color-danger)] text-white border-[var(--color-danger)] shadow-md'
                : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] border-[var(--color-border)]'"
            >
              ⬆ Issued
            </button>
          </div>

          <!-- Party -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">{{ newForm.party_type }} *</label>
            <button
              @click="showPartySearch = true"
              class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 text-left font-bold hover:border-[var(--color-highlight)] transition-all"
              :class="newForm.party ? 'text-[var(--color-text)] opacity-100' : 'text-[var(--color-highlight)] opacity-70'"
            >
              {{ newForm.party_label || 'Select party...' }}
            </button>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Cheque No *</label>
              <input
                ref="chequeNoInputRef"
                v-model="newForm.cheque_no"
                @keydown.enter.prevent="chequeDateInputRef?.focus()"
                class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 font-mono font-bold outline-none focus:border-[var(--color-highlight)] text-[1.25rem]"
                placeholder="000123"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Cheque Date (DD-MM-YYYY) *</label>
              <input
                ref="chequeDateInputRef"
                v-model="newForm.cheque_date_display"
                @input="onChequeDateInput"
                @blur="autoCompleteChequeDate"
                @keydown.enter.prevent="bankNameInputRef?.focus()"
                class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 font-bold outline-none focus:border-[var(--color-highlight)] font-mono text-[1.25rem]"
                placeholder="DD-MM-YYYY"
                maxlength="10"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Bank Name</label>
              <input
                ref="bankNameInputRef"
                v-model="newForm.bank_name"
                @keydown.enter.prevent="amountInputRef?.focus()"
                class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 font-bold outline-none focus:border-[var(--color-highlight)]"
                placeholder="e.g. SBI"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Amount *</label>
              <input
                ref="amountInputRef"
                v-model.number="newForm.amount"
                type="number"
                min="0"
                step="0.01"
                @keydown.enter.prevent="remarksInputRef?.focus()"
                class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 h-[50px] py-0 text-right font-mono text-[27px] leading-[48px] font-black text-[var(--color-info)] outline-none focus:border-[var(--color-highlight)]"
                placeholder="0.00"
              />
            </div>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Remarks</label>
            <input
              ref="remarksInputRef"
              v-model="newForm.remarks"
              @keydown.enter.prevent="saveBtnRef?.focus()"
              class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 outline-none focus:border-[var(--color-highlight)]"
              placeholder="Optional note"
            />
          </div>
        </div>

        <div class="flex justify-end gap-3 border-t border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface)]">
          <button class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-2 font-semibold" @click="showWarningModal = true">Cancel</button>
          <button
            @click="submitNewCheque(true)"
            :disabled="isSaving || !canSaveNew"
            class="rounded-xl bg-[var(--color-info)] px-6 py-2 font-black uppercase tracking-widest text-white shadow-md hover:brightness-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            🖨 Save &amp; Print
          </button>
          <button
            ref="saveBtnRef"
            @click="submitNewCheque(false)"
            :disabled="isSaving || !canSaveNew"
            class="rounded-xl bg-[var(--color-highlight)] px-6 py-2 font-black uppercase tracking-widest text-[var(--color-text-on-highlight)] shadow-md hover:brightness-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {{ isSaving ? 'Saving...' : 'Save Cheque' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ Settle Modal ═══ -->
    <div v-if="settleTarget" class="fixed inset-0 z-40 flex items-center justify-center bg-black/50" @keydown.esc="settleTarget = null">
      <div class="w-[480px] rounded-3xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div class="border-b border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface)]">
          <div class="text-xl font-bold">Settle Cheque</div>
          <div class="text-sm text-[var(--color-text-muted)]">Posts to the bank ledger on the clearance date</div>
        </div>

        <div class="px-6 py-5 space-y-4">
          <div class="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 space-y-1">
            <div class="flex justify-between text-sm">
              <span class="font-bold">{{ settleTarget.party_name || settleTarget.party }}</span>
              <span class="font-mono font-black text-lg">₹{{ fmt(settleTarget.amount) }}</span>
            </div>
            <div class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] font-semibold">
              {{ settleTarget.direction }} · Cheque {{ settleTarget.cheque_no }} · {{ formatDate(settleTarget.cheque_date) }}
              <span v-if="settleTarget.bank_name">· {{ settleTarget.bank_name }}</span>
            </div>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Clearance Date (DD-MM-YYYY) *</label>
            <input
              v-model="settleForm.clearance_date_display"
              @input="onClearanceDateInput"
              @blur="autoCompleteClearanceDate"
              class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 font-bold outline-none focus:border-[var(--color-highlight)] font-mono"
              placeholder="DD-MM-YYYY"
              maxlength="10"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Bank Account *</label>
            <select v-model="settleForm.bank_account" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 font-bold outline-none focus:border-[var(--color-highlight)]">
              <option value="">— Select bank account —</option>
              <option v-for="acc in bankAccounts" :key="acc.name" :value="acc.name">{{ acc.name }}</option>
            </select>
          </div>
        </div>

        <div class="flex justify-end gap-3 border-t border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface)]">
          <button class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-2 font-semibold" @click="settleTarget = null">Cancel</button>
          <button
            @click="submitSettle"
            :disabled="isSaving || !settleForm.bank_account || !settleForm.clearance_date"
            class="rounded-xl bg-[var(--color-success)] px-6 py-2 font-black uppercase tracking-widest text-white shadow-md hover:brightness-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {{ isSaving ? 'Settling...' : 'Confirm Settlement' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Party Search Modal -->
    <CustomerSearchModal
      ref="partySearchRef"
      :show="showPartySearch"
      :allowedTypes="['Customer', 'Supplier', 'Employee']"
      :initialType="newForm.direction === 'Received' ? 'Customer' : 'Supplier'"
      :skip-date-filter="true"
      @close="showPartySearch = false"
      @select="handlePartySelect"
    />

    <!-- Print Options Modal -->
    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="printTargetName"
      doctype="SSPL Cheque"
      @close="showPrintModal = false"
    />

    <!-- Warning Discard Modal -->
    <Warning
      :show="showWarningModal"
      title="Discard Changes"
      message="Are you sure you want to discard this cheque entry?"
      @close="showWarningModal = false"
      @confirm="confirmDiscardNewCheque"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchCheques,
  createCheque,
  clearCheque,
  bounceCheque,
  cancelCheque,
  fetchChequeBankAccounts,
  frappeGet,
} from '../api'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import Warning from '../components/Warning.vue'

const router = useRouter()

const receivedBtnRef = ref(null)
const issuedBtnRef = ref(null)
const chequeNoInputRef = ref(null)
const chequeDateInputRef = ref(null)
const bankNameInputRef = ref(null)
const amountInputRef = ref(null)
const remarksInputRef = ref(null)
const saveBtnRef = ref(null)

function focusReceivedBtn() {
  nextTick(() => receivedBtnRef.value?.focus())
}

function focusIssuedBtn() {
  nextTick(() => issuedBtnRef.value?.focus())
}

const STATUSES = ['Pending', 'Cleared', 'Bounced', 'Cancelled', 'All']
const STATUS_CLASSES = {
  Pending: 'bg-[var(--color-warning)]/10 text-[var(--color-warning)]',
  Cleared: 'bg-[var(--color-success)]/10 text-[var(--color-success)]',
  Bounced: 'bg-[var(--color-danger)]/10 text-[var(--color-danger)]',
  Cancelled: 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]',
}

const statusFilter = ref('Pending')
const directionFilter = ref('All')
const isLoading = ref(false)
const isSaving = ref(false)
const cheques = ref([])
const summary = ref({ received_total: 0, received_count: 0, issued_total: 0, issued_count: 0, due_today_total: 0, due_today_count: 0 })
const bankAccounts = ref([])
const selectedChequeName = ref('')
const rowRefs = new Map()

function setRowRef(el, name) {
  if (el) rowRefs.set(name, el)
  else rowRefs.delete(name)
}
const bankBalance = ref(0)
const bankName = ref(localStorage.getItem('wb-bank') || '')

async function loadBankBalance() {
  const account = bankName.value
  if (!account) return
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_balance', { account })
    bankBalance.value = res?.balance || 0
  } catch (e) {
    console.error('Failed to load bank balance:', e)
  }
}

const showNewModal = ref(false)
const showPartySearch = ref(false)
const partySearchRef = ref(null)
const settleTarget = ref(null)
const showPrintModal = ref(false)
const showWarningModal = ref(false)
const printTargetName = ref('')

const today = () => new Date().toISOString().slice(0, 10)

function formatDateToDisplay(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}-${m}-${y}`
}

function getLocalDateParts() {
  const now = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options)
  return formatter.format(now).split('-').map(Number)
}

function getTodayIST() {
  const [y, m, d] = getLocalDateParts()
  const mm = String(m).padStart(2, '0')
  const dd = String(d).padStart(2, '0')
  return `${y}-${mm}-${dd}`
}

function onChequeDateInput(e) {
  let val = e.target.value.replace(/\D/g, '')

  if (val.length === 4) {
    const day = parseInt(val.slice(0, 2))
    const month = parseInt(val.slice(2, 4))
    
    if (!isNaN(day) && !isNaN(month) && month >= 1 && month <= 12) {
      const [y, m] = getLocalDateParts()
      let year = y

      if (month > m) {
        year--
      }
      
      const dayStr = day.toString().padStart(2, '0')
      const monthStr = month.toString().padStart(2, '0')
      
      newForm.value.cheque_date = `${year}-${monthStr}-${dayStr}`
      newForm.value.cheque_date_display = `${dayStr}-${monthStr}-${year}`
      return
    }
  }

  if (val.length > 2 && val.length <= 4) {
    val = val.slice(0, 2) + '-' + val.slice(2)
  } else if (val.length > 4) {
    val = val.slice(0, 2) + '-' + val.slice(2, 4) + '-' + val.slice(4, 8)
  }

  newForm.value.cheque_date_display = val

  if (val.length === 10) {
    const [d, m, y] = val.split('-')
    if (d && m && y && y.length === 4) {
      newForm.value.cheque_date = `${y}-${m}-${d}`
    }
  }
}

function autoCompleteChequeDate() {
  let val = newForm.value.cheque_date_display.replace(/\D/g, '')

  if (val.length >= 1 && val.length <= 2) {
    const day = parseInt(val)
    if (!isNaN(day) && day >= 1 && day <= 31) {
      const [y, m] = getLocalDateParts()
      const dayStr = day.toString().padStart(2, '0')
      const monthStr = m.toString().padStart(2, '0')
      
      newForm.value.cheque_date = `${y}-${monthStr}-${dayStr}`
      newForm.value.cheque_date_display = `${dayStr}-${monthStr}-${y}`
    }
  }
}

function onClearanceDateInput(e) {
  let val = e.target.value.replace(/\D/g, '')

  if (val.length === 4) {
    const day = parseInt(val.slice(0, 2))
    const month = parseInt(val.slice(2, 4))
    
    if (!isNaN(day) && !isNaN(month) && month >= 1 && month <= 12) {
      const [y, m] = getLocalDateParts()
      let year = y

      if (month > m) {
        year--
      }
      
      const dayStr = day.toString().padStart(2, '0')
      const monthStr = month.toString().padStart(2, '0')
      
      settleForm.value.clearance_date = `${year}-${monthStr}-${dayStr}`
      settleForm.value.clearance_date_display = `${dayStr}-${monthStr}-${year}`
      return
    }
  }

  if (val.length > 2 && val.length <= 4) {
    val = val.slice(0, 2) + '-' + val.slice(2)
  } else if (val.length > 4) {
    val = val.slice(0, 2) + '-' + val.slice(2, 4) + '-' + val.slice(4, 8)
  }

  settleForm.value.clearance_date_display = val

  if (val.length === 10) {
    const [d, m, y] = val.split('-')
    if (d && m && y && y.length === 4) {
      settleForm.value.clearance_date = `${y}-${m}-${d}`
    }
  }
}

function autoCompleteClearanceDate() {
  let val = settleForm.value.clearance_date_display.replace(/\D/g, '')

  if (val.length >= 1 && val.length <= 2) {
    const day = parseInt(val)
    if (!isNaN(day) && day >= 1 && day <= 31) {
      const [y, m] = getLocalDateParts()
      const dayStr = day.toString().padStart(2, '0')
      const monthStr = m.toString().padStart(2, '0')
      
      settleForm.value.clearance_date = `${y}-${monthStr}-${dayStr}`
      settleForm.value.clearance_date_display = `${dayStr}-${monthStr}-${y}`
    }
  }
}

const emptyNewForm = () => ({
  direction: 'Received',
  party: '',
  party_type: 'Customer',
  party_label: '',
  cheque_no: '',
  cheque_date: today(),
  cheque_date_display: formatDateToDisplay(today()),
  bank_name: '',
  amount: null,
  remarks: '',
})

const newForm = ref(emptyNewForm())
const settleForm = ref({
  clearance_date: today(),
  clearance_date_display: formatDateToDisplay(today()),
  bank_account: ''
})

const canSaveNew = computed(() => {
  const f = newForm.value
  if (!f.party) return false
  if (!f.cheque_no || !f.cheque_no.trim()) return false
  if (!f.cheque_date) return false
  if (!f.amount || Number(f.amount) <= 0) return false
  return true
})

function selectChequeAt(idx) {
  const chq = cheques.value[idx]
  if (!chq) return
  selectedChequeName.value = chq.name
  rowRefs.get(chq.name)?.scrollIntoView({ block: 'nearest' })
}

function onKeydown(e) {
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    if (showPartySearch.value || showPrintModal.value || showWarningModal.value ||
        showNewModal.value || settleTarget.value) return
    const tag = e.target?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
    if (!cheques.value.length) return

    e.preventDefault()
    const currentIdx = cheques.value.findIndex(c => c.name === selectedChequeName.value)
    if (e.key === 'ArrowDown') {
      selectChequeAt(currentIdx < 0 ? 0 : Math.min(currentIdx + 1, cheques.value.length - 1))
    } else {
      selectChequeAt(currentIdx < 0 ? 0 : Math.max(currentIdx - 1, 0))
    }
    return
  }

  if (e.key === 'Escape') {
    if (showPartySearch.value) return
    if (showPrintModal.value) return
    if (showWarningModal.value) return

    if (showNewModal.value) {
      e.preventDefault()
      e.stopPropagation()
      showWarningModal.value = true
      return
    }

    if (settleTarget.value) {
      e.preventDefault()
      e.stopPropagation()
      settleTarget.value = null
      return
    }

    e.preventDefault()
    router.push('/')
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  loadCheques()
  loadBankBalance()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})

function confirmDiscardNewCheque() {
  showWarningModal.value = false
  showNewModal.value = false
}

watch(showPartySearch, (v) => {
  if (v) nextTick(() => partySearchRef.value?.focus())
})

async function loadCheques() {
  isLoading.value = true
  try {
    const res = await fetchCheques(
      statusFilter.value,
      directionFilter.value,
      localStorage.getItem('wb-company') || ''
    )
    const todayStr = getTodayIST()
    const allCheques = res.cheques || []
    const todayList = allCheques.filter(c => c.cheque_date === todayStr)
    const otherList = allCheques.filter(c => c.cheque_date !== todayStr)
    cheques.value = [...todayList, ...otherList]
    summary.value = res.summary || summary.value
  } catch (e) {
    alert('Failed to load cheques: ' + e.message)
  } finally {
    isLoading.value = false
  }
}

function openNewCheque() {
  newForm.value = emptyNewForm()
  showNewModal.value = true
  nextTick(() => {
    receivedBtnRef.value?.focus()
  })
}

function triggerPrint(chq) {
  printTargetName.value = chq.name
  showPrintModal.value = true
}

function setDirection(d) {
  if (newForm.value.direction === d) return
  newForm.value.direction = d
  newForm.value.party_type = d === 'Received' ? 'Customer' : 'Supplier'
  newForm.value.party = ''
  newForm.value.party_label = ''
}

function handlePartySelect(item) {
  showPartySearch.value = false
  newForm.value.party = item.name
  newForm.value.party_type = item.type || newForm.value.party_type
  newForm.value.party_label = item.label || item.name
  nextTick(() => {
    chequeNoInputRef.value?.focus()
    chequeNoInputRef.value?.select()
  })
}

async function submitNewCheque(andPrint = false) {
  if (!canSaveNew.value || isSaving.value) return
  isSaving.value = true
  try {
    const res = await createCheque({
      company: localStorage.getItem('wb-company') || '',
      direction: newForm.value.direction,
      party_type: newForm.value.party_type,
      party: newForm.value.party,
      cheque_no: newForm.value.cheque_no.trim(),
      cheque_date: newForm.value.cheque_date,
      bank_name: newForm.value.bank_name,
      amount: Number(newForm.value.amount),
      remarks: newForm.value.remarks,
    })
    showNewModal.value = false
    await loadCheques()
    if (andPrint && res && res.cheque) {
      printTargetName.value = res.cheque
      showPrintModal.value = true
    }
  } catch (e) {
    alert('Failed to save cheque: ' + e.message)
  } finally {
    isSaving.value = false
  }
}

async function openSettle(chq) {
  settleForm.value = {
    clearance_date: today(),
    clearance_date_display: formatDateToDisplay(today()),
    bank_account: ''
  }
  settleTarget.value = chq
  if (bankAccounts.value.length === 0) {
    try {
      bankAccounts.value = await fetchChequeBankAccounts()
    } catch (e) {
      alert('Failed to load bank accounts: ' + e.message)
    }
  }
}

async function submitSettle() {
  if (!settleTarget.value || isSaving.value) return
  isSaving.value = true
  try {
    await clearCheque(settleTarget.value.name, settleForm.value.bank_account, settleForm.value.clearance_date)
    settleTarget.value = null
    await loadCheques()
  } catch (e) {
    alert('Failed to settle cheque: ' + e.message)
  } finally {
    isSaving.value = false
  }
}

async function markBounced(chq) {
  if (!confirm(`Mark cheque ${chq.cheque_no} (₹${fmt(chq.amount)}) as BOUNCED?\nThe linked Payment Entry will be cancelled and the party outstanding restored.`)) return
  try {
    await bounceCheque(chq.name)
    await loadCheques()
  } catch (e) {
    alert('Failed to bounce cheque: ' + e.message)
  }
}

async function markCancelled(chq) {
  if (!confirm(`Cancel cheque ${chq.cheque_no} (₹${fmt(chq.amount)})?\nThe linked Payment Entry will be cancelled and the party outstanding restored.`)) return
  try {
    await cancelCheque(chq.name)
    await loadCheques()
  } catch (e) {
    alert('Failed to cancel cheque: ' + e.message)
  }
}

function isPostDated(chq) {
  return chq.status === 'Pending' && chq.cheque_date > today()
}

function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>
