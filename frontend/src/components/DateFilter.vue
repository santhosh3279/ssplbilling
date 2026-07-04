<template>
  <div v-if="show" class="absolute inset-0 z-[60] flex items-center justify-center bg-black/70" @click.self="$emit('close')">
    <div class="w-[400px] rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden">
      <div class="border-b border-[var(--color-border)] px-5 py-4 bg-[var(--color-surface)]">
        <div class="text-xl font-bold text-[var(--color-text)]">Select Date Range</div>
        <div class="text-sm text-[var(--color-text-muted)]">
          {{ customerName }}
        </div>
      </div>
      <div class="flex flex-col gap-4 px-6 py-5">
        <!-- Quick Filters -->
        <div class="grid grid-cols-5 gap-2">
          <button
            ref="btnToday"
            @click="setDateRange('Today')"
            @keydown="e => handleButtonKeydown(e, 0)"
            class="py-2 text-xs font-black uppercase tracking-wider rounded-xl border-2 focus:outline-none active:scale-95 transition-all shadow-sm"
            :class="selectedRange === 'Today'
              ? 'border-[var(--color-info)] bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
              : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)] focus:bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:border-[var(--color-info)] focus:border-[var(--color-info)]'"
          >
            Today
          </button>
          <button
            ref="btnYesterday"
            @click="setDateRange('Yesterday')"
            @keydown="e => handleButtonKeydown(e, 1)"
            class="py-2 text-xs font-black uppercase tracking-wider rounded-xl border-2 focus:outline-none active:scale-95 transition-all shadow-sm"
            :class="selectedRange === 'Yesterday'
              ? 'border-[var(--color-info)] bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
              : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)] focus:bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:border-[var(--color-info)] focus:border-[var(--color-info)]'"
          >
            Y
          </button>
          <button
            ref="btnCM"
            @click="setDateRange('CM')"
            @keydown="e => handleButtonKeydown(e, 2)"
            class="py-2 text-xs font-black uppercase tracking-wider rounded-xl border-2 focus:outline-none active:scale-95 transition-all shadow-sm"
            :class="selectedRange === 'CM'
              ? 'border-[var(--color-info)] bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
              : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)] focus:bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:border-[var(--color-info)] focus:border-[var(--color-info)]'"
          >
            CM
          </button>
          <button
            ref="btnLM"
            @click="setDateRange('LM')"
            @keydown="e => handleButtonKeydown(e, 3)"
            class="py-2 text-xs font-black uppercase tracking-wider rounded-xl border-2 focus:outline-none active:scale-95 transition-all shadow-sm"
            :class="selectedRange === 'LM'
              ? 'border-[var(--color-info)] bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
              : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)] focus:bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:border-[var(--color-info)] focus:border-[var(--color-info)]'"
          >
            LM
          </button>
          <button
            ref="btnFY"
            @click="setDateRange('FY')"
            @keydown="e => handleButtonKeydown(e, 4)"
            class="py-2 text-xs font-black uppercase tracking-wider rounded-xl border-2 focus:outline-none active:scale-95 transition-all shadow-sm"
            :class="selectedRange === 'FY'
              ? 'border-[var(--color-info)] bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
              : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)] focus:bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:border-[var(--color-info)] focus:border-[var(--color-info)]'"
          >
            FY
          </button>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">From Date (DD-MM-YYYY)</label>
          <input
            ref="fromDateInput"
            v-model="dateData.fromDisplay"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xl font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            placeholder="DD-MM-YYYY"
            maxlength="10"
            @input="e => onInput(e, 'from')"
            @focus="selectText"
            @keydown.backspace="handleBackspace($event, 'from')"
            @keydown.enter.prevent="focusToDate"
            @keydown.down.prevent="focusToDate"
            @keydown.up.prevent="focusQuickFilters"
            @keydown.esc.stop="$emit('close')"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">To Date (DD-MM-YYYY)</label>
          <input
            ref="toDateInput"
            v-model="dateData.toDisplay"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xl font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            placeholder="DD-MM-YYYY"
            maxlength="10"
            @input="e => onInput(e, 'to')"
            @focus="selectText"
            @keydown.backspace="handleBackspace($event, 'to')"
            @keydown.enter.prevent="confirmDate"
            @keydown.up.prevent="focusFromDate"
            @keydown.esc.stop="$emit('close')"
          />
        </div>
      </div>
      <div class="flex justify-end gap-3 border-t border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface)]">
        <button class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-2 font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]" @click="$emit('close')">Cancel</button>
        <button class="rounded bg-[var(--color-info)] px-6 py-2 font-bold text-[var(--color-text-on-highlight)] shadow-md active:scale-95 hover:bg-[var(--color-info)]" @click="confirmDate">
          Confirm <kbd class="ml-1 rounded border border-[var(--color-info)] bg-[var(--color-info)] px-1.5 py-0.5 font-mono text-xs">Enter</kbd>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { useSubwindow } from '../services/shortcutManager'

useSubwindow()

const props = defineProps({
  show: Boolean,
  customerName: String
})

const emit = defineEmits(['close', 'confirm'])

const fromDateInput = ref(null)
const toDateInput = ref(null)

const btnToday = ref(null)
const btnYesterday = ref(null)
const btnCM = ref(null)
const btnLM = ref(null)
const btnFY = ref(null)

function focusQuickFilters() {
  nextTick(() => {
    btnToday.value?.focus()
  })
}

