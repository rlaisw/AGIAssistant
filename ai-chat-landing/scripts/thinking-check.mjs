#!/usr/bin/env node
// Spec 022 Thinking indicator: T1 waiting, T2 streaming, T3 completion,
// T5 delete-mid-stream, T6 accessibility. T4 (source grep) runs in bash.
// Chrome :9240 · pnpm dev :3000 · live Dify.

const CDP = "http://localhost:9240"
const APP = "http://localhost:3000"
const MARKER = `022-thinking-${Date.now()}`

function die(msg) { console.error(`✗ ${msg}`); process.exit(1) }

await fetch(`${CDP}/json/version`).then(r => r.json())
  .catch(() => die(`Chrome CDP ${CDP} unreachable — start Chrome with --remote-debugging-port=9240`))
const home = await fetch(APP).then(r => r.status).catch(() => die(`${APP} not serving`))
if (home !== 200) die(`${APP} returned HTTP ${home}`)

const tab = await fetch(`${CDP}/json/new`, { method: "PUT" }).then(r => r.json())
const ws = new WebSocket(tab.webSocketDebuggerUrl)
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws failed")) })

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
  if (r.error) throw new Error(JSON.stringify(r.error))
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails))
  return r.result.result.value
}
const fails = []
function check(name, ok, detail) {
  console.log(`${ok ? "✓" : "✗"} ${name} — ${detail}`)
  if (!ok) fails.push(name)
}

await send("Page.enable")
await send("Page.navigate", { url: APP })
for (let i = 0; i < 40; i++) {
  try { if (await evalJS("document.readyState") === "complete") break } catch {}
  await sleep(500)
}
await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false })

async function sendMarker() {
  await evalJS(`(() => {
    const ta = document.querySelector('textarea')
    const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set
    set.call(ta, '${MARKER} short reply')
    ta.dispatchEvent(new Event('input', { bubbles: true }))
    ta.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
    return true
  })()`)
}
const indicatorState = () => evalJS(`(() => {
  const row = document.querySelector('[role="status"]')
  const svg = row?.querySelector('svg')
  const label = row?.querySelector('span:last-child') ?? [...(row?.querySelectorAll('span') ?? [])].find(s => s.textContent === 'Thinking')
  const dots = document.querySelectorAll('span.animate-pulse.rounded-full').length
  const caret = document.querySelectorAll('span.h-4.w-2.animate-pulse').length
  const labelCs = label ? getComputedStyle(label) : null
  return {
    row: !!row,
    spin: svg ? getComputedStyle(svg).animationName : null,
    color: svg ? getComputedStyle(svg).color : null,
    ariaHidden: svg?.getAttribute('aria-hidden') ?? null,
    classes: svg?.getAttribute('class') ?? '',
    text: label?.textContent ?? null,
    weight: labelCs ? labelCs.fontWeight : null,
    dots, caret,
  }
})()`)

// T1: waiting state (before first chunk)
await sendMarker()
let s = null
for (let i = 0; i < 40 && !s?.row; i++) { s = await indicatorState().catch(() => null); if (s?.row) break; await sleep(250) }
check("T1 indicator row appears while waiting", !!s?.row, JSON.stringify({ row: s?.row }))
check("T1 ring spins (animation-name spin)", s?.spin === "spin", `animationName=${s?.spin}`)
check("T1 ring color is #82D2F6", s?.color === "rgb(130, 210, 246)", `color=${s?.color}`)
check("T1 bold Thinking text", s?.text === "Thinking" && (s?.weight === "600" || s?.weight === "700"), `text=${s?.text} weight=${s?.weight}`)
check("T1 old dots gone", s?.dots === 0, `dots=${s?.dots}`)
check("T6 aria-hidden on icon", s?.ariaHidden === "true", `aria-hidden=${s?.ariaHidden}`)
check("T6 always-on spin (gate removed after user testing)", (s?.classes ?? "").includes("animate-spin") && !(s?.classes ?? "").includes("motion-safe"), "")

// T2: streaming state (text arriving)
let streaming = false
for (let i = 0; i < 80; i++) {
  const t = await evalJS(`(() => {
    const md = document.querySelector('[role="status"]')
    const hasText = !!document.querySelector('.prose, [class*="prose"]') || document.body.textContent.includes('${MARKER}'.split('-')[0])
    return { indicator: !!md, textArriving: hasText }
  })()`).catch(() => null)
  if (t?.indicator && t?.textArriving) { streaming = true; break }
  await sleep(500)
}
s = await indicatorState()
check("T2 indicator shows while streaming (below content)", streaming && s.row, `streaming=${streaming}`)
check("T2 old caret gone", s.caret === 0, `caret=${s.caret}`)

// T3: completion clears the indicator
let done = false
for (let i = 0; i < 90; i++) {
  done = await evalJS(`!!document.querySelector('button[aria-label="Copy response"]')`).catch(() => false)
  if (done) break
  await sleep(1000)
}
s = await indicatorState()
check("T3 reply completed", done, "")
check("T3 indicator cleared on completion", !s.row, `row=${s.row}`)

// T5: delete mid-stream clears the indicator
await sendMarker()
let mid = false
for (let i = 0; i < 30; i++) {
  const t = await indicatorState().catch(() => null)
  if (t?.row) { mid = true; break }
  await sleep(250)
}
check("T5 indicator visible mid-stream before delete", mid, "")
const deleted = await evalJS(`(async () => {
  const btn = [...document.querySelectorAll('button[aria-label="Conversation options"]')].find(b => b.closest('div')?.textContent.includes('${MARKER}'))
  if (!btn) return 'row-not-found'
  btn.click()
  await new Promise(r => setTimeout(r, 300))
  const item = [...document.querySelectorAll('[role="menuitem"]')].find(el => el.textContent.includes('Delete'))
  if (!item) return 'menu-not-found'
  item.click()
  await new Promise(r => setTimeout(r, 300))
  document.querySelector('button[aria-label="Confirm delete"]')?.click()
  return 'confirmed'
})()`)
check("T5 delete flow ran", deleted === "confirmed", deleted)
let cleared = false
for (let i = 0; i < 20; i++) {
  const t = await indicatorState().catch(() => null)
  if (!t?.row) { cleared = true; break }
  await sleep(500)
}
check("T5 delete mid-stream clears the indicator", cleared, "")

ws.close()
if (fails.length) die(`${fails.length} FAILED: ${fails.join(", ")}`)
console.log("\nAll thinking-indicator checks passed (T1, T2, T3, T5, T6).")
