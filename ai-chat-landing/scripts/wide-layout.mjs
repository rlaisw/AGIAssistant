#!/usr/bin/env node
// Spec 016 wide-chat-layout acceptance script (persisted per tasks.md T013).
// Layout measurement (T1-T7, T9 structural) always runs; behavioral smoke
// (buckets / Load more / PDF export / delete, T014+T015) runs with --smoke.
// The smoke creates one throwaway conversation and deletes it — it never
// touches existing conversations.
// Chrome: --remote-debugging-port=9240 · app: pnpm dev on :3000.

import { mkdirSync, readdirSync, statSync, copyFileSync } from "node:fs"
import { argv } from "node:process"

const CDP = "http://localhost:9240"
const APP = "http://localhost:3000"
const SMOKE = argv.includes("--smoke")
const DOWNLOADS = "/tmp/kilo/cdp/downloads"
const BASELINE = "/tmp/kilo/cdp/pdf-baseline.pdf"
const MARKER = `016-smoke-${Date.now()}`

function die(msg) { console.error(`✗ ${msg}`); process.exit(1) }

const version = await fetch(`${CDP}/json/version`).then(r => {
  if (!r.ok) die(`Chrome CDP ${CDP} unreachable (HTTP ${r.status}) — start Chrome with --remote-debugging-port=9240`)
  return r.json()
}).catch(() => die(`Chrome CDP ${CDP} unreachable — start Chrome with --remote-debugging-port=9240`))
console.log(`CDP ok: ${version.Browser}`)

const home = await fetch(APP).then(r => r.status).catch(() => die(`${APP} not serving — start pnpm dev in ai-chat-landing/`))
if (home !== 200) die(`${APP} returned HTTP ${home} — expected 200 from pnpm dev`)
console.log(`App ok: ${APP} (HTTP 200)`)

if (typeof WebSocket === "undefined") die("global WebSocket missing — run with Node >= 22")

const tab = await fetch(`${CDP}/json/new`, { method: "PUT" }).then(r => r.json())
  .catch(() => die("could not open a tab via /json/new"))
const ws = new WebSocket(tab.webSocketDebuggerUrl)
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("websocket connect failed")) })

let seq = 0
const pending = new Map()
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data)
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id) }
}
function send(method, params = {}) {
  return new Promise((res, rej) => {
    const id = ++seq
    pending.set(id, res)
    ws.send(JSON.stringify({ id, method, params }))
    setTimeout(() => rej(new Error(`CDP timeout: ${method}`)), 5000)
  })
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms))
async function evalJS(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })
  if (r.error) throw new Error(`Runtime.evaluate: ${JSON.stringify(r.error)}`)
  if (r.exceptionDetails) throw new Error(`page exception: ${JSON.stringify(r.exceptionDetails)}`)
  return r.result.result.value
}

const WIDE = 'xl:max-w-[min(90%,1400px)]'
const SEL_COLUMN = `[class*="${WIDE}"][class*="space-y-6"]`
const SEL_COMPOSER = `[class*="${WIDE}"][class*="p-3"]`

async function setViewport(width, height) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false })
  await evalJS("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
}

async function widths() {
  const w = await evalJS(`(() => {
    const c = document.querySelector('${SEL_COLUMN}')
    const p = document.querySelector('${SEL_COMPOSER}')
    if (!c) return { missing: '${SEL_COLUMN}' }
    if (!p) return { missing: '${SEL_COMPOSER}' }
    return { column: c.getBoundingClientRect().width, composer: p.getBoundingClientRect().width }
  })()`)
  if (w.missing) die(`Selector not found: ${w.missing} — class strings drifted (spec 016 contract)`)
  return w
}

// Spec 020: the app lands on the empty state — the chat column only exists
// once a conversation has messages, so open the first history row first.
async function openFirstConversation() {
  await evalJS(`(() => {
    const btn = document.querySelector('button[aria-label="Conversation options"]')
    const row = btn?.closest('div')
    const openBtn = row ? [...row.querySelectorAll('button')].find(b => b.getAttribute('aria-label') !== 'Conversation options') : null
    openBtn?.click()
    return !!openBtn
  })()`)
  for (let i = 0; i < 30; i++) {
    const ok = await evalJS(`!!document.querySelector('${SEL_COLUMN}')`).catch(() => false)
    if (ok) return
    await sleep(500)
  }
  die("message column did not render after opening a history conversation")
}

