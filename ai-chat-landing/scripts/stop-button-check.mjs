#!/usr/bin/env node
// Spec 027 stop-generation-button acceptance script (tasks T005/T011/T015).
// Live CDP checks against pnpm dev on :3000 (Chrome --remote-debugging-port=9240):
//   B1 morph during generation · B2 stop mid-stream (<1s ready, partial kept,
//   no growth = SC-005 UI-side) · B3 follow-up works · B4 thinking-phase stop
//   (no empty bubble) · B5 double-click no-op · B6 conversation-switch
//   visibility (FR-010) · D5 reload: partial kept, session-only caption gone
//   D1/D3 stop-route failure → client still stops cleanly · D2 no-task race.
// NOT covered here: B7 demo mode (needs a key-less dev server — manual).
// Every throwaway conversation is deleted at the end (spec-015 flow).

import { argv } from "node:process"

const CDP = "http://localhost:9240"
const APP = "http://localhost:3000"
const ONLY = argv.find((a) => a.startsWith("--only="))?.slice(7) ?? null
const STAMP = Date.now()
const MARKERS = [1, 2, 3, 4, 5].map((n) => `027-stop-${n}-${STAMP}`)
const LONG_Q = "Write a detailed 300-word story about a lighthouse keeper. Do not use any tools."
const FOLLOW_UP = "In one short sentence, what was the keeper's name?"

function die(msg) { console.error(`✗ ${msg}`); process.exit(1) }
const fails = []
function check(name, ok, detail = "") {
  console.log(`${ok ? "✓" : "✗"} ${name}${detail ? ` — ${detail}` : ""}`)
  if (!ok) fails.push(name)
}

const version = await fetch(`${CDP}/json/version`).then(r => r.json())
  .catch(() => die(`Chrome CDP ${CDP} unreachable — start Chrome with --remote-debugging-port=9240`))
const home = await fetch(APP).then(r => r.status).catch(() => die(`${APP} not serving — start pnpm dev in ai-chat-landing/`))
if (home !== 200) die(`${APP} returned HTTP ${home}`)
console.log(`CDP ok (${version.Browser}) · app ok`)

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
    setTimeout(() => rej(new Error(`CDP timeout: ${method}`)), 20000)
  })
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms))
async function evalJS(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })
  if (r.error) throw new Error(`Runtime.evaluate: ${JSON.stringify(r.error)}`)
  if (r.exceptionDetails) throw new Error(`page exception: ${JSON.stringify(r.exceptionDetails.exception?.description ?? r.exceptionDetails)}`)
  return r.result.result.value
}

const SEL_COLUMN = `[class*="space-y-6"][class*="p-4"]`
async function navigate() {
  await send("Page.navigate", { url: APP })
  for (let i = 0; i < 40; i++) {
    try { if (await evalJS("document.readyState") === "complete") break } catch {}
    await sleep(500)
  }
  await sleep(800)
}
async function newChat() {
  await evalJS(`document.querySelector('aside button.w-full')?.click(); true`)
  await sleep(600)
}
async function typeAndSend(text) {
  const ok = await evalJS(`(() => {
    const ta = document.querySelector('textarea')
    if (!ta) return false
    const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set
    set.call(ta, ${JSON.stringify(text)})
    ta.dispatchEvent(new Event('input', { bubbles: true }))
    ta.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
    return true
  })()`)
  if (!ok) die("composer textarea not found")
}
async function composerMode() {
  return await evalJS(`document.querySelector('button[data-composer-mode]')?.getAttribute('data-composer-mode') ?? null`)
}
async function lastAssistant() {
  return await evalJS(`(() => {
    const col = document.querySelector('${SEL_COLUMN}')
    if (!col) return { missing: true }
    const blocks = [...col.children].filter(el => el.classList.contains('gap-3'))
    if (!blocks.length) return { count: 0 }
    const last = blocks[blocks.length - 1]
    const answer = last.querySelector('[data-answer-text]')
    return {
      count: blocks.length,
      len: answer ? answer.innerText.length : 0,
      reasoning: last.innerText.length - (answer ? answer.innerText.length : 0),
      caption: !!last.querySelector('[data-stopped-caption]'),
      streaming: !!last.querySelector('[role="status"]'),
      text: answer ? answer.innerText : '',
    }
  })()`)
}
async function waitComposerMode(mode, timeoutMs) {
  const t0 = Date.now()
  for (;;) {
    if ((await composerMode()) === mode) return Date.now() - t0
    if (Date.now() - t0 > timeoutMs) return -1
    await sleep(50)
  }
}
async function waitText(minLen, timeoutMs) {
  const t0 = Date.now()
  for (;;) {
    const m = await lastAssistant()
    if (!m.missing && m.count > 0 && m.len >= minLen && !m.caption) return m
    if (Date.now() - t0 > timeoutMs) return null
    await sleep(400)
  }
}
async function clickStop() {
  await evalJS(`document.querySelector('button[aria-label="Stop generation"]')?.click(); true`)
}
async function rowCount() {
  return await evalJS(`document.querySelectorAll('button[aria-label="Conversation options"]').length`)
}
async function openConversationByMarker(marker) {
  await evalJS(`(() => {
    const rows = [...document.querySelectorAll('aside button[aria-label="Conversation options"]')]
    const row = rows.map(b => b.closest('div')).find(d => d?.textContent.includes('${marker}'))
    const openBtn = row ? [...row.querySelectorAll('button')].find(b => b.getAttribute('aria-label') !== 'Conversation options') : null
    openBtn?.click()
    return !!openBtn
  })()`)
  for (let i = 0; i < 40; i++) {
    const col = await evalJS(`!!document.querySelector('${SEL_COLUMN}')`).catch(() => false)
    if (col) return true
    await sleep(500)
  }
  return false
}

