export const runtime = "nodejs"

import { readFileSync } from "node:fs"
import path from "node:path"

const ARTIFACT = path.join(
  process.cwd(),
  "..",
  "dify",
  "AGIAssistant",
  "AGI_Assistant.yml"
)
const DEFAULT_MODEL = "deepseek/deepseek-v4.1-flash"

/**
 * The globally configured cloud model, resolved from the cycle-maintained
 * artifact (spec 026, research D4 / contracts §2): locate the intent_router
 * node id and take its model value. Unreadable artifact → the Deepseek
 * default, never a guess at another model.
 */
export async function GET() {
  let model = DEFAULT_MODEL
  try {
    const text = readFileSync(ARTIFACT, "utf8")
    const idx = text.indexOf("id: intent_router")
    if (idx >= 0) {
      // yaml keys are alphabetical: the node's model: line precedes its id: line
      const before = text.slice(Math.max(0, idx - 8000), idx)
      const matches = [...before.matchAll(/^\s*model:\s*(\S+)\s*$/gm)]
      if (matches.length) model = matches[matches.length - 1][1]
    }
  } catch {
    model = DEFAULT_MODEL
  }
  return Response.json({ model }, { headers: { "Cache-Control": "no-store" } })
}