function approx(a, b, tol = 2) { return Math.abs(a - b) <= tol }
const fails = []
function check(name, ok, detail) {
  console.log(`${ok ? "✓" : "✗"} ${name} — ${detail}`)
  if (!ok) fails.push(name)
}

await send("Page.enable")
await send("Page.navigate", { url: APP })
for (let i = 0; i < 60; i++) {
  try { if (await evalJS("document.readyState") === "complete") break } catch {}
  await sleep(500)
}
await openFirstConversation()

// T1 1440×900 sidebar open: 90% of (1440-256=1184) ≈ 1065.6
await setViewport(1440, 900)
let w = await widths()
check("T1 1440×900 sidebar open ≥85% of 1184px", w.column >= 1184 * 0.85 - 1, `column=${w.column.toFixed(1)}px composer=${w.composer.toFixed(1)}px`)
check("T1 column ≈ 90% of 1184px (± one scrollbar)", w.column >= 1184 * 0.9 - 20 && w.column <= 1184 * 0.9 + 3, `column=${w.column.toFixed(1)}px`)
check("T1 composer ≈ column (± one scrollbar)", Math.abs(w.column - w.composer) <= 20, `Δ=${Math.abs(w.column - w.composer).toFixed(1)}px`)

// T2 sidebar closed: 90% of 1440 = 1296
await evalJS(`document.querySelector('button[aria-label="Toggle sidebar"]')?.click(); true`)
await setViewport(1440, 900)
w = await widths()
check("T2 1440×900 sidebar closed ≈1296px (± one scrollbar)", w.column >= 1296 - 20 && w.column <= 1296 + 3, `column=${w.column.toFixed(1)}px`)
await evalJS(`document.querySelector('button[aria-label="Toggle sidebar"]')?.click(); true`)

// T3 1920×1080: cap binds at 1400
await setViewport(1920, 1080)
w = await widths()
check("T3 1920×1080 cap = 1400px", approx(w.column, 1400, 1), `column=${w.column.toFixed(1)}px`)

// T4 1280×800: xl active ≈ 921.6
await setViewport(1280, 800)
w = await widths()
check("T4 1280×800 ≈922px (wider than 768, ± one scrollbar)", w.column >= 921.6 - 20 && w.column <= 921.6 + 3, `column=${w.column.toFixed(1)}px`)

// T5 1279×800: xl inactive → ≤768
await setViewport(1279, 800)
w = await widths()
check("T5 1279×800 ≤768px (xl inactive)", w.column <= 768.5, `column=${w.column.toFixed(1)}px`)

// T5b 1024×768 (SC-002 spot-check): xl inactive → column capped at 768px
await setViewport(1024, 768)
w = await widths()
check("T5b 1024×768 ≤768px (SC-002 spot-check)", w.column <= 768.5, `column=${w.column.toFixed(1)}px`)

// T6 390×844: mobile full width minus padding, drawer starts closed
await setViewport(390, 844)
// Fresh load at mobile width: the spec-019 drawer must start closed
await send("Page.navigate", { url: APP })
for (let i = 0; i < 30; i++) {
  try { if (await evalJS("document.readyState") === "complete") break } catch {}
  await sleep(500)
}
const sidebarVisible = await evalJS(`(() => { const a = document.querySelector('aside.w-64'); return a ? getComputedStyle(a).display !== 'none' : false })()`)
check("T6 390×844 drawer closed on fresh load (spec 019)", !sidebarVisible, `sidebar visible: ${sidebarVisible}`)
await evalJS(`document.querySelector('button[aria-label="Toggle sidebar"]')?.click(); true`)
await sleep(400)
await openFirstConversation()
w = await widths()
check("T6 390×844 full-bleed column (± one scrollbar)", w.column >= 390 - 20 && w.column <= 390 + 4, `column=${w.column.toFixed(1)}px`)

