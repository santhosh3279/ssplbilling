import * as XLSX from 'xlsx'

/**
 * Generates a multi-sheet XLSX report for the cashier's daily activities.
 * 
 * @param {Object} data - The report data
 * @param {string} data.date - The selected report date
 * @param {Object} data.docs - The cashier session documents (Opening, Mid-Day-1, etc.)
 * @param {Array} data.bills - Today's filtered bills
 * @param {Array} data.ledgerEntries - Cash ledger transactions
 * @param {number} data.ledgerOpening - Cash ledger opening balance
 * @param {Object} data.metadata - Biller details (billerName, warehouse, etc.)
 * @param {Function} data.getMopAmount - Helper to get MOP amounts from a bill
 */
export function generateCashierReport(data) {
  const { date, docs, bills, ledgerEntries, ledgerOpening, metadata, getMopAmount } = data
  const wb = XLSX.utils.book_new()

  // ── SHEET 1: DAILY CASH SUMMARY ───────────────────────────────────
  const summarySheetData = []
  
  // Header section
  summarySheetData.push(['Biller Name:', metadata.billerName, '', 'Warehouse:', metadata.warehouse])
  summarySheetData.push(['Cash Account:', metadata.cashAccount, '', 'Cost Center:', metadata.costCenter])
  summarySheetData.push([]) // Spacer

  // Sessions side-by-side (side-by-side isn't trivial in AOA; but we can do it)
  const types = ['Opening', 'Mid-Day-1', 'Mid-Day-2', 'Closing']
  const denoms = ['500', '200', '100', '50', '20', '10', '5', '2', '1']

  // Session Headers
  const sessHeader = []
  types.forEach(t => {
    sessHeader.push(t.toUpperCase(), '', '', '') // Merge handled later
  })
  summarySheetData.push(sessHeader)

  const sessSubHeader = []
  types.forEach(() => {
    sessSubHeader.push('Denom', 'Count', 'Value', '')
  })
  summarySheetData.push(sessSubHeader)

  // Denom rows
  denoms.forEach(d => {
    const row = []
    types.forEach(t => {
      const doc = docs[t]
      const count = doc ? Number(doc[d] || 0) : 0
      const val = count * Number(d)
      row.push(Number(d), count, val, '')
    })
    summarySheetData.push(row)
  })

  summarySheetData.push([]) // Spacer

  // Totals Section
  const totalsRow = []
  types.forEach(t => {
    totalsRow.push('TOTAL BOX', '', docs[t]?.total || 0, '')
  })
  summarySheetData.push(totalsRow)

  const ledgerRow = []
  types.forEach(t => {
    ledgerRow.push('LEDGER BAL', '', docs[t]?.cash_ledger_balance || 0, '')
  })
  summarySheetData.push(ledgerRow)

  const diffRow = []
  types.forEach(t => {
    const doc = docs[t]
    const diff = Number(doc?.difference || 0)
    const status = diff === 0 ? 'Tally' : (diff > 0 ? 'Excess' : 'Short')
    diffRow.push('DIFFERENCE', '', diff, status)
  })
  summarySheetData.push(diffRow)

  const summarySheet = XLSX.utils.aoa_to_sheet(summarySheetData)
  
  // Apply Merges for Sheet 1
  const merges = []
  // Header merges (Biller Name/Warehouse labels)
  // Types merges
  types.forEach((t, i) => {
    merges.push({ s: { r: 3, c: i * 4 }, e: { r: 3, c: i * 4 + 2 } }) // Session titles
  })
  summarySheet['!merges'] = merges
  XLSX.utils.book_append_sheet(wb, summarySheet, 'Daily Cash Summary')

  // ── SHEET 2: TODAY'S BILLS ────────────────────────────────────────
  const billsData = [
    ['Bill No', 'Customer', 'Total', 'Cash', 'UPI', 'Card', 'Credit']
  ]
  let totalSales = 0
  const totalsMop = { cash: 0, upi: 0, card: 0, credit: 0 }

  bills.forEach(bill => {
    const cash = getMopAmount(bill, 'cash')
    const upi = getMopAmount(bill, 'upi')
    const card = getMopAmount(bill, 'card')
    const credit = getMopAmount(bill, 'credit')
    
    totalSales += bill.grand_total
    totalsMop.cash += cash
    totalsMop.upi += upi
    totalsMop.card += card
    totalsMop.credit += credit

    billsData.push([
      bill.name,
      bill.customer,
      bill.grand_total,
      cash,
      upi,
      card,
      credit
    ])
  })

  // Append Totals row
  billsData.push(['TOTAL', '', totalSales, totalsMop.cash, totalsMop.upi, totalsMop.card, totalsMop.credit])
  
  const billsSheet = XLSX.utils.aoa_to_sheet(billsData)
  XLSX.utils.book_append_sheet(wb, billsSheet, 'Today Bills')

  // ── SHEET 3: CASH LEDGER ──────────────────────────────────────────
  const ledgerData = [
    ['Time', 'Voucher No', 'Party', 'Debit (DR)', 'Credit (CR)', 'Balance'],
    ['', 'OPENING BALANCE', '', '', '', ledgerOpening]
  ]

  ledgerEntries.forEach(entry => {
    ledgerData.push([
      entry.time,
      entry.voucher_no,
      entry.party || '',
      entry.debit || 0,
      entry.credit || 0,
      entry.balance || 0
    ])
  })

  const ledgerSheet = XLSX.utils.aoa_to_sheet(ledgerData)
  XLSX.utils.book_append_sheet(wb, ledgerSheet, 'Cash Ledger')

  // Generate and Download File
  XLSX.writeFile(wb, `Cashier_Report_${date}.xlsx`)
}