function handleButtonKeydown(e, index) {
  if (e.key === 'ArrowRight') {
    e.preventDefault()
    const nextIdx = (index + 1) % 5
    focusButton(nextIdx)
  } else if (e.key === 'ArrowLeft') {
    e.preventDefault()
    const prevIdx = (index - 1 + 5) % 5
    focusButton(prevIdx)
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    nextTick(() => {
      fromDateInput.value?.focus()
      fromDateInput.value?.select()
    })
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const ranges = ['Today', 'Yesterday', 'CM', 'LM', 'FY']
    setDateRange(ranges[index])
    confirmDate()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  }
}

function focusButton(index) {
  const refs = [btnToday.value, btnYesterday.value, btnCM.value, btnLM.value, btnFY.value]
  const target = refs[index]
  if (target) {
    target.focus()
  }
}

const selectedRange = ref('FY')

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
  selectedRange.value = ''
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
  return `${d}-${m}-${y}`
}

function getLocalDateParts() {
  const now = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options)
  return formatter.format(now).split('-').map(Number)
}

function initDates() {
  const [y, m, d] = getLocalDateParts()
  const todayISO = `${y}-${m.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`
  const fromYear = m < 4 ? y - 1 : y
  const fromISO = `${fromYear}-04-01`

  dateData.value = {
    fromISO: fromISO,
    toISO: todayISO,
    fromDisplay: formatDateToDisplay(fromISO),
    toDisplay: formatDateToDisplay(todayISO)
  }
  selectedRange.value = 'FY'
}

function setDateRange(range) {
  const [y, m, d] = getLocalDateParts()
  const todayISO = `${y}-${m.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`

  let fromISO = todayISO
  let toISO = todayISO

  if (range === 'Today') {
    fromISO = todayISO
    toISO = todayISO
  } else if (range === 'Yesterday') {
    const date = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }))
    date.setDate(date.getDate() - 1)
    const options = { year: 'numeric', month: '2-digit', day: '2-digit' }
    const formatter = new Intl.DateTimeFormat('en-CA', options)
    const yesterdayISO = formatter.format(date)
    fromISO = yesterdayISO
    toISO = yesterdayISO
  } else if (range === 'CM') {
    fromISO = `${y}-${m.toString().padStart(2, '0')}-01`
    toISO = todayISO
  } else if (range === 'LM') {
    let lmYear = y
    let lmMonth = m - 1
    if (lmMonth === 0) {
      lmMonth = 12
      lmYear--
    }
    const lastDayOfLm = new Date(lmYear, lmMonth, 0).getDate()
    fromISO = `${lmYear}-${lmMonth.toString().padStart(2, '0')}-01`
    toISO = `${lmYear}-${lmMonth.toString().padStart(2, '0')}-${lastDayOfLm.toString().padStart(2, '0')}`
  } else if (range === 'FY') {
    const fromYear = m < 4 ? y - 1 : y
    fromISO = `${fromYear}-04-01`
    toISO = todayISO
  }

  dateData.value = {
    fromISO,
    toISO,
    fromDisplay: formatDateToDisplay(fromISO),
    toDisplay: formatDateToDisplay(toISO)
  }
  selectedRange.value = range
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
  selectedRange.value = ''
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
      const display = `${dayStr}-${monthStr}-${year}`

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
    val = val.slice(0, 2) + '-' + val.slice(2)
  } else if (val.length > 4) {
    val = val.slice(0, 2) + '-' + val.slice(2, 4) + '-' + val.slice(4, 8)
  }

  if (field === 'from') dateData.value.fromDisplay = val
  else dateData.value.toDisplay = val

  // Try to update ISO if we have a full valid date
  if (val.length === 10) {
    const [d, m, y] = val.split('-')
    if (d && m && y && y.length === 4) {
      const iso = `${y}-${m}-${d}`
      if (field === 'from') dateData.value.fromISO = iso
      else dateData.value.toISO = iso
    }
  }
}

function focusToDate() {
  autoCompleteDate('from')
  nextTick(() => {
    toDateInput.value?.focus()
    toDateInput.value?.select()
  })
}

function focusFromDate() {
  autoCompleteDate('to')
  nextTick(() => {
    fromDateInput.value?.focus()
    fromDateInput.value?.select()
  })
}

function autoCompleteDate(field) {
  const displayField = field === 'from' ? 'fromDisplay' : 'toDisplay'
  const isoField = field === 'from' ? 'fromISO' : 'toISO'
  let val = dateData.value[displayField].replace(/\D/g, '')

  if (val.length >= 1 && val.length <= 2) {
    const day = parseInt(val)
    if (!isNaN(day) && day >= 1 && day <= 31) {
      const now = new Date()
      const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit' }
      const formatter = new Intl.DateTimeFormat('en-CA', options)
      const [y, m] = formatter.format(now).split('-').map(Number)

      const dayStr = day.toString().padStart(2, '0')
      const monthStr = m.toString().padStart(2, '0')
      
      dateData.value[isoField] = `${y}-${monthStr}-${dayStr}`
      dateData.value[displayField] = `${dayStr}-${monthStr}-${y}`
    }
  }
}

function confirmDate() {
  autoCompleteDate('to')
  const from = dateData.value.fromISO
  const to = dateData.value.toISO
  if (from && to) {
    emit('confirm', { from, to })
    emit('close')
  } else if (dateData.value.fromDisplay.length === 10 && dateData.value.toDisplay.length === 10) {
    // Backup: try to parse from display if ISO not set
    const [df, mf, yf] = dateData.value.fromDisplay.split('-')
    const [dt, mt, yt] = dateData.value.toDisplay.split('-')
    emit('confirm', { 
      from: `${yf}-${mf}-${df}`, 
      to: `${yt}-${mt}-${dt}` 
    })
    emit('close')
  }
}
</script>
