#!/usr/bin/env node
// Spec 020 landing-page checks: T1/T2 fresh-load empty state, T4 first send.
// Chrome :9240 · pnpm dev :3000 · live Dify for T4.

const CDP = "http://localhost:9240"
const APP = "http://localhost:3000"
const MARKER = `020-landing-${Date.now()}`

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
async function navigateAndWait(width, height) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false })
  await send("Page.navigate", { url: APP })
  for (let i = 0; i < 40; i++) {
    try { if (await evalJS("document.readyState") === "complete") break } catch {}
    await sleep(500)
  }
  await sleep(800)
}
const landingState = () => evalJS(`(() => {
  const headerTitle = document.querySelector('header span.truncate')?.textContent ?? ''
  const emptyState = document.body.textContent.includes('How can I help you today?')
  const userBubbles = document.querySelectorAll('[class*="max-w-[85%]"]').length
  const suggestions = document.querySelectorAll('div[class*="rounded-2xl"][class*="bg-card"]').length
  return { headerTitle, emptyState, userBubbles, suggestions }
})()`)

// T1: fresh load at 1440×900
await navigateAndWait(1440, 900)
let s = await landingState()
check("T1 header title is New chat (1440px)", s.headerTitle === "New chat", JSON.stringify(s.headerTitle))
check("T1 empty state visible (1440px)", s.emptyState, "")
check("T1 zero message bubbles (1440px)", s.userBubbles === 0, `bubbles=${s.userBubbles}`)
check("T1 six feature cards (1440px)", s.suggestions === 6, `cards=${s.suggestions}`)

// T2: fresh load at 390×844 (mobile, drawer closed per spec 019)
await navigateAndWait(390, 844)
s = await landingState()
check("T2 header title is New chat (390px)", s.headerTitle === "New chat", JSON.stringify(s.headerTitle))
check("T2 empty state + zero bubbles (390px)", s.emptyState && s.userBubbles === 0, `empty=${s.emptyState} bubbles=${s.userBubbles}`)
const drawerClosed = await evalJS(`!document.querySelector('aside.w-64') || getComputedStyle(document.querySelector('aside.w-64')).display === 'none'`)
check("T2 drawer closed on mobile (spec 019)", drawerClosed, "")

// T4: first send from the initial draft creates the sidebar row
await navigateAndWait(1440, 900)
await evalJS(`(() => {
  const ta = document.querySelector('textarea')
  const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set
  set.call(ta, '${MARKER} short reply')
  ta.dispatchEvent(new Event('input', { bubbles: true }))
  ta.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
  return true
})()`)
let row = false
for (let i = 0; i < 60; i++) {
  row = await evalJS(`!![...document.querySelectorAll('button[aria-label="Conversation options"]')].find(b => b.closest('div')?.textContent.includes('${MARKER}'))`).catch(() => false)
  if (row) break
  await sleep(1000)
}
check("T4 first send from initial draft creates the sidebar row", row, "")

// cleanup: delete the throwaway
if (row) {
  await evalJS(`(async () => {
    const btn = [...document.querySelectorAll('button[aria-label="Conversation options"]')].find(b => b.closest('div')?.textContent.includes('${MARKER}'))
    btn?.click()
    await new Promise(r => setTimeout(r, 300))
    const item = [...document.querySelectorAll('[role="menuitem"]')].find(el => el.textContent.includes('Delete'))
    item?.click()
    await new Promise(r => setTimeout(r, 300))
    document.querySelector('button[aria-label="Confirm delete"]')?.click()
    return true
  })()`)
  let gone = false
  for (let i = 0; i < 20; i++) {
    gone = await evalJS(`!document.querySelector('aside')?.textContent.includes('${MARKER}')`)
    if (gone) break
    await sleep(500)
  }
  check("T4 cleanup: throwaway deleted", gone, "")
}

ws.close()
if (fails.length) die(`${fails.length} FAILED: ${fails.join(", ")}`)
console.log("\nAll landing checks passed (T1, T2, T4).")
