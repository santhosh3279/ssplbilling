<template>
  <!-- Bill entry (with its collapsible bill list) on the left, payment on the right:
       F8 saves the bill and moves to Cash, F9 posts the payment, then the bill prints and clears;
       P prints and M modifies the bill from inside payment (outside its text boxes);
       Left in payment jumps to the bill list, Right in the bill list jumps back to payment;
       while focus is in payment the bill side dims so the cashier's eye stays on the panel -->
  <div class="pos-root flex h-screen overflow-hidden bg-[var(--color-bg)]">
    <div class="relative min-w-0 flex-1">
      <SalesInvoice
        ref="salesRef"
        pos-mode
        @active-bill="onActiveBill"
        @focus-payment="paymentRef?.focus()"
        @modifying="modifying = $event"
        @print-closed="onPrintClosed"
      />
      <div class="pos-dim pointer-events-none absolute inset-0 z-40" aria-hidden="true"></div>
    </div>
    <PosPaymentPanel
      ref="paymentRef"
      class="pos-pay"
      :invoice-name="activeBill"
      :reload-key="reloadKey"
      :suspended="modifying"
      @loaded="onPaymentLoaded"
      @settled="onSettled"
      @back="salesRef?.focusBarcodeInput()"
      @bill-list="salesRef?.focusBillList()"
      @open-bill="salesRef?.openBill($event)"
      @print="salesRef?.handlePrint()"
      @modify="salesRef?.handleModify()"
    />

    <!-- Same as CashierDesk: an exempt bill paid by UPI is offered for mirroring, asked once its print popup closes -->
    <Warning
      :show="showGstWarning"
      title="GST Mirroring"
      :message="`mirror salesinvoice no: ${mirrorInvoice} to alternate company`"
      @close="closeGstWarning"
      @confirm="confirmGstWarning"
    />
    <BillMirrorCreator
      v-if="showBillMirrorCreator"
      :show="showBillMirrorCreator"
      :invoice-name="mirrorInvoice"
      @close="closeBillMirrorCreator"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SalesInvoice from './SalesInvoice.vue'
import PosPaymentPanel from '../components/PosPaymentPanel.vue'
import Warning from '../components/Warning.vue'
import BillMirrorCreator from '../components/BillMirrorCreator.vue'
import { useSubwindowWatcher } from '../services/shortcutManager'

const salesRef = ref(null)
const paymentRef = ref(null)
const activeBill = ref(null)
const reloadKey = ref(0)
// M opened the bill for edit: payment hides until F8 saves it again
const modifying = ref(false)
// a just-saved bill or a draft picked from the list goes straight to Cash; a paid bill leaves focus in the bill
const focusOnLoad = ref(false)

function onActiveBill(name, reason) {
  focusOnLoad.value = reason === 'saved' || reason === 'draft'
  // saved again after a modify: same bill, new totals, so load it afresh
  if (name && name === activeBill.value) reloadKey.value++
  activeBill.value = name
}

// settled bill waiting for the mirror question until its print popup closes
const pendingMirror = ref('')
const mirrorInvoice = ref('')
const showGstWarning = ref(false)
const showBillMirrorCreator = ref(false)
// the bill side's window shortcuts stay quiet while the question is open
useSubwindowWatcher(showGstWarning)

function onSettled(name, { askMirror } = {}) {
  pendingMirror.value = askMirror ? name : ''
  salesRef.value?.printAndClear()
}

function onPrintClosed() {
  if (!pendingMirror.value) return
  mirrorInvoice.value = pendingMirror.value
  pendingMirror.value = ''
  showGstWarning.value = true
}

function closeGstWarning() {
  showGstWarning.value = false
  salesRef.value?.focusBarcodeInput()
}

function confirmGstWarning() {
  showGstWarning.value = false
  showBillMirrorCreator.value = true
}

function closeBillMirrorCreator() {
  showBillMirrorCreator.value = false
  salesRef.value?.focusBarcodeInput()
}

function onPaymentLoaded() {
  if (focusOnLoad.value) paymentRef.value?.focus()
  focusOnLoad.value = false
}
</script>

<style scoped>
/* driven by real focus (:has + :focus-within), so it can never get stuck on after an input unmounts */
.pos-dim {
  opacity: 0;
  background: rgb(0 0 0 / 0.45);
  backdrop-filter: blur(1.5px);
  transition: opacity 150ms ease;
}
.pos-root:has(.pos-pay:focus-within) .pos-dim {
  opacity: 1;
}
</style>
