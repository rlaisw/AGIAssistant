"use client"

import * as React from "react"
import { useTheme } from "next-themes"
import {
  ArrowUp,
  Bot,
  BrainCircuit,
  Check,
  ChevronDown,
  Code,
  Copy,
  FileText,
  Lightbulb,
  Link2,
  LogOut,
  MessageSquareText,
  Mic,
  Monitor,
  Moon,
  MoreHorizontal,
  Paperclip,
  PanelLeft,
  Pin,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Share2,
  SquarePen,
  Sun,
  ThumbsDown,
  ThumbsUp,
  User,
} from "lucide-react"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Markdown } from "@/components/markdown"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

type Message = {
  id: number
  role: "user" | "assistant"
  text: string
  reasoning?: string
  code?: string
  codeName?: string
  sources?: string[]
  streaming?: boolean
}

type Conversation = {
  id: string
  title: string
  group: string
  messages: Message[]
  difyId?: string
}

const sidebarGroups = ["Pinned", "Today", "Yesterday", "Previous 7 days"]

const initialConversations: Conversation[] = [
  {
    id: "q3",
    title: "Q3 roadmap draft",
    group: "Pinned",
    messages: [
      {
        id: 1,
        role: "user",
        text: "Summarize the Q3 roadmap and turn it into a table I can share with stakeholders.",
      },
      {
        id: 2,
        role: "assistant",
        reasoning:
          "Group the roadmap items by theme, then render them as a markdown table with owners and status so it can be pasted straight into a doc.",
        text: "Here's the Q3 roadmap, grouped by theme and ready to share:",
        code: `| Theme       | Owner | Status   |
|-------------|-------|----------|
| Agents      | Alex  | On track |
| Performance | Mia   | At risk  |
| Onboarding  | Sam   | Shipped  |`,
        codeName: "roadmap.md",
        sources: ["q3-planning.md", "roadmap.yaml"],
      },
    ],
  },
  {
    id: "auth",
    title: "Refactor auth flow",
    group: "Today",
    messages: [
      {
        id: 1,
        role: "user",
        text: "What's the safest order of steps to migrate from session cookies to JWTs without logging everyone out?",
      },
      {
        id: 2,
        role: "assistant",
        text: "Migrate in three phases:\n\n1. Issue JWTs alongside existing sessions and verify both.\n2. Move reads to JWTs, keeping sessions as a fallback.\n3. Remove session issuance once error rates settle.\n\nThat way a bad token can always fall back to a valid session.",
      },
    ],
  },
  {
    id: "copy",
    title: "Landing page copy",
    group: "Today",
    messages: [
      {
        id: 1,
        role: "user",
        text: "Write three hero headline options for a developer tool that previews API responses.",
      },
      {
        id: 2,
        role: "assistant",
        text: '1. "See your API respond before you ship."\n2. "Mock it, test it, ship it."\n3. "Your endpoints, rendered."',
      },
    ],
  },
  {
    id: "sql",
    title: "SQL query optimization",
    group: "Yesterday",
    messages: [
      {
        id: 1,
        role: "user",
        text: "Why is SELECT * FROM orders WHERE email LIKE '%gmail%' so slow on 40M rows?",
      },
      {
        id: 2,
        role: "assistant",
        text: "The leading wildcard forces a full scan of all 40M rows. Options:\n\n1. Drop the leading % if a prefix search is acceptable — then a plain index on email works.\n2. Use a trigram index (pg_trgm) for true substring search.\n3. Push the search to a dedicated search index.",
      },
    ],
  },
  {
    id: "email",
    title: "Onboarding email sequence",
    group: "Previous 7 days",
    messages: [
      {
        id: 1,
        role: "user",
        text: "Draft a three-email onboarding sequence for a note-taking app.",
      },
      {
        id: 2,
        role: "assistant",
        text: "Email 1 (day 0): welcome plus one quick win — create your first note.\nEmail 2 (day 2): the aha moment — backlinks and instant search.\nEmail 3 (day 5): habits — templates, mobile capture, and a gentle upgrade nudge.",
      },
    ],
  },
]

