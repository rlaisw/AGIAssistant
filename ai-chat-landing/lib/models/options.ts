export type ModelId =
  | "local"
  | "deepseek/deepseek-v4.1-flash"
  | "moonshotai/kimi-k3"
  | "z-ai/glm-5.3-flash"
  | "qwen/qwen3.8-flash"

export type ModelOption = {
  id: ModelId
  origin: "cloud" | "local"
  displayName: string
  isDefault: boolean
  hint?: string
}

/** FR-001: single-select catalog — one local model plus selectable cloud models. */
export const MODEL_OPTIONS: readonly ModelOption[] = [
  {
    id: "local",
    origin: "local",
    displayName: "Qwen3 8B Q4_K_M",
    isDefault: false,
    hint: "Runs on this host's CPU — slower responses",
  },
  {
    id: "deepseek/deepseek-v4.1-flash",
    origin: "cloud",
    displayName: "Deepseek-v4.1-flash",
    isDefault: true,
  },
  {
    id: "moonshotai/kimi-k3",
    origin: "cloud",
    displayName: "Kimi-k3",
    isDefault: false,
  },
  {
    id: "z-ai/glm-5.3-flash",
    origin: "cloud",
    displayName: "GLM-5.3-flash",
    isDefault: false,
  },
  {
    id: "qwen/qwen3.8-flash",
    origin: "cloud",
    displayName: "Qwen3.8-flash",
    isDefault: false,
  },
]

export const DEFAULT_MODEL_ID: ModelId = "deepseek/deepseek-v4.1-flash"

const VALID_IDS = new Set<string>(MODEL_OPTIONS.map((o) => o.id))

export function isModelId(value: unknown): value is ModelId {
  return typeof value === "string" && VALID_IDS.has(value)
}

/** Unknown, missing, or legacy `"cloud"` values resolve to the cloud default. */
export function normalizeSelection(value: unknown): ModelId {
  if (value === "cloud") return DEFAULT_MODEL_ID
  return isModelId(value) ? value : DEFAULT_MODEL_ID
}

export function optionById(id: ModelId): ModelOption {
  return MODEL_OPTIONS.find((o) => o.id === id) ?? MODEL_OPTIONS[1]
}