// T7 1440×900: synthetic long user bubble ≤672px (measures the CSS contract
// inside the real column; the send path is exercised in --smoke)
// Fresh load at desktop: T6's mobile load closed the drawer (spec 019)
await setViewport(1440, 900)
await send("Page.navigate", { url: APP })
for (let i = 0; i < 30; i++) {
  try { if (await evalJS("document.readyState") === "complete") break } catch {}
  await sleep(500)
}
await openFirstConversation()
const bubble = await evalJS(`(() => {
  const col = document.querySelector('${SEL_COLUMN}')
  if (!col) return { missing: 'column' }
  const row = document.createElement('div')
  row.className = 'flex justify-end'
  const b = document.createElement('div')
  b.className = 'max-w-[85%] lg:max-w-2xl rounded-2xl bg-primary px-4 py-2.5 text-sm text-primary-foreground'
  b.textContent = 'x'.repeat(2000)
  row.appendChild(b); col.appendChild(row)
  const width = b.getBoundingClientRect().width
  row.remove()
  return { width }
})()`)
check("T7 long user bubble ≤672px", bubble.width <= 672.5, `bubble=${bubble.width.toFixed(1)}px`)

// T9 (structural): sidebar + New chat + PdfExportButton present
const smoke = await evalJS(`(() => ({
  sidebar: !!document.querySelector('aside.w-64'),
  newChat: !!document.querySelector('aside button.w-full'),
  pdfBtn: !!document.querySelector('button[aria-label="Download conversation as PDF"]'),
  toggle: !!document.querySelector('button[aria-label="Toggle sidebar"]'),
}))()`)
check("T9 sidebar present", smoke.sidebar, JSON.stringify(smoke))
check("T9 New chat button", smoke.newChat, "")
check("T9 PDF export button", smoke.pdfBtn, "")

if (!SMOKE) {
  console.log(`\nBehavioral smoke skipped (run with --smoke).`)
  ws.close()
  if (fails.length) die(`${fails.length} FAILED: ${fails.join(", ")}`)
  console.log("\nAll automated checks passed (T1–T7, T9 structural).")
  process.exit(0)
}

// ---- Behavioral smoke (T014 buckets/Load-more/delete, T015 PDF baseline) ----
console.log("\n--smoke: behavioral checks at 1440×900")

async function rowCount() {
  return await evalJS(`document.querySelectorAll('button[aria-label="Conversation options"]').length`)
}

// Wait for history (status ready) — poll rows
let rows = 0
for (let i = 0; i < 20; i++) {
  rows = await rowCount()
  if (rows > 0) break
  await sleep(500)
}
console.log(rows > 0 ? `✓ history rows present: ${rows}` : `⚠ no backend history rows — continuing with throwaway only`)
const buckets = await evalJS(`[...document.querySelectorAll('aside .text-xs.font-medium')].map(e => e.textContent.trim()).filter(Boolean)`)
console.log(`✓ bucket headers rendered: ${JSON.stringify(buckets)}`)

// Load more (only if a second page exists)
const loadMore = await evalJS(`(() => {
  const btns = [...document.querySelectorAll('aside button')].filter(b => b.textContent.includes('Load more'))
  return btns.length
})()`)
if (loadMore > 0) {
  const before = await rowCount()
  await evalJS(`(() => { const b = [...document.querySelectorAll('aside button')].find(x => x.textContent.includes('Load more')); b?.click(); return true })()`)
  let after = before
  for (let i = 0; i < 24; i++) { after = await rowCount(); if (after > before) break; await sleep(500) }
  check("T014 Load more paginates", after > before, `rows ${before} → ${after}`)
} else {
  console.log("✓ Load more not present (single page) — pagination not exercised")
}

// Create a throwaway conversation (real send through Dify) — start from a
// fresh draft so the throwaway never merges into the initial demo thread
await evalJS(`document.querySelector('aside button.w-full')?.click(); true`)
await sleep(500)
const beforeCreate = await rowCount()
const typed = await evalJS(`(() => {
  const ta = document.querySelector('textarea')
  if (!ta) return false
  const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set
  set.call(ta, '${MARKER} please reply with one short sentence')
  ta.dispatchEvent(new Event('input', { bubbles: true }))
  ta.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
  return true
})()`)
if (!typed) die("composer textarea not found")
let afterCreate = beforeCreate
for (let i = 0; i < 120; i++) {
  afterCreate = await rowCount()
  if (afterCreate > beforeCreate) break
  await sleep(1000)
}
check("T014 send → conversation appears in sidebar", afterCreate > beforeCreate, `rows ${beforeCreate} → ${afterCreate}`)

