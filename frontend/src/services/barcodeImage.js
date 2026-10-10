/**
 * Decode a barcode from a still photo.
 *
 * Fallback for pages opened over plain http, where browsers block live camera
 * video (getUserMedia needs a secure context) but still let
 * <input type="file" capture> open the phone's own camera app.
 * ZXing is imported lazily so it only downloads when a photo is decoded.
 */

// Phone photos are 12MP+; ZXing is faster and often more accurate on a smaller copy
const TARGET_WIDTHS = [1280, 1920, 800]

async function loadImage(file) {
  const url = URL.createObjectURL(file)
  try {
    const img = new Image()
    img.src = url
    await img.decode()
    return img
  } finally {
    URL.revokeObjectURL(url)
  }
}

function drawScaled(img, width, rotate) {
  const scale = Math.min(1, width / img.naturalWidth)
  const w = Math.round(img.naturalWidth * scale)
  const h = Math.round(img.naturalHeight * scale)
  const canvas = document.createElement('canvas')
  canvas.width = rotate ? h : w
  canvas.height = rotate ? w : h
  const ctx = canvas.getContext('2d')
  if (rotate) {
    // Barcode photographed upright (bars horizontal): turn it 90° for the 1D readers
    ctx.translate(h, 0)
    ctx.rotate(Math.PI / 2)
  }
  ctx.drawImage(img, 0, 0, w, h)
  return canvas
}

/** Returns the decoded text, or null when no barcode was found in the photo. */
export async function decodeBarcodeFromFile(file) {
  const [{ BrowserMultiFormatReader }, { DecodeHintType }] = await Promise.all([
    import('@zxing/browser'),
    import('@zxing/library'),
  ])
  const hints = new Map([[DecodeHintType.TRY_HARDER, true]])
  const reader = new BrowserMultiFormatReader(hints)
  const img = await loadImage(file)

  for (const rotate of [false, true]) {
    for (const width of TARGET_WIDTHS) {
      try {
        const text = reader.decodeFromCanvas(drawScaled(img, width, rotate)).getText()
        if (text) return text.trim()
      } catch (e) {
        // NotFoundException: try the next size / orientation
      }
    }
  }
  return null
}
