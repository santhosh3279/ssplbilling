<template>
  <!-- Bill entry (with its collapsible bill list) on the left, payment on the right:
       F8 saves the bill and moves to Cash, F9 posts the payment, then the bill prints and clears -->
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)]">
    <div class="min-w-0 flex-1">
      <SalesInvoice
        ref="salesRef"
        pos-mode
        @active-bill="onActiveBill"
        @focus-payment="paymentRef?.focus()"
      />
    </div>
    <PosPaymentPanel
      ref="paymentRef"
      :invoice-name="activeBill"
      :reload-key="reloadKey"
      @loaded="onPaymentLoaded"
      @settled="salesRef?.printAndClear()"
      @back="salesRef?.focusBarcodeInput()"
      @open-bill="salesRef?.openBill($event)"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SalesInvoice from './SalesInvoice.vue'
import PosPaymentPanel from '../components/PosPaymentPanel.vue'

const salesRef = ref(null)
const paymentRef = ref(null)
const activeBill = ref(null)
const reloadKey = ref(0)
// a just-saved bill goes straight to payment; one picked from the list leaves focus in the bill
const focusOnLoad = ref(false)

function onActiveBill(name, reason) {
  focusOnLoad.value = reason === 'saved'
  // saved again after a modify: same bill, new totals, so load it afresh
  if (name && name === activeBill.value) reloadKey.value++
  activeBill.value = name
}

function onPaymentLoaded() {
  if (focusOnLoad.value) paymentRef.value?.focus()
  focusOnLoad.value = false
}
</script>
