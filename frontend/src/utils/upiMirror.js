// "Mandatory UPI/Card Mirror Series" (Automatic Entries): a bill from one of these
// series that is posted with a UPI or Card amount is offered for mirroring to the
// Alternative Company. Prefixes match the way the server matches mirror series.
export function isMandatoryUpiMirrorSeries(namingSeries) {
  const series = String(namingSeries || '').trim()
  if (!series) return false
  return String(localStorage.getItem('ae-mandatory-upi-mirror-series') || '')
    .split(/[,\n]/)
    .map(s => s.trim())
    .filter(Boolean)
    .some(prefix => series === prefix || series.startsWith(prefix))
}

export function shouldAskUpiMirror(upiAmount, cardAmount, namingSeries) {
  return (Number(upiAmount) > 0.01 || Number(cardAmount) > 0.01)
    && !!localStorage.getItem('ae-alternative_company')
    && isMandatoryUpiMirrorSeries(namingSeries)
}

// The server already queued the automatic mirror, or a mirror bill already exists:
// asking again would create a duplicate.
export function mirrorAlreadyHandled(submitResult) {
  return !!(submitResult?.mirror_queued || submitResult?.mirrored)
}
