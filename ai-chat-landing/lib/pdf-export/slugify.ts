const MAX_SLUG = 40

function timestampName(): string {
  const now = new Date()
  const p = (n: number, w = 2) => String(n).padStart(w, "0")
  return `chat-${now.getFullYear()}${p(now.getMonth() + 1)}${p(now.getDate())}-${p(now.getHours())}${p(now.getMinutes())}${p(now.getSeconds())}.pdf`
}

export function slugifyFilename(firstQuestion?: string): string {
  const slug = (firstQuestion ?? "")
    .toLowerCase()
    .replace(/['’]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, MAX_SLUG)
  return slug ? `${slug}.pdf` : timestampName()
}