// Give the reply a moment; export only needs the first chunks, and deleting
// mid-stream is spec-015-verified safe, so we don't wait for the full reply.
await sleep(6000)
for (let i = 0; i < 15; i++) {
  const idle = await evalJS(`(() => { const b = document.querySelector('button[aria-label="Send message"]'); return !b || !b.disabled })()`)
  if (idle) break
  await sleep(1000)
}
mkdirSync(DOWNLOADS, { recursive: true })
const browserWs = new WebSocket(version.webSocketDebuggerUrl)
await new Promise((res, rej) => { browserWs.onopen = res; browserWs.onerror = () => rej(new Error("browser ws failed")) })
browserWs.send(JSON.stringify({ id: 1, method: "Browser.setDownloadBehavior", params: { behavior: "allow", downloadPath: DOWNLOADS, eventsEnabled: true } }))
const preFiles = new Set(readdirSync(DOWNLOADS))
await evalJS(`document.querySelector('button[aria-label="Download conversation as PDF"]')?.click(); true`)
let pdfName = null
for (let i = 0; i < 60; i++) {
  for (const f of readdirSync(DOWNLOADS)) {
    if (f.endsWith(".pdf") && !preFiles.has(f)) {
      try { if (statSync(`${DOWNLOADS}/${f}`).size > 1000) { pdfName = f; break } } catch {}
    }
  }
  if (pdfName) break
  await sleep(1000)
}
if (!pdfName) die("PDF export did not produce a file within 60s (FR-004 live check)")
copyFileSync(`${DOWNLOADS}/${pdfName}`, BASELINE)
const pdfSize = statSync(BASELINE).size
check("T015 PDF export produces a file (FR-004 live)", pdfSize > 1000, `baseline saved: ${BASELINE} (${(pdfSize / 1024).toFixed(1)} KiB) — baseline-established per SC-004`)

// Delete the throwaway conversation via the 015 flow
const deleted = await evalJS(`(async () => {
  const rows = [...document.querySelectorAll('aside button[aria-label="Conversation options"]')]
  const row = rows.map(btn => btn.closest('div')).find(d => d?.textContent.includes('${MARKER}'))
  if (!row) return { step: 'row-not-found' }
  row.querySelector('button[aria-label="Conversation options"]').click()
  await new Promise(r => setTimeout(r, 300))
  const item = [...document.querySelectorAll('[role="menuitem"]')].find(el => el.textContent.includes('Delete'))
  if (!item) return { step: 'menu-item-not-found' }
  item.click()
  await new Promise(r => setTimeout(r, 300))
  const confirmBtn = row.querySelector('button[aria-label="Confirm delete"]')
  if (!confirmBtn) return { step: 'confirm-not-found' }
  confirmBtn.click()
  return { step: 'confirmed' }
})()`)
if (deleted.step !== "confirmed") die(`delete flow stalled at: ${deleted.step}`)
// The confirming state unmounts the "…" button, so the button count dips
// before the row is actually gone — wait on the marker text leaving the
// sidebar instead, then recount.
let gone = false
for (let i = 0; i < 30; i++) {
  gone = await evalJS(`!document.querySelector('aside')?.textContent.includes('${MARKER}')`)
  if (gone) break
  await sleep(500)
}
const afterDelete = await rowCount()
check("T014 delete flow removes the throwaway row", gone && afterDelete === beforeCreate, `rows ${afterCreate} → ${afterDelete}, marker gone: ${gone}`)

ws.close()
browserWs.close()
if (fails.length) die(`${fails.length} FAILED: ${fails.join(", ")}`)
console.log("\nAll automated checks passed (T1–T7, T9 structural" + (SMOKE ? ", T14/T15 behavioral" : "") + ").")