const cannedReplies = [
  {
    text: "Here's how I'd approach it:\n\n1. Start with the smallest working version and ship it behind a flag.\n2. Measure the real bottleneck before optimizing anything.\n3. Roll out gradually, watching error rates at each step.",
    sources: ["engineering-handbook.md"],
  },
  {
    text: "Good question. The short version: it depends on your constraints, but for most teams the pragmatic order is data model first, then API surface, then UI. Each layer should be usable before the next one exists.",
  },
  {
    text: "Here's a compact implementation:",
    code: `export function debounce<T extends (...args: never[]) => void>(
  fn: T,
  wait = 200
) {
  let timer: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), wait)
  }
}`,
    codeName: "debounce.ts",
  },
]

const suggestions = [
  {
    icon: SquarePen,
    title: "Summarize a document",
    subtitle: "Paste text or attach a file",
    prompt: "Summarize this document into five bullet points.",
  },
  {
    icon: Code,
    title: "Write code",
    subtitle: "Generate a function with tests",
    prompt: "Write a TypeScript function that debounces an async call, with tests.",
  },
  {
    icon: Lightbulb,
    title: "Brainstorm ideas",
    subtitle: "Features, names, or plans",
    prompt: "Brainstorm five feature ideas for a note-taking app for students.",
  },
  {
    icon: FileText,
    title: "Explain a concept",
    subtitle: "Simple, with an analogy",
    prompt: "Explain how vector databases work, with an analogy.",
  },
]

const FLUSH_MS = 100
const WATCHDOG_MS = 120000

function parseAnswer(raw: string): { text: string; reasoning?: string } {
  let reasoning = ""
  const text = raw
    .replace(/<think>([\s\S]*?)(?:<\/think>|$)/g, (_, inner: string) => {
      reasoning += inner
      return ""
    })
    .replace(/<\/?think>$/, "")
    .trim()
  return { text, reasoning: reasoning.trim() || undefined }
}

