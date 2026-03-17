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

  // Header section - we'll fill session data first and then add metadata to those rows
  const summarySheetData = []
  
  // Create 15 empty rows initially to be safe (denoms + headers + totals)
  for (let i = 0; i < 20; i++) {
    summarySheetData.push(new Array(20).fill(''))
  }

  // Session Headers (Row 3, index 3)
  const types = ['Opening', 'Mid-Day-1', 'Mid-Day-2', 'Closing']
  types.forEach((t, i) => {
    summarySheetData[3][i * 4] = t.toUpperCase()
  })

  // Sub Headers (Row 4, index 4)
  types.forEach((t, i) => {
    summarySheetData[4][i * 4] = 'Denom'
    summarySheetData[4][i * 4 + 1] = 'Count'
    summarySheetData[4][i * 4 + 2] = 'Value'
  })

  // Denom rows (Rows 5 to 13)
  const denoms = ['500', '200', '100', '50', '20', '10', '5', '2', '1']
  denoms.forEach((d, dIdx) => {
    types.forEach((t, tIdx) => {
      const doc = docs[t]
      const count = doc ? Number(doc[d] || 0) : 0
      const val = count * Number(d)
      summarySheetData[5 + dIdx][tIdx * 4] = Number(d)
      summarySheetData[5 + dIdx][tIdx * 4 + 1] = count
      summarySheetData[5 + dIdx][tIdx * 4 + 2] = val
    })
  })

  // Totals (Row 15, 16, 17)
  types.forEach((t, i) => {
    summarySheetData[15][i * 4] = 'TOTAL BOX'
    summarySheetData[15][i * 4 + 2] = docs[t]?.total || 0

    summarySheetData[16][i * 4] = 'LEDGER BAL'
    summarySheetData[16][i * 4 + 2] = docs[t]?.cash_ledger_balance || 0

    const diff = Number(docs[t]?.difference || 0)
    const status = diff === 0 ? 'Tally' : (diff > 0 ? 'Excess' : 'Short')
    summarySheetData[17][i * 4] = 'DIFFERENCE'
    summarySheetData[17][i * 4 + 2] = diff
    summarySheetData[17][i * 4 + 3] = status
  })

  // ── METADATA (Starting at Column Q, index 16) ─────────────────────
  // Row 0
  summarySheetData[0][16] = 'Biller Name:'
  summarySheetData[0][17] = metadata.billerName
  summarySheetData[0][18] = 'Warehouse:'
  summarySheetData[0][19] = metadata.warehouse
  // Row 1
  summarySheetData[1][16] = 'Cash Account:'
  summarySheetData[1][17] = metadata.cashAccount
  summarySheetData[1][18] = 'Cost Center:'
  summarySheetData[1][19] = metadata.costCenter

  const summarySheet = XLSX.utils.aoa_to_sheet(summarySheetData)
  
  // Apply Column Widths
  const colWidths = []
  // Sessions A-P (4 * 4)
  for (let i = 0; i < 16; i++) {
    colWidths.push({ wch: (i % 4 === 3) ? 2 : 8 }) // Every 4th column is spacer
  }
  // Metadata Q-T
  colWidths[16] = { wch: 15 } // Q
  colWidths[17] = { wch: 25 } // R
  colWidths[18] = { wch: 15 } // S
  colWidths[19] = { wch: 25 } // T
  summarySheet['!cols'] = colWidths

  // Apply Merges for Sheet 1
  const merges = []
  // Session titles (A-C, E-G, etc.)
  types.forEach((t, i) => {
    merges.push({ s: { r: 3, c: i * 4 }, e: { r: 3, c: i * 4 + 2 } }) 
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
  billsSheet['!cols'] = [
    { wch: 20 }, { wch: 30 }, { wch: 12 }, { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 10 }
  ]
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
  ledgerSheet['!cols'] = [
    { wch: 12 }, { wch: 20 }, { wch: 30 }, { wch: 12 }, { wch: 12 }, { wch: 15 }
  ]
  XLSX.utils.book_append_sheet(wb, ledgerSheet, 'Cash Ledger')

  // Generate and Download File
  XLSX.writeFile(wb, `Cashier_Report_${date}.xlsx`)
}
