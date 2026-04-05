import re

with open('frontend/src/pages/GstLedger.vue', 'r') as f:
    content = f.read()

# 1. Add Print and Excel buttons
btns = """        <div class="flex items-center gap-4 text-[10px] text-slate-400">
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-300">Ctrl+L</kbd> Search</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-300">Esc</kbd> Back</span>
        </div>

        <div class="flex items-center gap-2">
          <!-- Print Button -->
          <button
            v-if="ledgerData"
            @click="showPrintModal = true"
            class="flex items-center gap-1.5 rounded border border-slate-600 bg-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-600 hover:text-slate-100"
            title="Print Ledger"
          >
            🖨 Print
          </button>

          <!-- Excel Button -->
          <button
            v-if="ledgerData"
            @click="exportExcel"
            class="flex items-center gap-1.5 rounded border border-slate-600 bg-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-600 hover:text-slate-100"
            title="Export to Excel"
          >
            ⬇ Excel
          </button>
        </div>"""

content = re.sub(
    r'        <div class="flex items-center gap-4 text-\[10px\] text-slate-400">\s*<span><kbd[^>]+>Ctrl\+L</kbd> Search</span>\s*<span><kbd[^>]+>Esc</kbd> Back</span>\s*</div>',
    btns,
    content,
    count=1
)

# 2. Remove <th>Type</th>
content = content.replace('<th class="px-6 py-3 text-left">Type</th>\n', '')

# 3. Remove <td>Type</td>
td_pattern = r'                <td class="px-6 py-3">\s*<span\s*class="rounded-full[^>]+>\s*\{\{\s*entry\.voucher_type[^}]+\}\}\s*</span>\s*</td>\n'
content = re.sub(td_pattern, '', content)

# 4. Colspans
content = content.replace('<td colspan="5" class="px-6 py-3 font-bold', '<td colspan="4" class="px-6 py-3 font-bold')
content = content.replace('<td colspan="6">No entries found', '<td colspan="5">No entries found')

# 5. Add PrintOptionsModal
modal = """    <!-- PRINT MODAL -->
    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="printKey"
      :doctype="''"
      @close="showPrintModal = false"
    />
  </div>
</template>"""
content = content.replace('  </div>\n</template>', modal)

# 6. Add imports
imports = """import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import { utils, writeFile } from 'xlsx'"""
content = content.replace("import CustomerSearchModal from '../components/CustomerSearchModal.vue'", imports)

# 7. Add variables
vars_new = """const showCustomerSearchModal = ref(false)
const showPrintModal = ref(false)
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 120)

// ── COMPUTED ─────────────────────────────────────────────────────────
const printKey = computed(() => {
  if (!selectedCustomer.value) return ''
  return `${selectedCustomer.value.name}||${fromDate.value}||${toDate.value}||Gst Ledger`
})

const dynamicRowStyle"""
content = content.replace("""const showCustomerSearchModal = ref(false)\nconst zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 120)\n\n// ── COMPUTED ─────────────────────────────────────────────────────────\nconst dynamicRowStyle""", vars_new)

# 8. Add exportExcel
export_func = """function onRowClick(entry) {
  selectedEntry.value = entry
}

// ── EXPORT EXCEL ───────────────────────────────────────────────────────
function exportExcel() {
  if (!ledgerData.value || !ledgerData.value.entries.length) return

  const headers = ['Date', 'Voucher No', 'Debit', 'Credit', 'Balance']
  const data = ledgerData.value.entries.map(e => [
    e.date,
    e.voucher_no,
    e.debit || 0,
    e.credit || 0,
    e.balance || 0
  ])

  // Add opening balance at the top
  data.unshift(['', 'Opening Balance', '', '', ledgerData.value.opening_balance])

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data])
  
  ws['!cols'] = [
    { wch: 15 }, { wch: 25 }, { wch: 15 }, { wch: 15 }, { wch: 15 }
  ]

  utils.book_append_sheet(wb, ws, 'GST Ledger')
  
  const custName = selectedCustomer.value?.customer_name || selectedCustomer.value?.name || 'Customer'
  writeFile(wb, `GST_Ledger_${custName}_${fromDate.value}_to_${toDate.value}.xlsx`)
}

function openInErpNext"""
content = content.replace("function onRowClick(entry) {\n  selectedEntry.value = entry\n}\n\nfunction openInErpNext", export_func)

with open('frontend/src/pages/GstLedger.vue', 'w') as f:
    f.write(content)
