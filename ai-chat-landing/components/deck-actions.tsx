"use client"

import { Download, Eye, Presentation } from "lucide-react"

import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function DeckActions({
  downloadUrl,
  pageUrl,
}: {
  downloadUrl: string
  pageUrl: string
}) {
  return (
    <span className="my-3 flex flex-wrap items-center gap-2 rounded-xl border bg-muted/30 p-3">
      <span className="flex items-center gap-2 pr-1 text-sm font-medium">
        <Presentation className="size-4 text-primary" />
        PowerPoint deck
      </span>
      <a
        href={downloadUrl}
        className={cn(buttonVariants({ size: "sm" }))}
        download
      >
        <Download />
        Download
      </a>
      <a
        href={pageUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
      >
        <Eye />
        Preview / Edit
      </a>
    </span>
  )
}
