#!/usr/bin/env node
// Spec 021 welcome feature cards: T1/T2 render+grid, T3 body-send, T4 links, T5 label-no-send.
// Chrome :9240 · pnpm dev :3000.

const CDP = "http://localhost:9240"
const APP = "http://localhost:3000"

const EXPECTED = [
  { title: "Generate PowerPoint", description: "Create professional PowerPoint from text prompts in minutes", label: "How to create PPT", url: "http://localhost/example1.html" },
  { title: "Generate Infographic", description: "Design eye-catching infographics without design skills", label: "How to create Infographic", url: "http://localhost/example2.html" },
  { title: "Draw Chart Diagram", description: "Visualize data with interactive charts and flow diagrams", label: "How to create chart diagram", url: "http://localhost/example3.html" },
  { title: "Talk with CorpIT Helpdesk Chatbot", description: "Get instant IT support and troubleshooting guidance", label: "Chat with CorpIT Support", url: "http://localhost/example4.html" },
  { title: "Ask Any Question with AI Chatbot", description: "Access knowledge across domains with our intelligent assistant", label: "Ask AI Chatbot", url: "http://localhost/example5.html" },
  { title: "Create Personal Agentic RAG Document DB", description: "Build your own searchable knowledge base with AI-powered Agentic RAG", label: "Create Self-Hosted Agentic RAG", url: "http://localhost/example6.html" },
]

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

const CARD_SEL = 'div[class*="rounded-2xl"][class*="bg-card"]'
const gridState = () => evalJS(`(() => {
  const cards = [...document.querySelectorAll('${CARD_SEL}')]
  const grid = document.querySelector('div.mt-8.grid')
  const cols = grid ? getComputedStyle(grid).gridTemplateColumns.split(' ').filter(Boolean).length : 0
  const heading = document.querySelector('h1')?.textContent?.trim() ?? ''
  const subtext = document.body.textContent.includes('Ask anything, or start from a suggestion.')
  return { count: cards.length, cols, heading, subtext, texts: cards.map(c => c.textContent) }
})()`)

// T1: render at 1440×900
await navigateAndWait(1440, 900)
let g = await gridState()
check("T1 six cards render (1440px)", g.count === 6, `count=${g.count}`)
check("T1 grid is 3 columns (1440px)", g.cols === 3, `cols=${g.cols}`)
check("T1 heading unchanged", g.heading === "How can I help you today?", JSON.stringify(g.heading))
check("T1 subtext unchanged", g.subtext, "")
const allText = g.texts.join("\n")
for (const [i, c] of EXPECTED.entries()) {
  check(`T1 card ${i + 1} title+description exact`, allText.includes(c.title) && allText.includes(c.description), c.title)
}

// T2: stacked at 390×844
await navigateAndWait(390, 844)
g = await gridState()
check("T2 six cards render (390px)", g.count === 6, `count=${g.count}`)
check("T2 grid is 1 column (390px)", g.cols === 1, `cols=${g.cols}`)

// T4: links correct (before any sends)
await navigateAndWait(1440, 900)
const links = await evalJS(`[...document.querySelectorAll('${CARD_SEL} a')].map(a => ({ href: a.getAttribute('href'), target: a.getAttribute('target'), rel: a.getAttribute('rel') }))`)
check("T4 six label links present", links.length === 6, `count=${links.length}`)
for (const [i, c] of EXPECTED.entries()) {
  const l = links[i] ?? {}
  check(`T4 link ${i + 1} href+target`, l.href === c.url && l.target === "_blank", `${l.href ?? "missing"}`)
}

// T3: body click sends the label prompt
await evalJS(`document.querySelectorAll('${CARD_SEL} button')[0]?.click(); true`)
await sleep(800)
const bubbleText = await evalJS(`[...document.querySelectorAll('[class*="max-w-[85%]"]')].map(b => b.textContent).join(' | ')`)
check("T3 body click sends label prompt", bubbleText.includes("How to create PPT"), JSON.stringify(bubbleText.slice(0, 60)))

// T3b: body click on a second card also sends its label (SC-002: at least two cards)
await navigateAndWait(1440, 900)
await evalJS(`document.querySelectorAll('${CARD_SEL} button')[5]?.click(); true`)
await sleep(800)
const bubbleText2 = await evalJS(`[...document.querySelectorAll('[class*="max-w-[85%]"]')].map(b => b.textContent).join(' | ')`)
check("T3b body click on card 6 sends its label", bubbleText2.includes("Create Self-Hosted Agentic RAG"), JSON.stringify(bubbleText2.slice(0, 60)))

// T5: label click sends nothing (fresh page)
await navigateAndWait(1440, 900)
await evalJS(`document.querySelectorAll('${CARD_SEL} a')[1]?.click(); true`)
await sleep(800)
const bubblesAfterLink = await evalJS(`document.querySelectorAll('[class*="max-w-[85%]"]').length`)
check("T5 label click sends nothing", bubblesAfterLink === 0, `bubbles=${bubblesAfterLink}`)

ws.close()
if (fails.length) die(`${fails.length} FAILED: ${fails.join(", ")}`)
console.log("\nAll welcome-cards checks passed (T1–T5).")
