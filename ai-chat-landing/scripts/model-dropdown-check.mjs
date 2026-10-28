#!/usr/bin/env node
// Spec 025 live checks: AI LLM drop-down (SC-001..SC-003, FR-004/007/008/009).
// Chrome :9240 · pnpm dev :3000 · live Dify + Ollama.
// Phases: A = switch+badge+persistence, B = unavailable+fallback (ollama down),
// C1/C2 = mid-stream kill (bash kills ollama between), D = purge + defaults.

const CDP = "http://localhost:9240"
const APP = "http://localhost:3000"
const PHASE = process.argv[2] ?? "A"
const QUERY = "Reply with exactly: PONG"

function die(msg) { console.error(`✗ ${msg}`); process.exit(1) }

await fetch(`${CDP}/json/version`).then(r => r.json())
  .catch(() => die(`Chrome CDP ${CDP} unreachable`))

let ws
if (PHASE === "C2") {
  const tabs = await fetch(`${CDP}/json/list`).then(r => r.json())
  const tab = tabs.find(t => t.url.startsWith(APP) && t.webSocketDebuggerUrl)
  if (!tab) die("no app tab open for C2")
  ws = new WebSocket(tab.webSocketDebuggerUrl)
} else {
  const tab = await fetch(`${CDP}/json/new`, { method: "PUT" }).then(r => r.json())
  ws = new WebSocket(tab.webSocketDebuggerUrl)
}
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
    setTimeout(() => { pending.delete(id); rej(new Error(`CDP timeout: ${method}`)) }, 8000)
  })
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms))
async function evalJS(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 200))
  return r.result.result.value
}

const fails = []
function check(name, ok, detail) {
  console.log(`${ok ? "✓" : "✗"} ${name} — ${detail}`)
  if (!ok) fails.push(name)
}

await send("Page.enable")
await send("Runtime.enable")
await send("Network.enable")
const net = []
ws.addEventListener("message", (ev) => {
  const m = JSON.parse(ev.data)
  if (m.method === "Network.requestWillBeSent" || m.method === "Network.responseReceived" ||
      m.method === "Network.loadingFinished" || m.method === "Network.loadingFailed") {
    const p = m.params || {}
    const url = (p.request && p.request.url) || (p.response && p.response.url) || ""
    if (url.includes("/api/chat")) net.push(`${m.method}:${p.errorText ?? ""}`)
  }
})

async function navigate() {
  await send("Page.navigate", { url: APP })
  for (let i = 0; i < 40; i++) {
    try { if (await evalJS("document.readyState") === "complete") break } catch {}
    await sleep(500)
  }
  await sleep(1500)
}

// minimal, layout-light poll expressions only (heavy body reads made earlier
// runs flaky during streaming re-renders)
const domState = () => evalJS(`(() => ({
  trigger: document.querySelector('button[aria-label="AI LLM model selector"]')?.textContent ?? '',
  badges: [...document.querySelectorAll('[data-model-badge]')].map(e => e.textContent),
  note: document.querySelector('[data-fallback-note]')?.textContent ?? '',
  thinking: !!document.querySelector('[role="status"]'),
  err: !!document.querySelector('p.text-sm, div.text-sm') && false,
}))()`)
const storageState = () => evalJS(`(() => ({
  sel: Object.fromEntries(Object.entries(localStorage).filter(([k]) => k.startsWith('agi-model:selection:'))),
  badge: Object.fromEntries(Object.entries(localStorage).filter(([k]) => k.startsWith('agi-model:badge:'))),
}))()`)

const openDropdown = () => evalJS(`(() => {
  document.querySelector('button[aria-label="AI LLM model selector"]')?.click()
  return true
})()`)
const selectInMenu = (name) => evalJS(`(() => {
  const item = [...document.querySelectorAll('[role="menuitem"]')].find(e => e.textContent.includes('${name}'))
  if (!item) return false
  item.click()
  return true
})()`)
const sendMessage = (text) => evalJS(`(() => {
  const ta = document.querySelector('textarea')
  const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set
  set.call(ta, '${text}')
  ta.dispatchEvent(new Event('input', { bubbles: true }))
  ta.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
  return true
})()`)
// the most-recent sidebar row's open button (rows are recency-sorted; Dify
// renames titles, so target positionally)
const openMostRecentConversation = () => evalJS(`(() => {
  const btn = document.querySelector('nav button[class*="flex-1"]')
  if (!btn) return false
  btn.click()
  return true
})()`)
const newChat = () => evalJS(`(() => {
  const btn = [...document.querySelectorAll('aside button')].find(b => b.textContent.includes('New chat'))
  btn?.click()
  return !!btn
})()`)

