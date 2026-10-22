"use client"

import { Download, Loader2 } from "lucide-react"
import { useCallback, useState } from "react"

import { Button } from "@/components/ui/button"
import { createExportState } from "@/lib/pdf-export/state"
import { createExportDeps } from "@/lib/pdf-export/render"
import type { ExportMessage } from "@/lib/pdf-export/types"

const EMPTY_MESSAGE = "Nothing to export yet"
const ERROR_MESSAGES: Record<string, string> = {
  render_failed: "Could not generate the PDF — please try again",
  download_blocked: "The download was blocked by the browser",
  empty_conversation: EMPTY_MESSAGE,
}

export function PdfExportButton({ messages }: { messages: ExportMessage[] }) {
  const exportState = useState(createExportState)[0]
  const [view, setView] = useState<"idle" | "busy" | "error">("idle")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const sync = useCallback(() => {
    setView(exportState.get())
    setErrorMessage(
      exportState.get() === "error" ? ERROR_MESSAGES[exportState.error?.code ?? "render_failed"] ?? ERROR_MESSAGES.render_failed : null
    )
  }, [exportState])

  const hasContent = messages.some((m) => m.text.trim().length > 0)

  const onExport = useCallback(() => {
    exportState.run(async () => {
      const { exportConversation } = await import("@/lib/pdf-export/export")
      await exportConversation(messages, createExportDeps())
    }).then(sync)
  }, [exportState, messages, sync])

  return (
    <div className="flex items-center gap-1.5">
      {view === "error" && (
        <span className="flex items-center gap-1 text-xs text-destructive">
          {errorMessage}
          <button
            className="underline underline-offset-2"
            onClick={() => {
              exportState.dismiss()
              sync()
            }}
          >
            dismiss
          </button>
        </span>
      )}
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Download conversation as PDF"
        title={hasContent ? "Download conversation as PDF" : EMPTY_MESSAGE}
        disabled={!hasContent || view === "busy"}
        onClick={onExport}
      >
        {view === "busy" ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Download className="size-4" />
        )}
      </Button>
    </div>
  )
}