// D2 (route-level, no browser needed): a stop for an unknown task must be
// `no-task` 200, not an error — the completion race is never a failure.
// Uses a valid (but nonexistent) UUID so the backend lookup 404s.
const d2 = await fetch(`${APP}/api/chat/stop`, {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ taskId: crypto.randomUUID() }),
}).then(async r => ({ status: r.status, body: await r.json() })).catch(e => ({ error: String(e) }))
check("D2 unknown task → 200 ok/no-task (race = success)", d2.status === 200 && ["ok", "no-task"].includes(d2.body?.result), JSON.stringify(d2))

await navigate()

// ---- B1 + B2: morph, stop mid-stream, <1s ready, partial kept, no growth ----
await newChat()
await typeAndSend(`${MARKERS[0]} ${LONG_Q}`)
const morphMs = await waitComposerMode("stop", 20000)
check("B1 composer morphs to Stop during generation", morphMs >= 0, morphMs >= 0 ? `visible after ${morphMs}ms` : "never appeared")
const typingEnabled = await evalJS(`!document.querySelector('textarea')?.disabled`)
check("B1 typing stays enabled while generating (FR-001)", typingEnabled)
let partial = await waitText(40, 120000)
check("B2 answer text streamed before stop", !!partial, partial ? `len=${partial.len}` : "no text in 120s")
const beforeLen = partial?.len ?? 0
const beforeText = partial?.text ?? ""
const stopT0 = Date.now()
await clickStop()
const readyMs = await waitComposerMode("send", 2000)
const elapsed = Date.now() - stopT0
check("B2 composer ready < 1s after Stop (SC-001)", readyMs >= 0 && elapsed < 1000, `ready in ${elapsed}ms`)
const stopped = await lastAssistant()
check("B2 partial text kept (FR-004)", stopped.len >= beforeLen && stopped.text === beforeText, `len ${beforeLen} → ${stopped.len}`)
check("B2 'Stopped' caption shown (FR-007)", stopped.caption)
check("B2 no streaming indicator after stop (FR-005)", !stopped.streaming)
await sleep(5000)
const after5s = await lastAssistant()
check("B2 no further content after stop (SC-005 UI-side)", after5s.len === stopped.len, `len ${stopped.len} → ${after5s.len} after 5s`)

// ---- B3: follow-up in the same conversation answers normally ----
await typeAndSend(FOLLOW_UP)
const followDone = await (async () => {
  const t0 = Date.now()
  for (;;) {
    const m = await lastAssistant()
    if (m.count >= 2 && m.len > 0 && !m.streaming && !m.caption) return true
    if (Date.now() - t0 > 120000) return false
    await sleep(500)
  }
})()
check("B3 follow-up answers after a stop (SC-002)", followDone)

// ---- B4: thinking-phase stop leaves no empty bubble ----
await newChat()
await typeAndSend(`${MARKERS[1]} ${LONG_Q}`)
await waitComposerMode("stop", 20000)
await clickStop()
const b4ready = await waitComposerMode("send", 2000)
const b4 = await lastAssistant()
check("B4 thinking-phase stop: no assistant bubble (empty-turn removal)", b4ready >= 0 && b4.count === 0, `assistant blocks: ${b4.count}`)

