import ExcelJS from 'exceljs'

/**
 * Generates a multi-sheet XLSX report for the cashier's daily activities using exceljs for styling.
 */
export async function generateCashierReport(data) {
  const { date, docs, bills, ledgerEntries, ledgerOpening, metadata, getMopAmount } = data
  const workbook = new ExcelJS.Workbook()
  workbook.creator = 'Gemini CLI'
  workbook.created = new Date()

  // ── SHEET 1: DAILY CASH SUMMARY ───────────────────────────────────
  const summarySheet = workbook.addWorksheet('Daily Cash Summary', {
    views: [{ showGridLines: false }]
  })

  const types = ['Opening', 'Mid-Day-1', 'Mid-Day-2', 'Closing']
  const denoms = ['500', '200', '100', '50', '20', '10', '5', '2', '1']

  const thinBorder = {
    top: { style: 'thin' },
    left: { style: 'thin' },
    bottom: { style: 'thin' },
    right: { style: 'thin' }
  }

  // Session Headers (Row 1)
  types.forEach((t, i) => {
    const col = i * 4 + 1
    summarySheet.mergeCells(1, col, 1, col + 2)
    const cell = summarySheet.getCell(1, col)
    cell.value = t.toUpperCase()
    cell.font = { bold: true, color: { argb: 'FFFFFFFF' } }
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1E293B' } }
    cell.alignment = { horizontal: 'center' }
    // Apply borders to merged range
    for (let c = col; c <= col + 2; c++) {
      summarySheet.getCell(1, c).border = thinBorder
    }
  })

  // Sub Headers (Row 2)
  types.forEach((t, i) => {
    const col = i * 4 + 1
    const subHeaders = ['Denom', 'Count', 'Value']
    subHeaders.forEach((sh, shIdx) => {
      const cell = summarySheet.getCell(2, col + shIdx)
      cell.value = sh
      cell.font = { bold: true }
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF1F5F9' } }
      cell.border = thinBorder
    })
  })

  // Denom Rows (Starting Row 3)
  denoms.forEach((d, dIdx) => {
    const row = 3 + dIdx
    types.forEach((t, tIdx) => {
      const col = tIdx * 4 + 1
      const doc = docs[t]
      const count = doc ? Number(doc[d] || 0) : 0
      const val = count * Number(d)
      const c1 = summarySheet.getCell(row, col)
      c1.value = Number(d)
      c1.border = thinBorder
      const c2 = summarySheet.getCell(row, col + 1)
      c2.value = count
      c2.border = thinBorder
      const c3 = summarySheet.getCell(row, col + 2)
      c3.value = val
      c3.border = thinBorder
    })
  })

  // Totals Section (Row 13, 14, 15)
  const footerStart = 13
  types.forEach((t, i) => {
    const col = i * 4 + 1
    const doc = docs[t]

    // TOTAL BOX
    const totalCellLabel = summarySheet.getCell(footerStart, col)
    totalCellLabel.value = 'TOTAL BOX'
    totalCellLabel.font = { bold: true }
    totalCellLabel.border = thinBorder
    summarySheet.getCell(footerStart, col + 1).border = thinBorder
    const totalValCell = summarySheet.getCell(footerStart, col + 2)
    totalValCell.value = doc?.total || 0
    totalValCell.font = { bold: true }
    totalValCell.border = thinBorder

    // LEDGER BAL
    const ledgerCellLabel = summarySheet.getCell(footerStart + 1, col)
    ledgerCellLabel.value = 'LEDGER BAL'
    ledgerCellLabel.border = thinBorder
    summarySheet.getCell(footerStart + 1, col + 1).border = thinBorder
    const ledgerValCell = summarySheet.getCell(footerStart + 1, col + 2)
    ledgerValCell.value = doc?.cash_ledger_balance || 0
    ledgerValCell.border = thinBorder

    // DIFFERENCE
    const diff = Number(doc?.difference || 0)
    const status = diff === 0 ? 'Tally' : (diff > 0 ? 'Excess' : 'Short')
    const color = diff >= 0 ? 'FF10B981' : 'FFFF0000'

    const diffCellLabel = summarySheet.getCell(footerStart + 2, col)
    diffCellLabel.value = 'DIFFERENCE'
    diffCellLabel.border = thinBorder
    summarySheet.getCell(footerStart + 2, col + 1).border = thinBorder
    const diffValCell = summarySheet.getCell(footerStart + 2, col + 2)
    diffValCell.value = diff
    diffValCell.font = { bold: true, color: { argb: color } }
    diffValCell.border = thinBorder

    const statusCell = summarySheet.getCell(footerStart + 2, col + 3)
    statusCell.value = status
    statusCell.font = { bold: true, color: { argb: color } }
    statusCell.border = thinBorder
  })

  // ── METADATA (Column Q Headings (17), Column R Values (18)) ───────
  const metaRows = [
    { label: 'Biller Name:', value: metadata.billerName },
    { label: 'Warehouse:', value: metadata.warehouse },
    { label: 'Cash Account:', value: metadata.cashAccount },
    { label: 'Cost Center:', value: metadata.costCenter }
  ]

  metaRows.forEach((item, i) => {
    const row = i + 1
    const labelCell = summarySheet.getCell(row, 17)
    labelCell.value = item.label
    labelCell.font = { bold: true }
    labelCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF8FAFC' } }
    labelCell.border = thinBorder
    
    summarySheet.mergeCells(row, 18, row, 20)
    for (let c = 18; c <= 20; c++) {
      const cell = summarySheet.getCell(row, c)
      if (c === 18) cell.value = item.value
      cell.border = thinBorder
    }
  })

  // Column Widths Sheet 1
  summarySheet.columns = Array(20).fill({ width: 10 })
  for (let i = 1; i <= 16; i++) {
    summarySheet.getColumn(i).width = (i % 4 === 0) ? 2 : 12
  }
  summarySheet.getColumn(17).width = 18 // Q
  summarySheet.getColumn(18).width = 40 // R

  // ── SHEET 2: TODAY'S BILLS ────────────────────────────────────────
  const billsSheet = workbook.addWorksheet('Today Bills')
  
  // Dynamic width calculation
  const maxCustomerLen = Math.max(15, ...bills.map(b => b.customer?.length || 0))

  billsSheet.columns = [
    { header: 'Bill No', key: 'name', width: 22 },
    { header: 'Customer', key: 'customer', width: maxCustomerLen + 5 },
    { header: 'Total', key: 'total', width: 15 },
    { header: 'Cash', key: 'cash', width: 12 },
    { header: 'UPI', key: 'upi', width: 12 },
    { header: 'Card', key: 'card', width: 12 },
    { header: 'Credit', key: 'credit', width: 12 }
  ]

  // Header Style
  billsSheet.getRow(1).height = 20
  billsSheet.getRow(1).font = { bold: true, color: { argb: 'FFFFFFFF' } }
  billsSheet.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1E293B' } }
  billsSheet.getRow(1).alignment = { vertical: 'middle', horizontal: 'center' }
  billsSheet.getRow(1).eachCell((cell) => { cell.border = thinBorder })

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

    const row = billsSheet.addRow({
      name: bill.name,
      customer: bill.customer,
      total: bill.grand_total,
      cash,
      upi,
      card,
      credit
    })
    row.eachCell((cell, colNum) => { 
      cell.border = thinBorder 
      if (colNum >= 3) cell.alignment = { horizontal: 'right' }
    })
  })

  const billsTotalRow = billsSheet.addRow({
    name: 'TOTAL',
    customer: '',
    total: totalSales,
    cash: totalsMop.cash,
    upi: totalsMop.upi,
    card: totalsMop.card,
    credit: totalsMop.credit
  })
  billsTotalRow.font = { bold: true }
  billsTotalRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF1F5F9' } }
  billsTotalRow.eachCell((cell, colNum) => { 
    cell.border = thinBorder 
    if (colNum >= 3) cell.alignment = { horizontal: 'right' }
  })

  // ── SHEET 3: CASH LEDGER ──────────────────────────────────────────
  const ledgerSheet = workbook.addWorksheet('Cash Ledger')
  
  const maxPartyLen = Math.max(15, ...ledgerEntries.map(e => e.party?.length || 0))

  ledgerSheet.columns = [
    { header: 'Time', key: 'time', width: 15 },
    { header: 'Voucher No', key: 'voucher_no', width: 25 },
    { header: 'Party', key: 'party', width: maxPartyLen + 5 },
    { header: 'Debit (DR)', key: 'debit', width: 15 },
    { header: 'Credit (CR)', key: 'credit', width: 15 },
    { header: 'Balance', key: 'balance', width: 18 }
  ]

  ledgerSheet.getRow(1).height = 20
  ledgerSheet.getRow(1).font = { bold: true, color: { argb: 'FFFFFFFF' } }
  ledgerSheet.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1E293B' } }
  ledgerSheet.getRow(1).alignment = { vertical: 'middle', horizontal: 'center' }
  ledgerSheet.getRow(1).eachCell((cell) => { cell.border = thinBorder })

  const openingRow = ledgerSheet.addRow({
    time: '',
    voucher_no: 'OPENING BALANCE',
    party: '',
    debit: '',
    credit: '',
    balance: ledgerOpening
  })
  openingRow.font = { italic: true, bold: true }
  openingRow.eachCell((cell, colNum) => { 
    cell.border = thinBorder 
    if (colNum >= 4) cell.alignment = { horizontal: 'right' }
  })

  ledgerEntries.forEach(entry => {
    const row = ledgerSheet.addRow({
      time: entry.time,
      voucher_no: entry.voucher_no,
      party: entry.party || '',
      debit: entry.debit || 0,
      credit: entry.credit || 0,
      balance: entry.balance || 0
    })
    row.eachCell((cell, colNum) => { 
      cell.border = thinBorder 
      if (colNum >= 4) cell.alignment = { horizontal: 'right' }
    })
  })

  // Final Balance Styling
  if (ledgerSheet.rowCount > 1) {
    const lastRow = ledgerSheet.getRow(ledgerSheet.rowCount)
    lastRow.font = { bold: true }
    lastRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF1F5F9' } }
    lastRow.eachCell((cell) => { cell.border = thinBorder })
  }


  // Generate and Download
  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `Cashier_Report_${date}.xlsx`
  link.click()
  window.URL.revokeObjectURL(url)
}
