// Hands a File from one page to Document Print without saving it anywhere.
// The sender sets it right before navigating; Document Print takes it once on mount.
let pending = null

export function sendToDocumentPrint(router, file, returnTo) {
  pending = { file, returnTo }
  router.push({ name: 'DocumentPrint' })
}

export function takePendingPrint() {
  const p = pending
  pending = null
  return p
}