// ---- B5: double-click is a single stop ----
await newChat()
await typeAndSend(`${MARKERS[2]} ${LONG_Q}`)
await waitComposerMode("stop", 20000)
await waitText(40, 120000)
await evalJS(`(() => {
  const b = document.querySelector('button[aria-label="Stop generation"]')
  b?.click(); b?.click()
  return true
})()`)
const b5ready = await waitComposerMode("send", 2000)
const b5 = await lastAssistant()
check("B5 double-click: one consistent stop, caption shown (FR-009)", b5ready >= 0 && b5.caption && b5.len > 0)

// ---- D1/D3: stop-route failure → client still stops cleanly ----
await newChat()
await evalJS(`(() => {
  window.__origFetch = window.fetch
  window.fetch = (input, init) => {
    const url = typeof input === 'string' ? input : input.url
    if (url.includes('/api/chat/stop')) {
      return Promise.resolve(new Response(JSON.stringify({ error: 'stop failed: injected D1' }), { status: 502, headers: { 'Content-Type': 'application/json' } }))
    }
    return window.__origFetch(input, init)
  }
  return true
})()`)
await typeAndSend(`${MARKERS[3]} ${LONG_Q}`)
await waitComposerMode("stop", 20000)
await waitText(40, 120000)
const d1t0 = Date.now()
await clickStop()
const d1ready = await waitComposerMode("send", 2000)
const d1 = await lastAssistant()
const d1ms = Date.now() - d1t0
await evalJS(`(() => { window.fetch = window.__origFetch; delete window.__origFetch; return true })()`)
check("D1/D3 stop-route 502 → client still stops < 1s + caption", d1ready >= 0 && d1ms < 1000 && d1.caption, `${d1ms}ms, caption=${d1.caption}`)

// ---- B6: conversation switch mid-generation (FR-010) ----
await newChat()
await typeAndSend(`${MARKERS[4]} ${LONG_Q}`)
await waitComposerMode("stop", 20000)
await waitText(30, 120000)
await newChat() // switch away — generation must not be disturbed
const awayMode = await composerMode()
const awayDisabled = await evalJS(`document.querySelector('button[data-composer-mode="send"]')?.disabled ?? false`)
check("B6 switched view: composer is Send and disabled (FR-010)", awayMode === "send" && awayDisabled)
const reopened = await openConversationByMarker(MARKERS[4])
const backMode = await composerMode()
check("B6 back in generating view: Stop visible again", reopened && backMode === "stop")
const b6partial = await waitText(30, 30000)
check("B6 generation kept updating its own conversation", !!b6partial)
await clickStop()
await waitComposerMode("send", 2000)

// ---- D5: reload — partial transcript is the durable record, caption is session-only ----
await navigate()
const historyWait = await (async () => {
  const t0 = Date.now()
  for (;;) {
    if ((await rowCount()) > 0) return true
    if (Date.now() - t0 > 15000) return false
    await sleep(300)
  }
})()
const opened = historyWait && (await openConversationByMarker(MARKERS[0]))
await sleep(1000)
const d5 = await lastAssistant()
check("D5 reloaded stopped turn keeps partial text", opened && d5.count >= 1 && d5.len > 0,
  JSON.stringify({ opened, count: d5.count, len: d5.len }))
check("D5 no caption after reload (session-only, FR-007)", !d5.caption)

// ---- cleanup: delete every throwaway conversation (spec-015 flow) ----
for (const marker of MARKERS) {
  const step = await evalJS(`(async () => {
    const rows = [...document.querySelectorAll('aside button[aria-label="Conversation options"]')]
    const row = rows.map(btn => btn.closest('div')).find(d => d?.textContent.includes('${marker}'))
    if (!row) return 'row-not-found'
    row.querySelector('button[aria-label="Conversation options"]').click()
    await new Promise(r => setTimeout(r, 300))
    const item = [...document.querySelectorAll('[role="menuitem"]')].find(el => el.textContent.includes('Delete'))
    if (!item) return 'menu-item-not-found'
    item.click()
    await new Promise(r => setTimeout(r, 300))
    const confirmBtn = row.querySelector('button[aria-label="Confirm delete"]')
    if (!confirmBtn) return 'confirm-not-found'
    confirmBtn.click()
    return 'confirmed'
  })()`)
  let gone = false
  for (let i = 0; i < 30; i++) {
    gone = await evalJS(`!document.querySelector('aside')?.textContent.includes('${marker}')`)
    if (gone) break
    await sleep(500)
  }
  if (!gone) fails.push(`cleanup ${marker} (${step})`)
}
console.log("cleanup: throwaway conversations removed")

ws.close()
if (fails.length) die(`${fails.length} FAILED: ${fails.join(", ")}`)
console.log(`\nAll spec 027 acceptance checks passed (B1–B6, D1–D3, D5, SC-001/002/005). B7 (demo mode) requires a key-less dev server — manual.`)
process.exit(0)
