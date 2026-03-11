<template>
  <div v-if="show" class="absolute inset-0 z-[60] flex items-center justify-center bg-black/40" @click.self="$emit('close')">
    <div class="w-[400px] rounded-xl bg-white shadow-2xl overflow-hidden">
      <div class="border-b border-gray-200 px-5 py-4 bg-gray-50">
        <div class="text-xl font-bold text-gray-700">Select Date Range</div>
        <div class="text-sm text-gray-500">
          {{ customerName }}
        </div>
      </div>
      <div class="flex flex-col gap-4 px-6 py-5">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">From Date (DD/MM/YYYY)</label>
          <input 
            ref="fromDateInput"
            v-model="dateData.fromDisplay" 
            class="rounded border border-gray-300 px-3 py-2 text-xl font-mono outline-none focus:border-blue-500" 
            placeholder="DD/MM/YYYY"
            maxlength="10"
            @input="e => onInput(e, 'from')"
            @focus="selectText"
            @keydown.backspace="handleBackspace($event, 'from')"
            @keydown.enter.prevent="focusToDate"
            @keydown.esc.stop="$emit('close')"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">To Date (DD/MM/YYYY)</label>
          <input 
            ref="toDateInput"
            v-model="dateData.toDisplay" 
            class="rounded border border-gray-300 px-3 py-2 text-xl font-mono outline-none focus:border-blue-500" 
            placeholder="DD/MM/YYYY"
            maxlength="10"
            @input="e => onInput(e, 'to')"
            @focus="selectText"
            @keydown.backspace="handleBackspace($event, 'to')"
            @keydown.enter.prevent="confirmDate"
            @keydown.esc.stop="$emit('close')"
          />
        </div>
      </div>
      <div class="flex justify-end gap-3 border-t border-gray-200 px-6 py-4 bg-gray-50">
        <button class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600" @click="$emit('close')">Cancel</button>
        <button class="rounded bg-blue-600 px-6 py-2 font-bold text-white shadow-md active:scale-95" @click="confirmDate">
          Confirm <kbd class="ml-1 rounded border border-blue-500 bg-blue-500 px-1.5 py-0.5 font-mono text-xs">Enter</kbd>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'

const props = defineProps({
  show: Boolean,
  customerName: String
})

const emit = defineEmits(['close', 'confirm'])

const fromDateInput = ref(null)
const toDateInput = ref(null)

const dateData = ref({
  fromDisplay: '', // DD/MM/YYYY
  toDisplay: '',
  fromISO: '',     // YYYY-MM-DD
  toISO: ''
})

function selectText(e) {
  e.target.select()
}

function handleBackspace(e, field) {
  const currentVal = field === 'from' ? dateData.value.fromDisplay : dateData.value.toDisplay
  if (currentVal && currentVal.length > 0) {
    e.preventDefault()
    if (field === 'from') {
      dateData.value.fromDisplay = ''
      dateData.value.fromISO = ''
    } else {
      dateData.value.toDisplay = ''
      dateData.value.toISO = ''
    }
  }
}

function formatDateToDisplay(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

function initDates() {
  const now = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  const [y, m, d] = formatter.format(now).split('-').map(Number)

  // From Date: April 1st of the current fiscal year
  // If we are in Jan/Feb/March, the fiscal year started in the previous calendar year
  const fromYear = m < 4 ? y - 1 : y
  const fromISO = `${fromYear}-04-01`
  
  // To Date: Today's date (local YYYY-MM-DD)
  const toISO = `${y}-${m.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`

  dateData.value = {
    fromISO,
    toISO,
    fromDisplay: formatDateToDisplay(fromISO),
    toDisplay: formatDateToDisplay(toISO)
  }
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    initDates()
    nextTick(() => {
      fromDateInput.value?.focus()
      fromDateInput.value?.select()
    })
  }
}, { immediate: true })

function onInput(e, field) {
  let val = e.target.value.replace(/\D/g, '') // Keep only digits
  
  // Smart Year Logic: If user enters 4 digits (DDMM), auto-complete the year
  if (val.length === 4) {
    const day = parseInt(val.slice(0, 2))
    const month = parseInt(val.slice(2, 4))
    
    if (!isNaN(day) && !isNaN(month) && month >= 1 && month <= 12) {
      const now = new Date()
      const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit' }
      const formatter = new Intl.DateTimeFormat('en-CA', options)
      const [y, m] = formatter.format(now).split('-').map(Number)

      const currentMonth = m
      let year = y

      if (month > currentMonth) {
        year--
      }
      
      const dayStr = day.toString().padStart(2, '0')
      const monthStr = month.toString().padStart(2, '0')
      
      const iso = `${year}-${monthStr}-${dayStr}`
      const display = `${dayStr}/${monthStr}/${year}`

      if (field === 'from') {
        dateData.value.fromISO = iso
        dateData.value.fromDisplay = display
      } else {
        dateData.value.toISO = iso
        dateData.value.toDisplay = display
      }
      return
    }
  }

  // Basic formatting as user types beyond 4 digits or manual entry
  if (val.length > 2 && val.length <= 4) {
    val = val.slice(0, 2) + '/' + val.slice(2)
  } else if (val.length > 4) {
    val = val.slice(0, 2) + '/' + val.slice(2, 4) + '/' + val.slice(4, 8)
  }

  if (field === 'from') dateData.value.fromDisplay = val
  else dateData.value.toDisplay = val

  // Try to update ISO if we have a full valid date
  if (val.length === 10) {
    const [d, m, y] = val.split('/')
    if (d && m && y && y.length === 4) {
      const iso = `${y}-${m}-${d}`
      if (field === 'from') dateData.value.fromISO = iso
      else dateData.value.toISO = iso
    }
  }
}

function focusToDate() {
  nextTick(() => {
    toDateInput.value?.focus()
    toDateInput.value?.select()
  })
}

function confirmDate() {
  const from = dateData.value.fromISO
  const to = dateData.value.toISO
  if (from && to) {
    emit('confirm', { from, to })
    emit('close')
  } else if (dateData.value.fromDisplay.length === 10 && dateData.value.toDisplay.length === 10) {
    // Backup: try to parse from display if ISO not set
    const [df, mf, yf] = dateData.value.fromDisplay.split('/')
    const [dt, mt, yt] = dateData.value.toDisplay.split('/')
    emit('confirm', { 
      from: `${yf}-${mf}-${df}`, 
      to: `${yt}-${mt}-${dt}` 
    })
    emit('close')
  }
}
</script>
