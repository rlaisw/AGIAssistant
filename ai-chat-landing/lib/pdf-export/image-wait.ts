export type ImageDecision = { url: string; embed: boolean }

type ImageLike = { src: string; onload: (() => void) | null; onerror: (() => void) | null }

export type DecideOptions = {
  ImageCtor: new () => ImageLike
  timeoutMs: number
}

/**
 * FR-012: bounded wait on every <img> in the export container; failures
 * (offline, CORS, 404, timeout) degrade to a visible labeled link — never a
 * blank box, broken icon, or silently missing content. Each degrade is
 * warned to console per R6. `doc` is injectable for node-env tests.
 */
export async function embedOrDegradeImages(
  container: HTMLElement,
  opts: { timeoutMs?: number; doc?: { createElement(tag: string): unknown } } = {}
): Promise<void> {
  const timeoutMs = opts.timeoutMs ?? 8000
  const doc = opts.doc ?? document
  const imgs = Array.from(container.querySelectorAll("img")) as HTMLImageElement[]
  await Promise.all(
    imgs.map(
      (img) =>
        new Promise<void>((resolve) => {
          let settled = false
          const finish = () => {
            if (settled) return
            settled = true
            clearTimeout(timer)
            resolve()
          }
          const degrade = (reason: string) => {
            // prefer the pre-proxy URL when the src was rewritten (image-proxy)
            const original = img.getAttribute?.("data-orig-src") ?? img.src
            console.warn(`[pdf-export] image degraded to link (${reason}):`, original)
            const link = doc.createElement("a") as HTMLAnchorElement
            link.href = original
            link.textContent = img.alt || original
            img.replaceWith(link as unknown as Node)
            finish()
          }
          const loaded = () => {
            if (img.naturalWidth > 0) finish()
            else degrade("zero-size")
          }
          const timer = setTimeout(() => degrade("timeout"), timeoutMs)
          if (img.complete && img.naturalWidth > 0) {
            finish()
            return
          }
          img.addEventListener("load", loaded, { once: true })
          img.addEventListener("error", () => degrade("error"), { once: true })
        })
    )
  )
}

export function decideImages(urls: string[], opts: DecideOptions): Promise<ImageDecision[]> {
  return Promise.all(
    urls.map(
      (url) =>
        new Promise<ImageDecision>((resolve) => {
          const img = new opts.ImageCtor()
          let settled = false
          const finish = (embed: boolean) => {
            if (settled) return
            settled = true
            clearTimeout(timer)
            resolve({ url, embed })
          }
          const timer = setTimeout(() => finish(false), opts.timeoutMs)
          img.onload = () => finish(true)
          img.onerror = () => finish(false)
          img.src = url
        })
    )
  )
}
