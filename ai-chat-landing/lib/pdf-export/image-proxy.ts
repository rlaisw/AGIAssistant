/**
 * Same-origin proxy helpers for the export rasterizer. html2canvas-pro runs
 * with useCORS; cross-origin images whose hosts send no ACAO header fail to
 * load in CORS mode and silently drop out of the PDF. Rewriting them through
 * /api/image-proxy makes them same-origin, so the rasterizer keeps them.
 */

export function needsProxy(src: string, origin: string): boolean {
  let url: URL
  try {
    url = new URL(src, origin)
  } catch {
    return false
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") return false
  return url.origin !== origin
}

export function proxySrc(src: string): string {
  return `/api/image-proxy?url=${encodeURIComponent(src)}`
}

/** Rewrite cross-origin <img> srcs to the proxy, keeping the original URL on
 * data-orig-src so the degrade-to-link path still points at the real source. */
export function rewriteCrossOriginImages(
  container: HTMLElement,
  origin: string = window.location.origin
): void {
  for (const img of Array.from(container.querySelectorAll("img"))) {
    if (!needsProxy(img.src, origin)) continue
    img.setAttribute("data-orig-src", img.src)
    img.src = proxySrc(img.src)
  }
}