async function waitFor(predicate, timeoutMs) {
  for (let i = 0; i < timeoutMs / 1000; i++) {
    if (await predicate().catch(() => false)) return true
    await sleep(1000)
  }
  return false
}

if (PHASE === "M") {
  // spec 025 T032 / quickstart item 7: mobile overlay layout reachability
  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true })
  await navigate()
  await evalJS("localStorage.clear()")
  await navigate()
  let s = await domState()
  check("M1 AI LLM trigger reachable at 390×844 (overlay layout)", s.trigger.includes("Deepseek"), JSON.stringify(s.trigger))
  await openDropdown()
  await sleep(800)
  const menu = await evalJS(`[...document.querySelectorAll('[role="menuitem"]')].map(e => e.textContent)`)
  check("M2 both model entries reachable on mobile",
    menu.join(" | ").includes("Qwen3 8B") && menu.join(" | ").includes("Deepseek"),
    menu.join(" | "))
  check("M3 selecting on mobile works", await selectInMenu("Qwen3 8B"))
  await sleep(400)
  s = await domState()
  check("M4 trigger reflects the selection on mobile", s.trigger.includes("Qwen3 8B"), JSON.stringify(s.trigger))
  await send("Emulation.clearDeviceMetricsOverride")
}

if (PHASE === "A") {
  await navigate()
  await evalJS("localStorage.clear()")
  await navigate()
  let s = await domState()
  check("A1 trigger exists, cloud default", s.trigger.includes("Deepseek"), JSON.stringify(s.trigger))

  await openDropdown()
  await sleep(500)
  s = await domState()
  const menu = await evalJS(`[...document.querySelectorAll('[role="menuitem"]')].map(e => e.textContent)`)
  check("A2 menu lists both models with local hint",
    menu.join(" | ").includes("Qwen3 8B") && menu.join(" | ").includes("CPU"),
    menu.join(" | "))
  check("A2 no unavailable line while up", !(await evalJS(`document.body.textContent.includes('Local model unavailable')`)), "")

  check("A3 select local", await selectInMenu("Qwen3 8B"))
  await sleep(500)
  s = await domState()
  check("A3 trigger switched to Qwen3 8B (≤2 interactions, SC-001)", s.trigger.includes("Qwen3 8B"), JSON.stringify(s.trigger))

  await sendMessage(QUERY)
  let pollCount = 0
  const ok = await waitFor(async () => {
    const s = await domState()
    pollCount += 1
    if (pollCount % 15 === 0) console.log(`  [poll ${pollCount}]`, JSON.stringify(s), "| net:", net.join(","))
    return s.badges.some(b => b.includes("Qwen3 8B"))
  }, 300000)
  console.log("  [net]", net.join(",") || "NONE")
  s = await domState()
  check("A4 local reply completed + badge Qwen3 8B (SC-001, FR-008)", ok, `badges=${JSON.stringify(s.badges)}`)
  check("A4 no reasoning block rendered (FR-009)",
    !(await evalJS(`!!document.querySelector('.rounded-lg.border') && [...document.querySelectorAll('.rounded-lg.border')].some(e => e.textContent.includes('Reasoning'))`)), "")
  const st = await storageState()
  check("A4 selection + badge persisted for the new conversation",
    Object.values(st.sel).includes('"local"') && JSON.stringify(st.badge).includes("local"),
    JSON.stringify(st))

  await navigate()
  check("A5 reopen most recent conversation", await openMostRecentConversation())
  check("A5 resumed messages render",
    await waitFor(async () => (await domState()).badges.length > 0, 30000), "")
  s = await domState()
  check("A5 selection persists across reload (SC-003)", s.trigger.includes("Qwen3 8B"), JSON.stringify(s.trigger))
  check("A5 badge survives reload (FR-008 ordinal)", s.badges.some(b => b.includes("Qwen3 8B")), JSON.stringify(s.badges))
} else if (PHASE === "B") {
  // no storage clear here: B depends on phase A's persisted "local" selection
  await navigate()
  let s = await domState()
  check("B1 fresh chat starts on cloud (FR-003 default)", s.trigger.includes("Deepseek"), JSON.stringify(s.trigger))

  await openDropdown()
  await sleep(1500)
  const menuInfo = await evalJS(`(() => ({
    unavailable: document.body.textContent.includes('Local model unavailable'),
    disabled: [...document.querySelectorAll('[role="menuitem"]')].find(e => e.textContent.includes('Qwen3 8B'))?.getAttribute('aria-disabled'),
  }))()`)
  check("B2 local marked unavailable while down (SC-002 ≤5s)", menuInfo.unavailable, "")
  check("B2 local entry disabled", menuInfo.disabled === "true", `aria-disabled=${menuInfo.disabled}`)
  await evalJS(`document.querySelector('body').click()`)
  await sleep(400)

  check("B3 reopen the local-selected conversation", await openMostRecentConversation())
  await sleep(2000)
  s = await domState()
  check("B3 persisted local selection still shown", s.trigger.includes("Qwen3 8B"), JSON.stringify(s.trigger))

  await sendMessage(QUERY)
  const ok = await waitFor(async () => {
    const st = await domState()
    return st.note.length > 0 && st.badges.some(b => b.includes("Deepseek"))
  }, 120000)
  s = await domState()
  check("B4 FR-004 fallback: cloud answered with persistent note", ok,
    `note=${JSON.stringify(s.note)} badges=${JSON.stringify(s.badges)}`)
  check("B4 trigger reset to DeepSeek (no auto-resume)",
    s.trigger.includes("Deepseek") && !s.trigger.includes("Qwen3 8B"), JSON.stringify(s.trigger))
  const st = await storageState()
  check("B4 stored selection is cloud after reset", Object.values(st.sel).every(v => v === '"cloud"'), JSON.stringify(st.sel))
} else if (PHASE === "C1") {
  await navigate()
  check("C1 reopen conversation", await openMostRecentConversation())
  await sleep(2000)
  await openDropdown()
  await sleep(1500)
  check("C1 local selectable again", await selectInMenu("Qwen3 8B"))
  await sleep(400)
  await sendMessage(QUERY)
  console.log("C1 sent — kill ollama now")
} else if (PHASE === "C2") {
  const ok = await waitFor(async () => {
    const t = await evalJS(`document.body.textContent.includes('could not answer this message')`).catch(() => false)
    return t
  }, 600000)
  check("C2 FR-007 mid-stream failure surfaces honest error", ok, "")
  const s = await domState()
  check("C2 selection reset to cloud", s.trigger.includes("Deepseek") && !s.trigger.includes("Qwen3 8B"), JSON.stringify(s.trigger))
} else if (PHASE === "D") {
  await navigate()
  const before = await storageState()
  check("D0 open most recent conversation", await openMostRecentConversation())
  await sleep(2000)
  await evalJS(`(async () => {
    const btn = document.querySelector('nav button[aria-label="Conversation options"]')
    btn?.click()
    await new Promise(r => setTimeout(r, 400))
    const item = [...document.querySelectorAll('[role="menuitem"]')].find(el => el.textContent.includes('Delete'))
    item?.click()
    await new Promise(r => setTimeout(r, 400))
    document.querySelector('button[aria-label="Confirm delete"]')?.click()
    return true
  })()`)
  check("D1 delete purges both storage keys (T026)",
    await waitFor(async () => {
      const after = await storageState()
      return Object.keys(after.sel).length === Math.max(0, Object.keys(before.sel).length - 1)
        && Object.keys(after.badge).length === Math.max(0, Object.keys(before.badge).length - 1)
    }, 20000),
    "")
  await newChat()
  await sleep(800)
  const s = await domState()
  check("D2 new chat defaults to cloud", s.trigger.includes("Deepseek"), JSON.stringify(s.trigger))
}

console.log(fails.length ? `PHASE ${PHASE}: ${fails.length} FAILED` : `PHASE ${PHASE}: all passed`)
process.exit(fails.length ? 1 : 0)
