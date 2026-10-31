<template>
  <!-- Keys the panel owns stop here: the SalesInvoice shortcuts listen on window,
       and its Escape would otherwise leave the page from inside the cash box -->
  <aside
    class="flex w-[360px] shrink-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)] overflow-y-auto"
    @keydown="handleKeydown"
  >
    <div class="p-4 space-y-3">
      <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] flex items-center gap-2">
        <div class="h-1.5 w-1.5 rounded-full bg-[var(--color-highlight)]"></div>
        Payment
        <span class="ml-auto font-mono normal-case tracking-normal text-[11px]">F9</span>
      </h3>

      <!-- UPI queue: this user's screen QR, phone pay link and machine requests, waiting or paid; click
           opens the bill, whose popup is the only place a waiting request is cancelled -->
      <div v-if="qrQueue.length" class="space-y-1">
        <div class="flex items-center justify-between px-1 text-[11px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">
          <span>UPI Queue</span>
          <span>{{ qrQueue.filter(q => q.status === 'Pending').length }} waiting</span>
        </div>
        <div class="max-h-48 space-y-1 overflow-y-auto">
          <button
            v-for="q in qrQueue"
            :key="q.order_id"
            type="button"
            tabindex="-1"
            @click="openQueuedBill(q)"
            class="flex w-full min-w-0 items-center justify-between gap-2 rounded-lg border px-2 py-1 text-left transition-all active:scale-[0.98]"
            :class="q.status === 'Success'
              ? 'bg-[var(--color-success)]/30 border-[var(--color-success)]/50 text-[var(--color-text)]'
              : invoice?.name === q.sales_invoice
                ? 'bg-[var(--color-info)]/20 border-[var(--color-info)]/40 text-[var(--color-text)]'
                : 'bg-[var(--color-bg)] border-[var(--color-border)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]'"
          >
            <div class="min-w-0">
              <div class="truncate text-[13px] font-black">{{ q.customer_name || q.customer }}</div>
              <div class="truncate text-[10px] font-bold opacity-70">{{ q.sales_invoice }} · {{ q.customer_mobile || (q.channel === 'EDC' ? 'Machine' : 'Screen QR') }}</div>
            </div>
            <div class="shrink-0 text-right">
              <div class="font-mono text-[15px] font-black">₹{{ fmt(q.amount) }}</div>
              <div class="text-[9px] font-black uppercase tracking-widest" :class="q.status === 'Success' ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'">{{ q.status === 'Success' ? 'Paid' : 'Waiting' }}</div>
            </div>
          </button>
        </div>
      </div>

      <!-- Last settled bill stays visible until the next one comes in -->
      <div
        v-if="lastSettled && !invoice"
        class="rounded-xl border border-[var(--color-success)] bg-[var(--color-success)]/15 p-4 text-center"
      >
        <div class="text-[11px] font-black uppercase tracking-widest text-[var(--color-success)]">Settled</div>
        <div class="font-mono text-sm font-bold text-[var(--color-text)] mt-1">{{ lastSettled.name }}</div>
        <div v-if="lastSettled.change > 0" class="mt-2">
          <div class="text-[11px] font-black uppercase tracking-widest text-[var(--color-danger)]">Change Return</div>
          <div class="font-mono text-[36px] font-black text-[var(--color-danger)]">₹{{ fmt(lastSettled.change) }}</div>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-highlight)] border-t-transparent"></div>
      </div>

      <div v-else-if="!invoice" class="flex h-48 items-center justify-center text-center">
        <p class="px-6 text-xs font-bold leading-relaxed text-[var(--color-text-muted)]">
          Save the bill (F8) or pick a draft from the bill list to take payment
        </p>
      </div>

      <template v-else>
        <!-- Summary -->
        <div class="relative rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] p-4">
          <div class="flex items-start justify-between">
            <div class="min-w-0">
              <div class="truncate font-mono text-xs font-bold text-[var(--color-text-muted)]">{{ invoice.name }}</div>
              <div class="truncate text-sm font-bold text-[var(--color-text)]">{{ invoice.customer_name || invoice.customer }}</div>
            </div>
            <span
              class="shrink-0 rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest"
              :class="isCredit
                ? 'bg-[var(--color-danger)]/40 border-[var(--color-danger)] text-[var(--color-danger)]'
                : 'bg-[var(--color-success)]/30 border-[var(--color-success)] text-[var(--color-success)]'"
            >{{ isCredit ? 'Credit' : 'Cash' }}</span>
          </div>
          <div class="mt-2 text-[12px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Bill Amount</div>
          <div class="font-mono text-[34px] font-black tracking-tight text-[var(--color-text)]">₹{{ fmt(amountToCollect) }}</div>
          <div class="mt-2 space-y-1 border-t border-[var(--color-border)] pt-2">
            <div class="flex items-center justify-between">
              <span class="text-[15px] font-bold text-[var(--color-text-muted)]">Paid</span>
              <span class="font-mono text-[15px] font-bold text-[var(--color-text)]">₹{{ fmt(totalPaid) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[15px] font-bold uppercase tracking-widest" :class="balance <= 0.01 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                {{ balance <= 0.01 ? 'Change' : 'Balance' }}
              </span>
              <span class="font-mono text-[26px] font-black" :class="balance <= 0.01 ? 'text-[var(--color-danger)]' : 'text-[var(--color-info)]'">
                ₹{{ fmt(Math.abs(balance)) }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="alreadySettled" class="rounded-xl border border-[var(--color-success)] bg-[var(--color-success)]/15 p-3 text-center text-xs font-black uppercase tracking-widest text-[var(--color-success)]">
          {{ invoice.docstatus === 2 ? 'Cancelled bill' : 'Already settled' }}
        </div>

        <template v-else>
          <!-- Mode -->
          <div class="flex gap-2">
            <button
              type="button"
              @click="toggleCredit(false)"
              :disabled="isSecondaryParty || invoice.is_return"
              class="flex-1 rounded-xl border py-1.5 text-[15px] font-black uppercase tracking-widest transition-all disabled:cursor-not-allowed disabled:opacity-30"
              :class="!isCredit ? 'bg-[var(--color-success)]/30 border-[var(--color-success)] text-[var(--color-success)]' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-muted)]'"
              :title="isSecondaryParty ? 'Secondary parties can only process Credit Sales' : (invoice.is_return ? 'Sales returns can only be processed as Credit' : '')"
            >Cash Bill</button>
            <button
              type="button"
              @click="toggleCredit(true)"
              class="flex-1 rounded-xl border py-1.5 text-[15px] font-black uppercase tracking-widest transition-all"
              :class="isCredit ? 'bg-[var(--color-danger)]/40 border-[var(--color-danger)] text-[var(--color-danger)]' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-muted)]'"
            >Credit</button>
          </div>

          <template v-if="!isCredit">
            <div class="relative">
              <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">{{ cashLabel }}</div>
              <input
                ref="cashInput"
                type="number"
                step="0.01"
                v-model="payments.cash"
                @input="cashAuto = false"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-24 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/20"
              />
            </div>
            <!-- Tendered notes: cash above the bill shows as change and is capped to the bill on posting -->
            <div class="grid grid-cols-4 gap-1.5">
              <button
                v-for="q in quickCash"
                :key="q.label"
                type="button"
                tabindex="-1"
                @click="cashAuto = false; payments.cash = q.value; cashInput?.focus()"
                class="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] py-1 font-mono text-[13px] font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]"
              >{{ q.label }}</button>
            </div>
            <div class="relative flex items-center">
              <div :ref="bindUpiOverlay" class="absolute left-4 top-1/2 z-10 flex -translate-y-1/2 items-center gap-2 whitespace-nowrap">
                <span class="text-[16px] font-black uppercase text-[var(--color-text-muted)]">{{ upiLabel }}</span>
                <button
                  v-if="upiWaiting"
                  @click="openQueuedBill(upiWaiting)"
                  type="button"
                  tabindex="-1"
                  title="Open the waiting UPI request; cancel it there to change the UPI amount"
                  class="rounded-lg bg-[var(--color-warning)] px-2 py-1 text-[13px] font-black uppercase tracking-wider text-white shadow-sm hover:opacity-90 active:scale-95"
                >Waiting</button>
                <button
                  v-if="hasPaytmMachine && !upiLocked && !upiWaiting"
                  @click="openPaytmModal('QR')"
                  type="button"
                  tabindex="-1"
                  title="Show the UPI QR for this amount on the Paytm machine"
                  class="rounded-lg bg-[var(--color-success)] px-2 py-1 text-[13px] font-black uppercase tracking-wider text-white shadow-sm hover:opacity-90 active:scale-95"
                >UPI</button>
                <button
                  v-if="paytm.qrEnabled && !upiLocked && !upiWaiting"
                  @click="openPaytmQr"
                  type="button"
                  tabindex="-1"
                  title="Send the UPI pay QR for this amount to the customer's WhatsApp"
                  class="rounded-lg bg-[var(--color-info)] px-2 py-1 text-white shadow-sm hover:opacity-90 active:scale-95"
                ><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg></button>
              </div>
              <input
                ref="upiInput"
                type="number"
                step="0.01"
                v-model="payments.upi"
                :readonly="upiLocked || !!upiWaiting"
                :title="upiLocked ? 'Received through Paytm — locked' : upiWaiting ? 'Waiting for the UPI QR — cancel it to change' : ''"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] read-only:cursor-not-allowed read-only:border-[var(--color-success)]/50 read-only:bg-[var(--color-success)]/10 focus:border-[var(--color-success)] focus:ring-4 focus:ring-[var(--color-success)]/20"
                :style="{ paddingLeft: `${upiInputPad}px` }"
              />
            </div>
            <!-- Saved as the UPI Payment Entry's Reference No; Paytm fills it on a machine payment -->
            <input
              v-if="Number(payments.upi) > 0"
              v-model.trim="upiRefNo"
              :readonly="upiLocked || !!upiWaiting"
              type="text"
              tabindex="-1"
              placeholder="UPI Ref No (optional)"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-1.5 text-right font-mono text-[14px] font-bold text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] outline-none read-only:cursor-not-allowed read-only:bg-[var(--color-success)]/10 focus:border-[var(--color-success)]"
            />
            <div class="relative flex items-center">
              <div :ref="bindCardOverlay" class="absolute left-4 top-1/2 z-10 flex -translate-y-1/2 items-center gap-2 whitespace-nowrap">
                <span class="text-[16px] font-black uppercase text-[var(--color-text-muted)]">{{ cardLabel }}</span>
                <button
                  v-if="hasPaytmMachine && !cardLocked"
                  @click="openPaytmModal('CARD')"
                  type="button"
                  tabindex="-1"
                  title="Take a card payment for this amount on the Paytm machine"
                  class="rounded-lg bg-[var(--color-info)] px-2 py-1 text-[13px] font-black uppercase tracking-wider text-white shadow-sm hover:opacity-90 active:scale-95"
                >Card</button>
              </div>
              <input
                ref="cardInput"
                type="number"
                step="0.01"
                v-model="payments.card"
                :readonly="cardLocked"
                :title="cardLocked ? 'Received through Paytm — locked' : ''"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] read-only:cursor-not-allowed read-only:border-[var(--color-success)]/50 read-only:bg-[var(--color-success)]/10 focus:border-[var(--color-info)] focus:ring-4 focus:ring-[var(--color-info)]/20"
                :style="{ paddingLeft: `${cardInputPad}px` }"
              />
            </div>
            <!-- Required for a card payment: saved as the Card Payment Entry's Reference No -->
            <input
              v-if="Number(payments.card) > 0"
              ref="cardRefInput"
              v-model.trim="cardRefNo"
              :readonly="cardLocked"
              type="text"
              placeholder="Card Ref No (required)"
              class="w-full rounded-xl border bg-[var(--color-bg)] px-4 py-1.5 text-right font-mono text-[14px] font-bold text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] outline-none focus:border-[var(--color-info)]"
              :class="cardRefNo ? 'border-[var(--color-border)]' : 'border-[var(--color-danger)]'"
            />
            <div class="relative">
              <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">Credit</div>
              <input
                ref="creditInput"
                type="number"
                step="0.01"
                v-model="payments.credit"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-24 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] focus:border-[var(--color-danger)] focus:ring-4 focus:ring-[var(--color-danger)]/20"
              />
            </div>
            <div class="relative">
              <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">{{ discountLabel }}</div>
              <input
                ref="discountInput"
                type="number"
                step="0.01"
                v-model="payments.discount"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-24 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] focus:border-[var(--color-warning)] focus:ring-4 focus:ring-amber-500/20"
              />
            </div>
          </template>

          <div v-else class="rounded-xl border border-[var(--color-danger)]/60 bg-[var(--color-danger)]/20 p-3">
            <label class="mb-1.5 block text-[13px] font-black uppercase tracking-widest text-[var(--color-danger)]">Promise Date (Due Date)</label>
            <div class="relative">
              <input
                ref="dueDateInput"
                type="text"
                v-model="dueDate"
                @input="handleDueDateInput"
                @keydown.backspace="handleDueDateKeyDown"
                placeholder="DDMM or DD/MM/YYYY"
                class="w-full rounded-2xl border border-[var(--color-danger)]/50 bg-[var(--color-bg)] py-3 pl-4 pr-12 text-center font-mono text-[20px] font-black text-[var(--color-text)] placeholder-[var(--color-text-muted)] outline-none focus:border-[var(--color-danger)]"
              />
              <div class="absolute right-2 top-1/2 -translate-y-1/2">
                <DatePickerButton :model-value="dueDate ? getIsoDueDate() : ''" label="Choose promise date" @update:model-value="dueDate = $event ? $event.split('-').reverse().join('/') : ''" />
              </div>
            </div>
          </div>

          <div class="relative">
            <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">Remarks</div>
            <input
              ref="remarksInput"
              type="text"
              v-model="payments.remarks"
              @focus="$event.target.select()"
              class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-28 pr-4 text-right font-mono text-[18px] font-black text-[var(--color-text)] focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/20"
            />
          </div>

          <p v-if="errorMsg" class="text-[12px] font-bold text-[var(--color-danger)]">{{ errorMsg }}</p>

          <button
            ref="postButton"
            type="button"
            @click="processPayment"
            :disabled="!canSubmit"
            class="w-full rounded-xl py-4 text-sm font-black uppercase tracking-[0.2em] transition-all active:scale-95 focus:outline-none disabled:pointer-events-none disabled:opacity-30"
            :class="isCredit
              ? 'bg-[var(--color-danger)] border-2 border-[var(--color-danger)] text-[var(--color-text-on-highlight)] hover:brightness-110'
              : 'border-2 border-[var(--color-success)] text-[var(--color-success)] hover:bg-[var(--color-success)]/10 focus:bg-[var(--color-success)] focus:text-[var(--color-text-on-highlight)]'"
          >
            <span v-if="isSubmitting">Processing...</span>
            <span v-else>{{ isCredit ? 'Post Credit Sale' : 'Post Settlement' }} (F9)</span>
          </button>
        </template>
      </template>
    </div>

    <!-- PAYTM MACHINE MODAL (UPI QR on the machine, or card) -->
    <div v-if="paytm.show" class="fixed inset-0 z-50 flex items-center justify-center bg-[var(--color-bg)]/80 p-4 backdrop-blur-sm">
      <div class="w-full max-w-md overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl">
        <div class="flex items-center justify-between border-b border-[var(--color-border)] p-5">
          <h3 class="text-sm font-bold uppercase tracking-widest text-[var(--color-text)]">Paytm Machine · {{ paytm.payMode === 'CARD' ? 'Card' : 'UPI' }}</h3>
          <button @click="dismissPaytmModal" :title="paytm.orderId && paytm.status === 'Pending' && paytm.payMode === 'QR' ? 'Keep waiting in the UPI queue' : 'Close'" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button>
        </div>
        <div class="space-y-5 p-6">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Amount</span>
            <span class="font-mono text-[24px] font-black text-[var(--color-text)]">₹{{ fmt(paytm.amount) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Machine</span>
            <span class="font-bold text-[var(--color-text)]">{{ paytm.deviceName }} ({{ paytm.tid }})</span>
          </div>
          <div v-if="paytm.customerName" class="flex items-center justify-between">
            <span class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Customer</span>
            <span class="font-bold text-[var(--color-text)]">{{ paytm.customerName }}<template v-if="paytm.phone && !paytm.askPhone"> · {{ paytm.phone }}</template></span>
          </div>
          <!-- The bill has no real number (e.g. 9999999999): the cashier may add one, or skip it -->
          <input
            v-if="paytm.askPhone && !paytm.orderId"
            ref="paytmPhoneInput"
            v-model.trim="paytm.phone"
            @keydown.enter="sendToPaytm"
            type="tel"
            maxlength="13"
            placeholder="Customer phone (optional)"
            class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 font-mono font-bold text-[var(--color-text)] outline-none placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-info)]"
          />
          <div
            v-if="paytm.message"
            class="rounded-lg border p-3 text-[12px] font-bold uppercase tracking-wider"
            :class="statusClass(paytm.status)"
          >{{ paytm.message }}</div>
          <div class="flex gap-3">
            <button
              @click="closePaytmModal"
              :disabled="paytm.sending"
              class="flex-1 rounded-xl py-3 text-xs font-bold uppercase tracking-widest transition-all active:scale-95 disabled:pointer-events-none disabled:opacity-40"
              :class="paytm.orderId && paytm.status === 'Pending'
                ? 'bg-[var(--color-danger)]/15 text-[var(--color-danger)] hover:bg-[var(--color-danger)]/25'
                : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-border)]'"
            >{{ paytm.orderId && paytm.status === 'Pending' ? 'Cancel' : 'Close' }}</button>
            <button
              v-if="paytm.orderId && paytm.status === 'Pending' && paytm.payMode === 'QR'"
              @click="queuePaytmMachine"
              title="Keep waiting in the UPI queue and take the next bill"
              class="flex-1 rounded-xl bg-[var(--color-info)] py-3 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all active:scale-95"
            >Queue</button>
            <button
              v-if="paytm.status === 'Failed' || (paytm.askPhone && !paytm.orderId)"
              @click="sendToPaytm"
              :disabled="paytm.sending"
              class="flex-1 rounded-xl bg-[var(--color-info)] py-3 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all active:scale-95 disabled:pointer-events-none disabled:opacity-40"
            >{{ paytm.sending ? 'Sending…' : paytm.status === 'Failed' ? 'Retry' : 'Send to Machine' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- PAYTM DYNAMIC QR MODAL (phone button: QR on screen, sent to WhatsApp) -->
    <div v-if="paytmQr.show" class="fixed inset-0 z-50 flex items-center justify-center bg-[var(--color-bg)]/80 p-4 backdrop-blur-sm">
      <div class="w-full max-w-md overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl">
        <div class="flex items-center justify-between border-b border-[var(--color-border)] p-5">
          <h3 class="text-sm font-bold uppercase tracking-widest text-[var(--color-text)]">Paytm UPI QR</h3>
          <button @click="dismissPaytmQr" :title="paytmQr.orderId && paytmQr.status === 'Pending' ? 'Keep waiting in the UPI queue' : 'Close'" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button>
        </div>
        <div class="space-y-5 p-6">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Amount</span>
            <span class="font-mono text-[24px] font-black text-[var(--color-text)]">₹{{ fmt(paytmQr.amount) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Machine</span>
            <span class="font-mono text-[12px] font-bold text-[var(--color-text)]">TID {{ paytmQr.tid || '—' }} · POS ID {{ paytmQr.posId || '—' }}</span>
          </div>
          <!-- WhatsApp number (saved WhatsApp, else mobile); the QR is created on Send -->
          <div v-if="!paytmQr.orderId && !paytmQr.sending" class="space-y-1">
            <label class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">WhatsApp number<template v-if="waSessionName"> · from {{ waSessionName }}</template></label>
            <input
              ref="paytmQrPhoneInput"
              v-model.trim="paytmQr.phone"
              @keydown.enter="createPaytmQr(false)"
              maxlength="14"
              placeholder="WhatsApp / mobile"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-2 font-mono text-[20px] font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            />
          </div>
          <div v-else-if="paytmQr.phone" class="flex items-center justify-between">
            <span class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">WhatsApp<template v-if="waSessionName"> · {{ waSessionName }}</template></span>
            <span class="text-[12px] font-bold" :class="paytmQr.waOk === false ? 'text-[var(--color-danger)]' : paytmQr.waOk ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]'">
              {{ paytmQr.waSending ? `Sending to +91 ${paytmQr.phone}…` : paytmQr.waText || `+91 ${paytmQr.phone}` }}
            </span>
          </div>
          <!-- print template of the bill PDF that Bill + QR sends; defaults to the bill series' -->
          <div v-if="!paytmQr.orderId && !paytmQr.sending && billFormat.list.length" class="space-y-1">
            <label class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Bill format · for Bill + QR</label>
            <select
              v-model="billFormat.selected"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-2 text-[14px] font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            >
              <option v-for="t in billFormat.list" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="flex items-center justify-center">
            <!-- white backing so the code scans in dark mode too -->
            <img v-if="paytmQr.image && paytmQr.status !== 'Failed'" :src="paytmQrSrc" alt="Paytm UPI QR" class="h-64 w-64 rounded-xl bg-white p-2" :class="paytmQr.status === 'Success' ? 'opacity-30' : ''" />
            <div v-else-if="paytmQr.sending" class="flex h-64 w-64 items-center justify-center text-[12px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Creating QR…</div>
          </div>
          <div
            v-if="paytmQr.message"
            class="rounded-lg border p-3 text-[12px] font-bold uppercase tracking-wider"
            :class="statusClass(paytmQr.status)"
          >{{ paytmQr.message }}</div>
          <div class="flex gap-3">
            <button
              @click="paytmQr.orderId && paytmQr.status === 'Pending' ? closePaytmQr() : dismissPaytmQr()"
              :title="paytmQr.orderId && paytmQr.status === 'Pending' ? 'Cancel this QR and free the bill' : ''"
              class="flex-1 rounded-xl py-3 text-xs font-bold uppercase tracking-widest transition-all active:scale-95"
              :class="paytmQr.orderId && paytmQr.status === 'Pending'
                ? 'bg-[var(--color-danger)]/15 text-[var(--color-danger)] hover:bg-[var(--color-danger)]/25'
                : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-border)]'"
            >{{ paytmQr.orderId && paytmQr.status === 'Pending' ? 'Cancel QR' : 'Close' }}</button>
            <template v-if="!paytmQr.orderId && paytmQr.status !== 'Failed'">
              <button
                @click="createPaytmQr(true)"
                :disabled="paytmQr.sending || !paytmQr.phone"
                title="Send the bill PDF, then the pay QR picture"
                class="flex-1 rounded-xl bg-[var(--color-info)] py-3 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all active:scale-95 disabled:pointer-events-none disabled:opacity-40"
              >{{ paytmQr.sending && paytmQr.withBill ? 'Creating…' : 'Bill + QR' }}</button>
              <button
                @click="createPaytmQr(false)"
                :disabled="paytmQr.sending"
                :title="paytmQr.phone ? 'Send only the pay QR picture (Enter)' : 'Show the QR without sending'"
                class="flex-1 rounded-xl bg-[var(--color-success)] py-3 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all active:scale-95 disabled:pointer-events-none disabled:opacity-40"
              >{{ paytmQr.sending && !paytmQr.withBill ? 'Creating…' : paytmQr.phone ? 'Only QR' : 'Show QR' }}</button>
            </template>
            <button
              v-if="paytmQr.orderId && paytmQr.status === 'Pending'"
              @click="queuePaytmQr"
              title="Keep waiting in the UPI queue and take the next bill"
              class="flex-1 rounded-xl bg-[var(--color-info)] py-3 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all active:scale-95"
            >Queue</button>
            <button
              v-if="paytmQr.orderId && paytmQr.status === 'Pending' && paytmQr.phone && paytmQr.waOk !== undefined"
              @click="sendPaytmQrLink"
              :disabled="paytmQr.waSending"
              class="flex-1 rounded-xl bg-[var(--color-success)] py-3 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all active:scale-95 disabled:pointer-events-none disabled:opacity-40"
            >{{ paytmQr.waOk ? 'Send Again' : 'Retry Send' }}</button>
            <button
              v-if="paytmQr.status === 'Failed'"
              @click="createPaytmQr()"
              :disabled="paytmQr.sending"
              class="flex-1 rounded-xl bg-[var(--color-info)] py-3 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all active:scale-95 disabled:pointer-events-none disabled:opacity-40"
            >{{ paytmQr.sending ? 'Creating…' : 'New QR' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- PAYMENT RECEIVED BIG TICK (UPI / CARD) -->
    <transition name="fade">
      <div v-if="paidTick.show" class="pointer-events-none fixed inset-0 z-[120] flex items-center justify-center bg-[var(--color-bg)]/60">
        <div class="paid-tick-pop flex flex-col items-center gap-4">
          <div class="flex h-56 w-56 items-center justify-center rounded-full bg-[var(--color-success)] shadow-2xl shadow-[var(--color-success)]/40">
            <svg viewBox="0 0 52 52" class="h-36 w-36 text-white" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
              <path class="paid-tick-path" d="M14 27 l8 8 l16 -18" />
            </svg>
          </div>
          <div class="font-mono text-[40px] font-black leading-none text-[var(--color-success)]">₹{{ fmt(paidTick.amount) }}</div>
          <div class="text-[18px] font-black uppercase tracking-widest text-[var(--color-text)]">Received by {{ paidTick.mode === 'card' ? 'Card' : 'UPI' }}</div>
          <div v-if="paidTick.label" class="text-[16px] font-bold text-[var(--color-text-muted)]">{{ paidTick.label }}</div>
        </div>
      </div>
    </transition>

    <component
      :is="ConfettiTester"
      v-if="ConfettiTester"
      :paytm-mock="paytmMockOn"
      :whatsapp-mock="whatsappMockOn"
      @mock-upi="settleMock('Success')"
      @mock-fail="settleMock('Failed')"
      @toggle-paytm-mock="togglePaytmMock"
      @toggle-whatsapp-mock="setWhatsAppMock(!whatsappMockOn)"
    />
  </aside>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted, defineAsyncComponent } from 'vue'
import DatePickerButton from './DatePickerButton.vue'
import { getInvoiceDetails, submitInvoiceWithPayment, fetchDashboardSettings, frappeGet, frappePost } from '../api.js'
import { useLedgerCache } from '../services/ledgerCache'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { session, getWhatsAppSessionId, getWhatsAppSessionName } from '../session'
import { getFrappeSocket } from '../services/frappeSocket.js'
import { fireConfetti } from '../utils/confetti'
import { paytmMockOn, whatsappMockOn, setPaytmMock, setWhatsAppMock, devCall, settleMockOrder } from '../utils/devMock'
import { canModifyDate } from '../composables/usePermission'
import { serverToday, serverCalendarDate } from '../services/serverTime'

const ConfettiTester = import.meta.env.DEV ? defineAsyncComponent(() => import('./ConfettiTester.vue')) : null

const props = defineProps({
  // bill in view on the POS screen; null when a new bill is being entered
  invoiceName: { type: String, default: null },
  // bumped when the same bill is saved again, so its new totals are fetched
  reloadKey: { type: Number, default: 0 },
})

// open-bill: a UPI queue row asks the page to bring its bill into view
const emit = defineEmits(['settled', 'back', 'loaded', 'open-bill'])

const invoice = ref(null)
const loading = ref(false)
const isSubmitting = ref(false)
const errorMsg = ref('')
const isCredit = ref(false)
const dueDate = ref('')
const upiRefNo = ref('')
const cardRefNo = ref('')
const lastSettled = ref(null)
// cash was filled with the bill amount by us, not typed: it shrinks as other modes are entered
const cashAuto = ref(false)
const payments = ref({ cash: 0, upi: 0, card: 0, credit: 0, discount: 0, remarks: '' })
const seriesAccounts = ref({ cash: '', upi: '', card: '', discount: '' })

const cashInput = ref(null)
const upiInput = ref(null)
const cardInput = ref(null)
const cardRefInput = ref(null)
const creditInput = ref(null)
const discountInput = ref(null)
const remarksInput = ref(null)
const dueDateInput = ref(null)
const postButton = ref(null)

const { partyLinks } = useLedgerCache()

function getTodayIST() {
  return serverToday()
}

function fmt(val) {
  return (Number(val) || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function glLabel(key, fallback) {
  const acc = localStorage.getItem(key) || ''
  return acc ? acc.split(' - ')[0].trim() : fallback
}
const cashLabel = computed(() => glLabel('wb-cash', 'Cash'))
const upiLabel = computed(() => glLabel('wb-upi', 'UPI'))
const cardLabel = computed(() => glLabel('wb-card', 'Card'))
const discountLabel = computed(() => {
  const acc = seriesAccounts.value.discount || localStorage.getItem('wb-discount-account') || ''
  return acc ? acc.split(' - ')[0].trim() : 'Disc'
})

const isSecondaryParty = computed(() => {
  if (!invoice.value?.customer) return false
  return partyLinks.value[invoice.value.customer]?.is_secondary || false
})

const amountToCollect = computed(() => {
  if (!invoice.value) return 0
  const gt = Number(invoice.value.rounded_total || invoice.value.grand_total || 0)
  const os = invoice.value.outstanding_amount !== undefined && invoice.value.outstanding_amount !== null
    ? Number(invoice.value.outstanding_amount)
    : gt
  if (invoice.value.docstatus === 1) return os
  return os < gt ? os : gt
})

const totalPaid = computed(() => {
  const p = payments.value
  const sum = (Number(p.cash) || 0) + (Number(p.upi) || 0) + (Number(p.card) || 0) + (Number(p.credit) || 0) + (Number(p.discount) || 0)
  return parseFloat(sum.toFixed(2))
})

const balance = computed(() => parseFloat((amountToCollect.value - totalPaid.value).toFixed(2)))

const changeAmount = computed(() => {
  const p = payments.value
  const money = (Number(p.cash) || 0) + (Number(p.upi) || 0) + (Number(p.card) || 0)
  const net = amountToCollect.value - (Number(p.discount) || 0) - (Number(p.credit) || 0)
  const change = money - net
  return change > 0.005 ? parseFloat(change.toFixed(2)) : 0
})

const alreadySettled = computed(() => {
  if (!invoice.value) return false
  if (invoice.value.docstatus === 2) return true
  return invoice.value.docstatus === 1 && (invoice.value.outstanding_amount || 0) <= 0.01
})

const canSubmit = computed(() => {
  if (!invoice.value || isSubmitting.value || alreadySettled.value) return false
  if (invoice.value.is_return && !isCredit.value) return false
  if (isCredit.value) return true
  return balance.value <= 0.01
})

// Exact amount plus the next notes up from it
const quickCash = computed(() => {
  const due = Math.ceil(amountToCollect.value)
  const out = [{ label: 'Exact', value: amountToCollect.value }]
  for (const step of [100, 500, 2000]) {
    const v = Math.ceil(due / step) * step
    if (v > due && !out.some(o => o.value === v)) out.push({ label: String(v), value: v })
  }
  return out.slice(0, 4)
})

// Billing settings depend on the user, not the bill: fetch once
let billingSettingsPromise = null
function getBillingSettingsCached() {
  if (!billingSettingsPromise) {
    const targetUser = localStorage.getItem('wb-inherited-user') || null
    billingSettingsPromise = fetchDashboardSettings(targetUser).catch(e => {
      billingSettingsPromise = null
      throw e
    })
  }
  return billingSettingsPromise
}

async function loadSeriesSettings(series) {
  try {
    const lsCash = localStorage.getItem('wb-cash')
    const lsUpi = localStorage.getItem('wb-upi')
    const lsCard = localStorage.getItem('wb-card')
    const settings = await getBillingSettingsCached()
    // Server resolves discount_account against wb-company
    const discountAccount = settings.discount_account || ''
    const seriesConfig = (settings.billing_series || []).find(s => s.series === series)
    const defaults = (lsCash || lsUpi || lsCard)
      ? { cash: lsCash, upi: lsUpi, card: lsCard }
      : (settings.user_defaults || {})
    seriesAccounts.value = {
      cash: defaults.cash || seriesConfig?.cash_account || 'Cash',
      upi: defaults.upi || seriesConfig?.upi || 'UPI',
      card: defaults.card || seriesConfig?.card || 'Card',
      discount: discountAccount,
    }
  } catch (e) {
    console.warn('Could not load accounts', e)
  }
}

let loadSeq = 0
async function loadInvoice(name) {
  const seq = ++loadSeq
  errorMsg.value = ''
  isCredit.value = false
  cashAuto.value = false
  dueDate.value = ''
  upiRefNo.value = ''
  cardRefNo.value = ''
  payments.value = { cash: 0, upi: 0, card: 0, credit: 0, discount: 0, remarks: '' }
  if (!name) {
    invoice.value = null
    return
  }
  loading.value = true
  try {
    const details = await getInvoiceDetails(name)
    if (seq !== loadSeq) return
    invoice.value = details
    lastSettled.value = null
    await loadSeriesSettings(details.naming_series)
    if (seq !== loadSeq) return
    // submit writes the box back to custom_remarks, so start from the saved remark
    payments.value.remarks = details.custom_remarks || ''
    // cash box starts empty: the cashier types the amount tendered
    if (details.is_return || isSecondaryParty.value || details.mop === 'Credit') {
      isCredit.value = true
    }
    loading.value = false
    resumeQueued(name)
    emit('loaded', name)
  } catch (e) {
    if (seq === loadSeq) {
      invoice.value = null
      errorMsg.value = 'Failed to load bill: ' + e.message
    }
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

watch(() => [props.invoiceName, props.reloadKey], () => loadInvoice(props.invoiceName), { immediate: true })

function toggleCredit(val) {
  if (val && (upiLocked.value || cardLocked.value)) {
    errorMsg.value = "A Paytm payment is already received on this bill; it can't be switched to Credit."
    return
  }
  if (!val && isSecondaryParty.value) {
    errorMsg.value = 'Secondary parties can only process Credit Sales.'
    return
  }
  if (!val && invoice.value?.is_return) {
    errorMsg.value = 'Sales returns can only be processed as Credit.'
    return
  }
  isCredit.value = val
  cashAuto.value = false
  errorMsg.value = ''
  const keptRemarks = payments.value.remarks || ''
  payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: keptRemarks }
  nextTick(() => (isCredit.value ? dueDateInput.value : cashInput.value)?.focus())
}

watch(() => [payments.value.upi, payments.value.card, payments.value.credit, payments.value.discount], () => {
  if (!cashAuto.value || isCredit.value) return
  const p = payments.value
  const others = (Number(p.upi) || 0) + (Number(p.card) || 0) + (Number(p.credit) || 0) + (Number(p.discount) || 0)
  p.cash = parseFloat(Math.max(0, amountToCollect.value - others).toFixed(2))
})

function handleDueDateKeyDown(e) {
  if (e.key === 'Backspace' && dueDate.value) {
    dueDate.value = ''
    e.preventDefault()
  }
}

function handleDueDateInput(e) {
  let raw = e.target.value.replace(/\D/g, '')
  if (raw.length > 8) raw = raw.slice(0, 8)
  // Quick entry for ddmm (4 digits)
  if (raw.length === 4) {
    dueDate.value = `${raw.slice(0, 2)}/${raw.slice(2, 4)}/${serverCalendarDate().getFullYear()}`
    return
  }
  let formatted = raw
  if (raw.length >= 5) formatted = raw.slice(0, 2) + '/' + raw.slice(2, 4) + '/' + raw.slice(4)
  else if (raw.length >= 3) formatted = raw.slice(0, 2) + '/' + raw.slice(2)
  dueDate.value = formatted
}

function getIsoDueDate() {
  if (!dueDate.value || !dueDate.value.includes('/')) {
    if (dueDate.value.match(/^\d{4}-\d{2}-\d{2}$/)) return dueDate.value
    return getTodayIST()
  }
  const parts = dueDate.value.split('/')
  if (parts.length !== 3) return getTodayIST()
  const [dd, mm, yyyy] = parts
  return `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`
}

async function processPayment() {
  if (!canSubmit.value) return
  errorMsg.value = ''
  if (import.meta.env.DEV && [upiRefNo.value, cardRefNo.value].some(r => String(r || '').startsWith('MOCK-'))) {
    errorMsg.value = 'This bill has a mock Paytm payment; reload the page before posting.'
    return
  }

  if (Number(payments.value.card) > 0.01 && !cardRefNo.value) {
    errorMsg.value = 'Enter the card reference number.'
    nextTick(() => cardRefInput.value?.focus())
    return
  }

  const bill = amountToCollect.value
  const upi = Number(payments.value.upi) || 0
  const card = Number(payments.value.card) || 0
  const disc = Number(payments.value.discount) || 0
  const credit = Number(payments.value.credit) || 0
  let cash = Number(payments.value.cash) || 0
  // overpaid: the excess is change handed back, so cash is reduced to fit the bill
  if (cash + upi + card + disc + credit > bill + 0.005) {
    cash = Math.max(0, bill - upi - card - disc - credit)
  }

  let finalDueDate = getIsoDueDate()
  const today = getTodayIST()
  if (finalDueDate < today) finalDueDate = today

  const name = invoice.value.name
  const change = changeAmount.value
  isSubmitting.value = true
  try {
    await submitInvoiceWithPayment({
      invoice_name: name,
      cash_amount: cash,
      upi_amount: upi,
      card_amount: card,
      discount_amount: disc,
      credit_amount: credit,
      is_credit: isCredit.value,
      due_date: finalDueDate,
      // the bill's own date, which the biller could only move with date permission
      posting_date: canModifyDate() ? (invoice.value.posting_date || today) : today,
      card_ref_no: cardRefNo.value,
      upi_ref_no: upiRefNo.value,
      cash_account: seriesAccounts.value.cash,
      upi_account: seriesAccounts.value.upi,
      card_account: seriesAccounts.value.card,
      discount_account: seriesAccounts.value.discount,
      custom_remarks: payments.value.remarks,
      cost_center: localStorage.getItem('wb-cost-center') || null,
    })
    lastSettled.value = { name, change }
    invoice.value = null
    qrQueue.value = qrQueue.value.filter(q => q.sales_invoice !== name)
    emit('settled', name)
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    isSubmitting.value = false
  }
}

function inputOrder() {
  const order = isCredit.value
    ? [dueDateInput, remarksInput]
    : [cashInput, upiInput, cardInput, cardRefInput, creditInput, discountInput, remarksInput]
  return order.map(r => r.value).filter(Boolean)
}

function handleKeydown(e) {
  if (paytm.value.show || paytmQr.value.show) {
    e.stopPropagation()
    if (e.key === 'Escape') {
      e.preventDefault()
      if (paytm.value.show) dismissPaytmModal()
      else dismissPaytmQr()
    }
    return
  }
  if (e.key === 'F9') {
    e.preventDefault()
    e.stopPropagation()
    processPayment()
    return
  }
  if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    emit('back')
    return
  }
  // Up / Down walk the boxes (and the Post button) instead of stepping number values;
  // read-only boxes (UPI / Card locked by Paytm or a waiting request) are skipped
  if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
    e.stopPropagation()
    const fields = [...inputOrder(), ...(canSubmit.value ? [postButton.value] : [])]
      .filter(el => el === e.target || !el.readOnly)
    const idx = fields.indexOf(e.target)
    if (idx === -1) return
    e.preventDefault()
    fields[idx + (e.key === 'ArrowDown' ? 1 : -1)]?.focus()
    return
  }
  if (e.key === 'Enter') {
    e.stopPropagation()
    const fields = inputOrder()
    const idx = fields.indexOf(e.target)
    if (idx === -1) return
    e.preventDefault()
    // a fully paid bill skips the remaining boxes
    if (idx === fields.length - 1 || (!isCredit.value && balance.value <= 0.01)) {
      if (canSubmit.value) postButton.value?.focus()
      else fields[idx + 1]?.focus()
    } else {
      fields[idx + 1].focus()
    }
    return
  }
  // single keys and Delete / PageUp belong to the panel, not to the bill's shortcuts
  if (e.key.length === 1 || e.key === 'Delete' || e.key === 'PageUp') e.stopPropagation()
}

// ---- Paytm (same calls as the Cashier Desk) ----
// Machine: push the UPI (QR) or Card box amount to the EDC machine and wait for the result
// (socket event from the webhook, with polling as fallback). Phone: a dynamic UPI QR shown here
// and sent to the customer's WhatsApp. A waiting UPI request can be queued (Queue or X) while the
// next bill is taken; Cancel stops it.
const paytm = ref({ enabled: false, qrEnabled: false, devices: [], show: false, payMode: 'QR', tid: '', deviceName: '', customerName: '', phone: '', askPhone: false, amount: 0, orderId: '', status: '', message: '', sending: false })
const paytmQr = ref({ show: false, amount: 0, orderId: '', status: '', message: '', image: '', link: false, sending: false, phone: '', withBill: false, tid: '', posId: '', waSending: false, waOk: undefined, waText: '' })
const billFormat = ref({ list: [], selected: '' })
const waSessionName = ref('')
const paytmPhoneInput = ref(null)
const paytmQrPhoneInput = ref(null)
let paytmPollTimer = null
let paytmQrPollTimer = null
const hasPaytmMachine = computed(() => paytm.value.enabled && paytm.value.devices.length > 0)
const paytmQrSrc = computed(() => {
  const img = paytmQr.value.image || ''
  return img.startsWith('data:') ? img : `data:image/png;base64,${img}`
})

// the page's shortcuts stay off while a Paytm popup is open
useSubwindowWatcher(computed(() => paytm.value.show))
useSubwindowWatcher(computed(() => paytmQr.value.show))

function statusClass(status) {
  if (status === 'Failed') return 'bg-[var(--color-danger)]/20 border-[var(--color-danger)]/50 text-[var(--color-danger)]'
  if (status === 'Success') return 'bg-[var(--color-success)]/20 border-[var(--color-success)]/50 text-[var(--color-success)]'
  return 'bg-[var(--color-info)]/20 border-[var(--color-info)]/50 text-[var(--color-info)]'
}

// A UPI / Card amount received through Paytm is locked, with its reference, for this bill
const paytmLock = ref({ invoice: '', upi: null, upiRef: '', card: null, cardRef: '' })
const upiLocked = computed(() => paytmLock.value.upi != null && paytmLock.value.invoice === invoice.value?.name)
const cardLocked = computed(() => paytmLock.value.card != null && paytmLock.value.invoice === invoice.value?.name)
const qrQueue = ref([])
// A UPI request waiting in the queue holds this bill's UPI box at the requested amount until it is
// paid or cancelled from its popup
const upiWaiting = computed(() => qrQueue.value.find(q => q.sales_invoice === invoice.value?.name && q.status === 'Pending'))
function lockPaytmPayment(mode, amount, refNo) {
  const lock = paytmLock.value.invoice === invoice.value?.name
    ? paytmLock.value
    : { invoice: invoice.value?.name, upi: null, upiRef: '', card: null, cardRef: '' }
  if (mode === 'card') Object.assign(lock, { card: Number(payments.value.card) || amount, cardRef: refNo })
  else Object.assign(lock, { upi: amount, upiRef: refNo })
  paytmLock.value = { ...lock }
}
// Every reset of the payment boxes (bill reload, credit flip…) puts locked values back
watch([payments, upiRefNo, cardRefNo, upiWaiting], () => {
  const lock = paytmLock.value
  if (upiWaiting.value && !upiLocked.value) {
    if (Number(payments.value.upi) !== upiWaiting.value.amount) payments.value.upi = upiWaiting.value.amount
    if (upiRefNo.value) upiRefNo.value = ''
  }
  if (upiLocked.value) {
    if (Number(payments.value.upi) !== lock.upi) payments.value.upi = lock.upi
    if (upiRefNo.value !== lock.upiRef) upiRefNo.value = lock.upiRef
  }
  if (cardLocked.value) {
    if (Number(payments.value.card) !== lock.card) payments.value.card = lock.card
    if (cardRefNo.value !== lock.cardRef) cardRefNo.value = lock.cardRef
  }
}, { deep: true })

// Full-screen tick flashed when Paytm confirms a payment
const paidTick = ref({ show: false, amount: 0, mode: 'upi', label: '' })
let paidTickTimer = null
function showPaidTick(amount, mode, label = '') {
  if (paidTickTimer) clearTimeout(paidTickTimer)
  paidTick.value = { show: true, amount, mode, label }
  paidTickTimer = setTimeout(() => { paidTick.value.show = false }, 1000)
}

// Left padding of the UPI / Card box = measured width of its label + buttons
function overlayPadBinder(padRef) {
  let overlayEl = null
  let observer = null
  return (el) => {
    if (el === overlayEl) return
    observer?.disconnect()
    overlayEl = el
    observer = null
    if (!el) return
    observer = new ResizeObserver(() => { padRef.value = el.offsetWidth + 32 }) // left-4 + 16px gap
    observer.observe(el)
  }
}
const upiInputPad = ref(96)
const cardInputPad = ref(96)
const bindUpiOverlay = overlayPadBinder(upiInputPad)
const bindCardOverlay = overlayPadBinder(cardInputPad)

function paytmMachineUser() {
  let inherited = ''
  try { inherited = localStorage.getItem('wb-inherited-user') || '' } catch (e) { /* storage blocked */ }
  return inherited || session.user.value
}

// Paytm / WhatsApp calls go through these so the dev mocks can answer them
function mockInvoiceInfo() {
  return { customer: invoice.value?.customer, customer_name: invoice.value?.customer_name }
}
function paytmPost(method, args, opts) {
  return devCall(method, args, () => frappePost(method, args, opts), mockInvoiceInfo)
}
function paytmGet(method, args, opts) {
  return devCall(method, args, () => frappeGet(method, args, opts), mockInvoiceInfo)
}

async function loadPaytmDevices() {
  try {
    const res = await paytmGet('ssplbilling.api.paytm_api.get_devices', { user: paytmMachineUser() })
    paytm.value.enabled = !!res?.enabled
    paytm.value.qrEnabled = !!res?.qr_enabled
    paytm.value.devices = res?.devices || []
  } catch (e) {
    paytm.value.enabled = false
    paytm.value.qrEnabled = false
  }
}

async function openPaytmModal(payMode) {
  errorMsg.value = ''
  // QR takes the UPI box amount, CARD the Card box amount
  const box = payMode === 'CARD' ? 'card' : 'upi'
  const amount = Number(payments.value[box]) || 0
  if (!invoice.value) return
  if (amount <= 0) {
    errorMsg.value = `Enter the amount in the ${box === 'card' ? 'Card' : 'UPI'} box before sending to the card machine.`
    return
  }
  // The machine is fixed by SSPL Paytm Settings (the user's assigned row)
  const device = paytm.value.devices[0]
  Object.assign(paytm.value, { show: true, payMode, tid: device.tid, deviceName: device.device_name, amount, orderId: '', status: '', message: '', sending: false, customerName: '', phone: '', askPhone: false })
  // Customer name + phone ride along in extendInfo; a placeholder number makes us ask first
  let contact = null
  try {
    contact = await frappeGet('ssplbilling.api.paytm_api.get_invoice_contact', { invoice_name: invoice.value.name })
  } catch (e) { /* send without contact details */ }
  Object.assign(paytm.value, { customerName: contact?.customer_name || '', phone: contact?.phone || '', askPhone: !!contact && !contact.phone })
  if (paytm.value.askPhone) {
    nextTick(() => paytmPhoneInput.value?.focus())
    return
  }
  sendToPaytm()
}

async function sendToPaytm() {
  const p = paytm.value
  Object.assign(p, { sending: true, orderId: '', status: '', message: 'Sending to the machine…' })
  try {
    if (await replaceQueuedRequest()) {
      p.show = false
      return
    }
    const res = await paytmPost('ssplbilling.api.paytm_api.send_to_device', {
      invoice_name: invoice.value.name,
      amount: p.amount,
      tid: p.tid,
      pay_mode: p.payMode,
      user: paytmMachineUser(),
      phone: p.phone,
    }, { silent: true })
    p.orderId = res.order_id
    p.status = 'Pending'
    p.message = `Waiting for payment on ${res.device_name}…`
    paytmPollTimer = startPolling(paytmPollTimer, () => paytm.value.orderId, applyPaytmResult)
  } catch (e) {
    p.status = 'Failed'
    p.message = e.message || 'Could not send to the card machine.'
  } finally {
    p.sending = false
  }
}

function startPolling(timer, getOrderId, apply) {
  if (timer) clearInterval(timer)
  const id = setInterval(async () => {
    const orderId = getOrderId()
    if (!orderId) return clearInterval(id)
    try {
      apply(await paytmPost('ssplbilling.api.paytm_api.get_status', { order_id: orderId }, { silent: true }))
    } catch (e) { /* keep polling; the socket event may still arrive */ }
  }, 3000)
  return id
}

function stopPaytmPolling() {
  if (paytmPollTimer) clearInterval(paytmPollTimer)
  paytmPollTimer = null
}

function stopPaytmQrPolling() {
  if (paytmQrPollTimer) clearInterval(paytmQrPollTimer)
  paytmQrPollTimer = null
}

function applyPaytmResult(r) {
  const p = paytm.value
  if (!r || r.order_id !== p.orderId || p.status !== 'Pending' || r.status === 'Pending') return
  stopPaytmPolling()
  p.status = r.status
  if (r.status !== 'Success') {
    p.message = r.message || `Payment ${r.status.toLowerCase()}.`
    return
  }
  // The customer may pay the other way on the machine: move the amount into the box it was paid by
  const sentFrom = p.payMode === 'CARD' ? 'card' : 'upi'
  const paidBy = r.mode === 'card' ? 'card' : 'upi'
  if (sentFrom !== paidBy) {
    payments.value[sentFrom] = Math.max(0, (Number(payments.value[sentFrom]) || 0) - r.amount)
    payments.value[paidBy] = (Number(payments.value[paidBy]) || 0) + r.amount
  } else {
    payments.value[paidBy] = r.amount
  }
  if (paidBy === 'card') cardRefNo.value = r.reference_no
  else upiRefNo.value = r.reference_no
  lockPaytmPayment(paidBy, r.amount, r.reference_no)
  fireConfetti({ count: 800, spread: 1.6 })
  showPaidTick(r.amount, paidBy)
  Object.assign(p, { show: false, orderId: '', status: '', message: '' })
  nextTick(() => postButton.value?.focus())
}

async function closePaytmModal() {
  const p = paytm.value
  stopPaytmPolling()
  if (p.orderId && p.status === 'Pending') {
    try {
      const r = await paytmPost('ssplbilling.api.paytm_api.cancel', { order_id: p.orderId }, { silent: true })
      // Paid just before the cashier gave up waiting — keep the payment
      if (r?.status === 'Success') return applyPaytmResult(r)
    } catch (e) { /* closing anyway */ }
  }
  Object.assign(p, { show: false, orderId: '', status: '', message: '' })
}

// Phone button by the UPI box: ask for the WhatsApp number, then Send makes the QR and sends it
async function openPaytmQr() {
  errorMsg.value = ''
  const amount = Number(payments.value.upi) || 0
  if (!invoice.value) return
  if (amount <= 0) {
    errorMsg.value = 'Enter the amount in the UPI box before creating the Paytm QR.'
    return
  }
  const invoiceName = invoice.value.name
  const device = paytm.value.devices[0]
  waSessionName.value = getWhatsAppSessionName()
  Object.assign(paytmQr.value, { show: true, amount, orderId: '', status: '', message: '', image: '', link: false, sending: false, phone: '', withBill: false, tid: device?.tid || '', posId: device?.pos_id || '', waSending: false, waOk: undefined, waText: '' })
  nextTick(() => paytmQrPhoneInput.value?.focus())
  billFormat.value = { list: [], selected: '' }
  frappeGet('ssplbilling.api.whatsapp_api.get_bill_print_templates', { invoice_name: invoiceName })
    .then((r) => {
      if (invoice.value?.name === invoiceName) billFormat.value = { list: r?.templates || [], selected: r?.default || '' }
    })
    .catch(() => { /* the server picks the default format */ })
  try {
    const phone = await frappeGet('ssplbilling.api.paytm_api.get_invoice_whatsapp', { invoice_name: invoiceName })
    // keep a number the cashier already typed
    if (phone && paytmQr.value.show && !paytmQr.value.orderId && !paytmQr.value.phone) paytmQr.value.phone = phone
  } catch (e) { /* cashier types it */ }
}

async function createPaytmQr(withBill = paytmQr.value.withBill) {
  const q = paytmQr.value
  if (q.sending) return
  q.withBill = withBill
  if (q.phone && !/^\d{10}$/.test(q.phone.replace(/\D/g, '').slice(-10))) {
    Object.assign(q, { status: '', message: 'Enter the 10-digit WhatsApp / mobile number' })
    return paytmQrPhoneInput.value?.focus()
  }
  Object.assign(q, { sending: true, orderId: '', status: '', message: '', image: '', waOk: undefined, waText: '' })
  try {
    if (await replaceQueuedRequest()) {
      q.show = false
      return
    }
    const res = await paytmPost('ssplbilling.api.paytm_api.create_qr', {
      invoice_name: invoice.value.name,
      amount: q.amount,
      mobile: q.phone,
      user: paytmMachineUser(),
    }, { silent: true })
    Object.assign(q, { orderId: res.order_id, image: res.qr_image, link: false, tid: res.tid || '', posId: res.pos_id || q.posId, status: 'Pending', message: 'Waiting for the customer to scan and pay…' })
    if (q.phone) sendPaytmQrLink()
    paytmQrPollTimer = startPolling(paytmQrPollTimer, () => paytmQr.value.orderId, applyPaytmQrResult)
  } catch (e) {
    q.status = 'Failed'
    q.message = e.message || 'Could not create the Paytm QR.'
  } finally {
    q.sending = false
  }
}

// The QR stands even when WhatsApp fails; Retry Send sends again
async function sendPaytmQrLink() {
  const q = paytmQr.value
  const orderId = q.orderId
  if (!orderId || q.waSending) return
  q.waSending = true
  try {
    const sent = await paytmPost('ssplbilling.api.whatsapp_api.send_receipt_pay_link', {
      order_id: orderId,
      session_id: getWhatsAppSessionId(),
      with_bill: q.withBill ? 1 : 0,
      print_template: q.withBill ? billFormat.value.selected || undefined : undefined,
    }, { silent: true })
    if (paytmQr.value.orderId === orderId) Object.assign(q, { waOk: true, waText: `${q.withBill ? 'Bill + ' : ''}${q.link ? 'Link' : 'QR'} sent to +${sent.phone}` })
  } catch (e) {
    if (paytmQr.value.orderId === orderId) Object.assign(q, { waOk: false, waText: `Not sent: ${e.message || e}` })
  } finally {
    q.waSending = false
  }
}

function applyPaytmQrResult(r) {
  const q = paytmQr.value
  if (!r || r.order_id !== q.orderId || q.status !== 'Pending' || r.status === 'Pending') return
  stopPaytmQrPolling()
  q.status = r.status
  if (r.status !== 'Success') {
    q.message = r.message || `Payment ${r.status.toLowerCase()}.`
    return
  }
  payments.value.upi = r.amount
  upiRefNo.value = r.reference_no
  lockPaytmPayment('upi', r.amount, r.reference_no)
  fireConfetti({ count: 800, spread: 1.6 })
  showPaidTick(r.amount, 'upi')
  resetPaytmQr()
  nextTick(() => postButton.value?.focus())
}

function resetPaytmQr() {
  Object.assign(paytmQr.value, { show: false, orderId: '', status: '', message: '', image: '', link: false, phone: '', withBill: false, tid: '', posId: '', waOk: undefined, waText: '' })
}

async function closePaytmQr() {
  const q = paytmQr.value
  stopPaytmQrPolling()
  if (q.orderId && q.status === 'Pending') {
    try {
      const r = await paytmPost('ssplbilling.api.paytm_api.cancel', { order_id: q.orderId }, { silent: true })
      // Paid just before the cashier gave up waiting — keep the payment
      if (r?.status === 'Success') return applyPaytmQrResult(r)
    } catch (e) { /* closing anyway */ }
  }
  resetPaytmQr()
}

function onPaytmSocket(r) {
  applyPaytmResult(r)
  applyPaytmQrResult(r)
  applyQrQueueResult(r)
}

// UPI queue (same as the Cashier Desk): a waiting Paytm request can be moved out of its popup so the
// next bill is taken. The queue keeps checking; a paid one shows the tick and fills UPI (locked) when
// its bill is opened, then it is posted. Rows come from the server, so they survive a reload.
let qrQueueTimer = null
let qrQueueLoading = false
// order to reopen in its popup once the page has brought its bill into view
let pendingQueuedOrder = ''

function startQrQueue() {
  if (!paytm.value.enabled && !paytm.value.qrEnabled) return
  loadQrQueue()
  if (qrQueueTimer) return
  qrQueueTimer = setInterval(() => {
    if (qrQueue.value.some(q => q.status === 'Pending')) loadQrQueue()
  }, 5000)
}

async function loadQrQueue() {
  if (qrQueueLoading) return
  qrQueueLoading = true
  try {
    const rows = await paytmPost('ssplbilling.api.paytm_api.get_qr_queue', {}, { silent: true })
    // requests still open in a popup are handled there
    const active = [paytmQr.value.orderId, paytm.value.orderId].filter(Boolean)
    const prev = qrQueue.value
    qrQueue.value = (rows || []).filter(r => !active.includes(r.order_id))
    for (const r of qrQueue.value) {
      if (r.status === 'Success' && prev.find(p => p.order_id === r.order_id)?.status === 'Pending') onQrQueuePaid(r)
    }
  } catch (e) { /* next round retries */ } finally {
    qrQueueLoading = false
  }
}

function applyQrQueueResult(r) {
  const q = qrQueue.value.find(x => x.order_id === r?.order_id)
  if (!q || q.status !== 'Pending' || r.status === 'Pending') return
  if (r.status !== 'Success') {
    qrQueue.value = qrQueue.value.filter(x => x !== q)
    return
  }
  Object.assign(q, { status: 'Success', amount: r.amount, reference_no: r.reference_no, mode: r.mode })
  onQrQueuePaid(q)
}

function onQrQueuePaid(q) {
  fireConfetti({ count: 800, spread: 1.6 })
  // another bill may be in view: name the one that got paid
  showPaidTick(q.amount, q.mode === 'card' ? 'card' : 'upi', `${q.customer_name || q.customer || ''} · ${q.sales_invoice}`)
  applyQueuedPayment(q)
}

// Fill and lock UPI (or Card, when paid by card on the machine) from a paid queue row, only while
// its bill is the one in view
function applyQueuedPayment(q) {
  if (q.status !== 'Success' || invoice.value?.name !== q.sales_invoice || isCredit.value) return
  if (q.mode === 'card') {
    if (cardLocked.value && paytmLock.value.cardRef === q.reference_no) return
    cashAuto.value = true
    payments.value.card = q.amount
    cardRefNo.value = q.reference_no
    lockPaytmPayment('card', q.amount, q.reference_no)
  } else {
    if (upiLocked.value && paytmLock.value.upiRef === q.reference_no) return
    cashAuto.value = true
    payments.value.upi = q.amount
    upiRefNo.value = q.reference_no
    lockPaytmPayment('upi', q.amount, q.reference_no)
  }
  nextTick(() => postButton.value?.focus())
}

function addToQueue(orderId, channel, amount, phone) {
  const inv = invoice.value
  qrQueue.value = [...qrQueue.value.filter(x => x.sales_invoice !== inv.name), {
    order_id: orderId,
    channel,
    sales_invoice: inv.name,
    customer: inv.customer,
    customer_name: inv.customer_name,
    customer_mobile: phone || '',
    amount,
    status: 'Pending',
    mode: 'upi',
    reference_no: '',
  }]
  startQrQueue()
}

function queuePaytmQr() {
  const q = paytmQr.value
  if (!q.orderId || q.status !== 'Pending' || !invoice.value) return
  stopPaytmQrPolling()
  addToQueue(q.orderId, q.link ? 'Link' : 'QR', q.amount, q.phone)
  resetPaytmQr()
}

// Machine UPI: the request stays on the machine while the next bill is taken
function queuePaytmMachine() {
  const p = paytm.value
  if (!p.orderId || p.status !== 'Pending' || !invoice.value) return
  stopPaytmPolling()
  addToQueue(p.orderId, 'EDC', p.amount, '')
  Object.assign(p, { show: false, orderId: '', status: '', message: '' })
}

// A new request replaces this bill's queued one; true when that one got paid meanwhile
async function replaceQueuedRequest() {
  const name = invoice.value?.name
  const queued = qrQueue.value.find(x => x.sales_invoice === name && x.status === 'Pending')
  if (queued) await cancelQueuedQr(queued)
  return qrQueue.value.some(x => x.sales_invoice === name && x.status === 'Success')
}

// The page loads the row's bill (emit), then resumeQueued fills a paid row or reopens a waiting popup
function openQueuedBill(q) {
  if (invoice.value?.name === q.sales_invoice && !loading.value) {
    pendingQueuedOrder = q.order_id
    return resumeQueued(q.sales_invoice)
  }
  pendingQueuedOrder = q.order_id
  emit('open-bill', q.sales_invoice)
}

async function resumeQueued(name) {
  const paid = qrQueue.value.find(x => x.sales_invoice === name && x.status === 'Success')
  if (paid) applyQueuedPayment(paid)
  const q = qrQueue.value.find(x => x.order_id === pendingQueuedOrder && x.sales_invoice === name)
  pendingQueuedOrder = ''
  if (!q || q.status !== 'Pending' || paytm.value.show || paytmQr.value.show) return
  if (q.channel === 'EDC') {
    qrQueue.value = qrQueue.value.filter(x => x !== q)
    Object.assign(paytm.value, {
      show: true, payMode: 'QR', amount: q.amount, orderId: q.order_id, status: 'Pending', sending: false,
      deviceName: q.device_name || '', tid: q.tid || '', customerName: q.customer_name || '', phone: '', askPhone: false,
      message: `Waiting for payment on ${q.device_name || 'the machine'}…`,
    })
    paytmPollTimer = startPolling(paytmPollTimer, () => paytm.value.orderId, applyPaytmResult)
    return
  }
  try {
    const res = await paytmPost('ssplbilling.api.paytm_api.get_invoice_qr', { order_id: q.order_id }, { silent: true })
    // paid or cancelled while the QR was fetched, or another bill came into view: leave it to the queue
    if (!qrQueue.value.includes(q) || q.status !== 'Pending' || invoice.value?.name !== name) return
    qrQueue.value = qrQueue.value.filter(x => x !== q)
    waSessionName.value = getWhatsAppSessionName()
    Object.assign(paytmQr.value, {
      show: true, amount: q.amount, orderId: q.order_id, status: 'Pending', sending: false, withBill: false,
      message: 'Waiting for the customer to scan and pay…', image: res.qr_image, link: q.channel === 'Link', tid: res.tid || '', posId: res.pos_id || '',
      phone: q.customer_mobile || '', waSending: false,
      waOk: q.customer_mobile ? true : undefined, waText: q.customer_mobile ? `QR sent to ${q.customer_mobile}` : '',
    })
    paytmQrPollTimer = startPolling(paytmQrPollTimer, () => paytmQr.value.orderId, applyPaytmQrResult)
  } catch (e) {
    errorMsg.value = e.message || 'Could not load the Paytm QR.'
  }
}

async function cancelQueuedQr(q) {
  try {
    const r = await paytmPost('ssplbilling.api.paytm_api.cancel', { order_id: q.order_id }, { silent: true })
    // Paid just before it was given up — keep the payment
    if (r?.status === 'Success') return applyQrQueueResult(r)
  } catch (e) { /* drop it anyway */ }
  qrQueue.value = qrQueue.value.filter(x => x.order_id !== q.order_id)
}

// Closing a waiting machine UPI request keeps it in the UPI queue; a card request cannot be
// queued, so its X still stops it
function dismissPaytmModal() {
  const p = paytm.value
  if (p.orderId && p.status === 'Pending' && p.payMode === 'QR' && invoice.value) return queuePaytmMachine()
  closePaytmModal()
}

// Closing a waiting QR keeps it in the UPI queue; only Cancel QR stops it
function dismissPaytmQr() {
  const q = paytmQr.value
  if (q.orderId && q.status === 'Pending' && invoice.value) return queuePaytmQr()
  closePaytmQr()
}

// Dev-only: walk the Paytm QR modal through Pending → Success without calling Paytm. The
// MOCK- reference it locks in is refused by processPayment, so nothing real can be posted.
function mockPaytmQrSuccess() {
  if (!invoice.value) {
    errorMsg.value = 'Save the bill (F8) or pick a draft before a mock payment.'
    return
  }
  const amount = Number(payments.value.upi) || invoice.value.rounded_total || invoice.value.grand_total || 100
  const orderId = `MOCK-${Date.now()}`
  stopPaytmQrPolling()
  Object.assign(paytmQr.value, { show: true, amount, orderId, status: 'Pending', message: 'Waiting for the customer to scan and pay… (mock)', image: '', sending: false })
  setTimeout(() => applyPaytmQrResult({ order_id: orderId, status: 'Success', amount, mode: 'upi', reference_no: orderId }), 2000)
}

// Dev Paytm mock: Paytm calls are answered in the browser (utils/devMock.js); switching it
// drops whatever was waiting so mock and real orders never mix
async function togglePaytmMock() {
  stopPaytmPolling()
  stopPaytmQrPolling()
  Object.assign(paytm.value, { show: false, orderId: '', status: '', message: '' })
  resetPaytmQr()
  qrQueue.value = []
  setPaytmMock(!paytmMockOn.value)
  await loadPaytmDevices()
  startQrQueue()
}

// Mock mode: settle the newest waiting mock order (machine or QR) as if Paytm answered
function settleMock(status) {
  if (!paytmMockOn.value) return status === 'Success' ? mockPaytmQrSuccess() : undefined
  const r = settleMockOrder(status)
  if (r) onPaytmSocket(r)
  else errorMsg.value = 'No mock Paytm order is waiting.'
}

onMounted(() => {
  loadPaytmDevices().then(startQrQueue)
  getFrappeSocket()?.on('paytm_payment_update', onPaytmSocket)
})

onUnmounted(() => {
  stopPaytmPolling()
  if (qrQueueTimer) clearInterval(qrQueueTimer)
  stopPaytmQrPolling()
  if (paidTickTimer) clearTimeout(paidTickTimer)
  bindUpiOverlay(null)
  bindCardOverlay(null)
  getFrappeSocket()?.off('paytm_payment_update', onPaytmSocket)
})

function focus() {
  if (!invoice.value) return false
  nextTick(() => (isCredit.value ? dueDateInput.value : cashInput.value)?.focus())
  return true
}

defineExpose({ focus })
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
.paid-tick-pop {
  animation: paid-tick-pop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
.paid-tick-path {
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  animation: paid-tick-draw 0.4s ease-out 0.3s forwards;
}
@keyframes paid-tick-pop {
  from { opacity: 0; transform: scale(0.4); }
  to { opacity: 1; transform: scale(1); }
}
@keyframes paid-tick-draw {
  to { stroke-dashoffset: 0; }
}
</style>
