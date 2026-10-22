const A4 = { widthMm: 210, heightMm: 297 }

/** Canvas px dims -> page count at the canvas's own aspect (A4 width fixed). */
export function pageSliceCount(canvasWidth: number, canvasHeight: number): number {
  if (canvasWidth <= 0 || canvasHeight <= 0) return 1
  const pageRatio = A4.heightMm / A4.widthMm
  const pageHeightPx = canvasWidth * pageRatio
  // relative slack absorbs float/DPI epsilons (1240x1754 IS one A4 page)
  return Math.max(1, Math.ceil(canvasHeight / pageHeightPx - 0.001))
}
