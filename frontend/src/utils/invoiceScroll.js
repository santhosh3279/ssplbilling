export function scrollInvoiceRowIntoView(rowEl, direction) {
  if (!rowEl) return
  const container = rowEl.closest('.overflow-y-auto')
  if (!container) return
  const rowRect = rowEl.getBoundingClientRect()
  const cRect = container.getBoundingClientRect()
  // The sticky header covers part of the scroll viewport. Native
  // scrollIntoView considers that covered area visible and can hide a row there.
  const theadH = container.querySelector('thead')?.getBoundingClientRect().height || 0
  const visibleTop = cRect.top + container.clientTop + theadH
  const visibleBottom = cRect.top + container.clientTop + container.clientHeight
  if (rowRect.bottom > visibleBottom && (direction === 'down' || rowRect.top >= visibleTop)) {
    container.scrollTop += rowRect.bottom - visibleBottom
  } else if (rowRect.top < visibleTop) {
    container.scrollTop += rowRect.top - visibleTop
  }
}
