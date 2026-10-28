export const runtime = "nodejs"

import { execFile } from "node:child_process"
import path from "node:path"
import { promisify } from "node:util"

import { MODEL_OPTIONS } from "@/lib/models/options"

const run = promisify(execFile)
const CLOUD_IDS = new Set<string>(
  MODEL_OPTIONS.filter((o) => o.origin === "cloud").map((o) => o.id)
)
const REPO_ROOT = path.join(process.cwd(), "..")
const VENV_PYTHON = path.join(REPO_ROOT, ".venv", "bin", "python")
const CYCLE_TIMEOUT_MS = 90_000

let inFlight = false

/**
 * Apply a cloud model to the chatflow (spec 026, contracts §1): spawns the
 * deploy CLI export → patch → overwrite → publish cycle and awaits it.
 * The published app stays untouched until the publish step — a failure here
 * means the previous configuration keeps serving (FR-004).
 */
export async function POST(req: Request) {
  const { model } = (await req.json().catch(() => ({}))) as { model?: unknown }
  if (typeof model !== "string" || !CLOUD_IDS.has(model)) {
    return Response.json({ error: "unknown cloud model id" }, { status: 400 })
  }
  if (inFlight) {
    return Response.json(
      { error: "a reconfiguration is already in flight" },
      { status: 409 }
    )
  }
  inFlight = true
  const started = Date.now()
  try {
    await run(VENV_PYTHON, ["-m", "agentic_rag_mcp.deploy", "apply-model", model], {
      cwd: REPO_ROOT,
      timeout: CYCLE_TIMEOUT_MS,
      maxBuffer: 1024 * 1024,
    })
    return Response.json({ applied: model, durationMs: Date.now() - started })
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error)
    return Response.json(
      { error: `cycle failed: ${detail.slice(0, 300)}` },
      { status: 502 }
    )
  } finally {
    inFlight = false
  }
}