export default function Page() {
  const [conversations, setConversations] =
    React.useState<Conversation[]>(initialConversations)
  const [activeId, setActiveId] = React.useState("q3")
  const [input, setInput] = React.useState("")
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const [busy, setBusy] = React.useState(false)
  const [copiedId, setCopiedId] = React.useState<number | null>(null)
  const { theme, setTheme } = useTheme()
  const streamRef = React.useRef<ReturnType<typeof setInterval> | null>(null)
  const abortRef = React.useRef<AbortController | null>(null)
  const replyRef = React.useRef(0)
  const idRef = React.useRef(3)
  const scrollRef = React.useRef<HTMLDivElement>(null)

  const active =
    conversations.find((c) => c.id === activeId) ?? conversations[0]

  React.useEffect(() => {
    return () => {
      if (streamRef.current) clearInterval(streamRef.current)
      abortRef.current?.abort()
    }
  }, [])

  React.useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [active?.messages])

  function updateConversation(
    id: string,
    updater: (c: Conversation) => Conversation
  ) {
    setConversations((prev) => prev.map((c) => (c.id === id ? updater(c) : c)))
  }

  function updateMessage(id: number, patch: Partial<Message>) {
    updateConversation(activeId, (c) => ({
      ...c,
      messages: c.messages.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    }))
  }

  function demoStream(assistantId: number) {
    const reply = cannedReplies[replyRef.current % cannedReplies.length]
    replyRef.current += 1
    const words = reply.text.split(" ")
    let i = 0
    streamRef.current = setInterval(() => {
      i += 3
      const done = i >= words.length
      updateMessage(assistantId, {
        text: words.slice(0, Math.min(i, words.length)).join(" "),
        streaming: !done,
        sources: done ? reply.sources : undefined,
        code: done ? reply.code : undefined,
        codeName: done ? reply.codeName : undefined,
      })
      if (done && streamRef.current) {
        clearInterval(streamRef.current)
        streamRef.current = null
        setBusy(false)
      }
    }, 60)
  }

  async function send(text = input) {
    const value = text.trim()
    if (!value || busy) return
    setInput("")
    setBusy(true)
    const userMessage: Message = {
      id: (idRef.current += 1),
      role: "user",
      text: value,
    }
    const assistantId = (idRef.current += 1)
    const difyId = active?.difyId

    updateConversation(activeId, (c) => ({
      ...c,
      title: c.title === "New chat" ? value.slice(0, 42) : c.title,
      messages: [
        ...c.messages,
        userMessage,
        { id: assistantId, role: "assistant", text: "", streaming: true },
      ],
    }))

    const controller = new AbortController()
    abortRef.current = controller
    let answer = ""
    let reasoning = ""
    let flushTimer: ReturnType<typeof setTimeout> | null = null
    let timedOut = false
    let watchdog: ReturnType<typeof setTimeout> | null = null

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: value, conversationId: difyId ?? null }),
        signal: controller.signal,
      })
      if (!res.ok || !res.body) {
        const detail = (await res.json().catch(() => null)) as
          | { error?: string }
          | null
        throw new Error(detail?.error ?? `Request failed (${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      const armWatchdog = () => {
        if (watchdog) clearTimeout(watchdog)
        watchdog = setTimeout(() => {
          timedOut = true
          controller.abort()
        }, WATCHDOG_MS)
      }
      armWatchdog()

      const flush = () => {
        flushTimer = null
        const parsed = parseAnswer(answer)
        updateMessage(assistantId, {
          text: parsed.text,
          reasoning: reasoning || parsed.reasoning,
        })
      }
      const scheduleFlush = () => {
        if (flushTimer) return
        flushTimer = setTimeout(flush, FLUSH_MS)
      }

      for (;;) {
        const { done, value: chunk } = await reader.read()
        if (done) break
        buffer += decoder.decode(chunk, { stream: true })
        let idx = buffer.indexOf("\n")
        while (idx >= 0) {
          const line = buffer.slice(0, idx).trim()
          buffer = buffer.slice(idx + 1)
          idx = buffer.indexOf("\n")
          if (!line) continue
          let msg: {
            type: string
            text?: string
            sources?: string[]
            message?: string
            conversationId?: string
          }
          try {
            msg = JSON.parse(line)
          } catch {
            continue
          }
          armWatchdog()
          switch (msg.type) {
            case "chunk":
              answer += msg.text ?? ""
              scheduleFlush()
              break
            case "reasoning":
              reasoning += msg.text ?? ""
              scheduleFlush()
              break
            case "replace":
              answer = msg.text ?? ""
              scheduleFlush()
              break
            case "sources":
              updateMessage(assistantId, { sources: msg.sources })
              break
            case "error":
              throw new Error(msg.message ?? "Stream error")
            case "done":
              if (msg.conversationId) {
                updateConversation(activeId, (c) => ({
                  ...c,
                  difyId: msg.conversationId,
                }))
              }
              break
          }
        }
      }
      if (flushTimer) clearTimeout(flushTimer)
      if (watchdog) clearTimeout(watchdog)
      flush()
      updateMessage(assistantId, { streaming: false })
      setBusy(false)
    } catch (error) {
      if (flushTimer) clearTimeout(flushTimer)
      if (watchdog) clearTimeout(watchdog)
      if (
        error instanceof DOMException &&
        error.name === "AbortError" &&
        !timedOut
      )
        return
      if (!answer) {
        if (timedOut) {
          updateMessage(assistantId, {
            text: "Connection lost — the assistant may still be working on it. Please send your question again.",
            streaming: false,
          })
          setBusy(false)
        } else {
          demoStream(assistantId)
        }
      } else {
        const parsed = parseAnswer(answer)
        updateMessage(assistantId, {
          text: `${parsed.text}\n\nSomething went wrong while streaming the response.`,
          reasoning: reasoning || parsed.reasoning,
          streaming: false,
        })
        setBusy(false)
      }
    }
  }

  function newChat() {
    const id = `c-${(idRef.current += 1)}`
    setConversations((prev) => [
      { id, title: "New chat", group: "Today", messages: [] },
      ...prev,
    ])
    setActiveId(id)
  }

  function copyMessage(message: Message) {
    navigator.clipboard?.writeText(message.text)
    setCopiedId(message.id)
    setTimeout(() => setCopiedId(null), 1500)
  }

  return (
    <div className="flex h-svh overflow-hidden">
      {sidebarOpen && (
        <aside className="hidden w-64 shrink-0 flex-col border-r bg-muted/30 md:flex">
          <div className="flex h-13 shrink-0 items-center gap-2 border-b px-3">
            <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Bot className="size-4" />
            </span>
            <span className="font-heading text-sm font-semibold">AI Chat</span>
          </div>
          <div className="space-y-3 p-3">
            <Button className="w-full" onClick={newChat}>
              <Plus />
              New chat
            </Button>
            <div className="relative">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search chats"
                className="h-8 rounded-lg pr-3 pl-9"
              />
            </div>
          </div>
          <nav className="flex-1 space-y-4 overflow-y-auto px-3 pb-4">
            {sidebarGroups.map((group) => {
              const items = conversations.filter((c) => c.group === group)
              if (items.length === 0) return null
              return (
                <div key={group}>
                  <div className="px-2 pt-2 pb-1.5 text-xs font-medium text-muted-foreground">
                    {group}
                  </div>
                  {items.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => setActiveId(c.id)}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm",
                        c.id === activeId
                          ? "bg-background font-medium shadow-sm"
                          : "text-muted-foreground hover:bg-muted"
                      )}
                    >
                      <MessageSquareText className="size-3.5 shrink-0" />
                      <span className="flex-1 truncate">{c.title}</span>
                      {group === "Pinned" && (
                        <Pin className="size-3 shrink-0 text-muted-foreground" />
                      )}
                    </button>
                  ))}
                </div>
              )
            })}
          </nav>
          <div className="flex items-center gap-2 border-t p-3">
            <Avatar size="sm">
              <AvatarFallback>AD</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm">Alex Doe</div>
              <div className="truncate text-xs text-muted-foreground">
                alex@acme.com
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label="Account options"
                  />
                }
              >
                <MoreHorizontal />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" side="top" className="w-44">
                <DropdownMenuItem>
                  <User />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive">
                  <LogOut />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </aside>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-13 shrink-0 items-center gap-2 border-b px-3">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Toggle sidebar"
            onClick={() => setSidebarOpen((o) => !o)}
          >
            <PanelLeft />
          </Button>
          <span className="truncate text-sm font-medium">{active.title}</span>
          <div className="ml-auto flex items-center gap-1.5">
            <Badge variant="secondary" className="gap-1.5 font-medium">
              <Bot className="size-3.5" />
              AgenticRAG
            </Badge>
            <Button variant="outline" size="sm">
              <Share2 />
              Share
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label="Conversation options"
            >
              <MoreHorizontal />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label="Toggle theme"
                  />
                }
              >
                <Sun className="dark:hidden" />
                <Moon className="hidden dark:block" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-36">
                <DropdownMenuItem onClick={() => setTheme("light")}>
                  <Sun />
                  Light
                  {theme === "light" && <Check className="ml-auto" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")}>
                  <Moon />
                  Dark
                  {theme === "dark" && <Check className="ml-auto" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("system")}>
                  <Monitor />
                  System
                  {theme === "system" && <Check className="ml-auto" />}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {active.messages.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-10">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
              <Bot className="size-6" />
            </div>
            <h1 className="font-heading mt-6 text-2xl font-semibold">
              How can I help you today?
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Ask anything, or start from a suggestion.
            </p>
            <div className="mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-2">
              {suggestions.map((s) => (
                <button
                  key={s.title}
                  onClick={() => send(s.prompt)}
                  className="rounded-2xl border bg-card p-4 text-left transition-colors hover:bg-muted"
                >
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <s.icon className="size-4" />
                    {s.title}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {s.subtitle}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div ref={scrollRef} className="flex-1 overflow-y-auto">
            <div className="mx-auto w-full max-w-3xl space-y-6 p-4 py-6 sm:p-6">
              {active.messages.map((m) =>
                m.role === "user" ? (
                  <div key={m.id} className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                      {m.text}
                    </div>
                  </div>
                ) : (
                  <div key={m.id} className="flex gap-3">
                    <Avatar size="sm" className="mt-0.5">
                      <AvatarFallback>
                        <Bot className="size-4 text-muted-foreground" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1 space-y-3">
                      {m.reasoning && (
                        <div className="rounded-lg border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1.5 font-medium text-foreground">
                            <BrainCircuit className="size-3.5" />
                            Reasoning
                            <ChevronDown className="size-3" />
                          </span>
                          <p className="mt-1.5 leading-relaxed">{m.reasoning}</p>
                        </div>
                      )}
                      {m.text ? (
                        <>
                          <Markdown>{m.text}</Markdown>
                          {m.streaming && (
                            <span className="ml-1 inline-block h-4 w-2 animate-pulse rounded-sm bg-foreground/50 align-middle" />
                          )}
                        </>
                      ) : (
                        <div className="flex items-center gap-1.5 pt-2.5 text-muted-foreground">
                          <span className="size-1.5 animate-pulse rounded-full bg-current" />
                          <span className="size-1.5 animate-pulse rounded-full bg-current [animation-delay:150ms]" />
                          <span className="size-1.5 animate-pulse rounded-full bg-current [animation-delay:300ms]" />
                        </div>
                      )}
                      {m.code && (
                        <div className="overflow-hidden rounded-lg border">
                          <div className="flex items-center justify-between border-b bg-muted/50 px-3 py-1.5 text-xs text-muted-foreground">
                            <span className="font-mono">{m.codeName}</span>
                            <span className="flex items-center gap-1">
                              <Copy className="size-3" />
                              Copy
                            </span>
                          </div>
                          <pre className="overflow-x-auto bg-muted/20 p-3 font-mono text-xs leading-relaxed">
                            <code>{m.code}</code>
                          </pre>
                        </div>
                      )}
                      {m.sources && (
                        <div className="flex flex-wrap gap-1.5">
                          {m.sources.map((source) => (
                            <Badge
                              key={source}
                              variant="outline"
                              className="gap-1 text-xs font-normal"
                            >
                              <Link2 className="size-3" />
                              {source}
                            </Badge>
                          ))}
                        </div>
                      )}
                      {!m.streaming && (
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <span className="text-xs">AgenticRAG</span>
                          <Button
                            variant="ghost"
                            size="icon-xs"
                            aria-label="Copy response"
                            onClick={() => copyMessage(m)}
                          >
                            {copiedId === m.id ? <Check /> : <Copy />}
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-xs"
                            aria-label="Good response"
                          >
                            <ThumbsUp />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-xs"
                            aria-label="Bad response"
                          >
                            <ThumbsDown />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-xs"
                            aria-label="Regenerate response"
                          >
                            <RefreshCw />
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        )}

        <div className="shrink-0 border-t">
          <div className="mx-auto w-full max-w-3xl p-3 sm:p-4">
            <div className="rounded-3xl border bg-muted/30 p-2 shadow-sm">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    send()
                  }
                }}
                placeholder="Message AI Chat…"
                rows={1}
                className="min-h-8 border-transparent bg-transparent px-3 py-2 focus-visible:border-transparent focus-visible:ring-0"
              />
              <div className="flex items-center gap-1 px-1 pt-1">
                <Button variant="ghost" size="icon-sm" aria-label="Attach files">
                  <Paperclip />
                </Button>
                <Button variant="ghost" size="icon-sm" aria-label="Voice input">
                  <Mic />
                </Button>
                <div className="ml-auto flex items-center gap-2">
                  <span className="hidden text-xs text-muted-foreground sm:inline">
                    AgenticRAG
                  </span>
                  <Button
                    size="icon-sm"
                    className="rounded-full"
                    aria-label="Send message"
                    disabled={!input.trim() || busy}
                    onClick={() => send()}
                  >
                    <ArrowUp />
                  </Button>
                </div>
              </div>
            </div>
            <p className="pt-2 text-center text-xs text-muted-foreground">
              AI Chat can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
