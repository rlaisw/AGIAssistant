"use client"

import { ChevronDown, Clock, MessageSquareText, MoreHorizontal, RefreshCw, Trash2 } from "lucide-react"
import React from "react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { groupConversations } from "@/lib/history/buckets"
import { createDeleteState } from "@/lib/history/delete"
import type { ConversationRecord } from "@/lib/history/types"

function DeleteRow({
  record,
  onDelete,
  active,
  onOpen,
}: {
  record: ConversationRecord
  onDelete: (record: ConversationRecord) => Promise<void>
  active: boolean
  onOpen: (record: ConversationRecord) => void
}) {
  const del = React.useMemo(() => createDeleteState({ deleteRequest: () => onDelete(record) }), [onDelete, record])
  const [delStatus, setDelStatus] = React.useState(del.status)

  const confirmDelete = async () => {
    await del.confirm(record.difyId)
    setDelStatus(del.status)
  }

  return (
    <div
      key={record.difyId}
      className="group/row relative flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm text-muted-foreground hover:bg-muted data-[active]:bg-background"
      {...(active ? { "data-active": "true" as const } : {})}
    >
      <button className="flex min-w-0 flex-1 items-center gap-2" onClick={() => onOpen(record)} aria-current={active ? "true" : undefined}>
        <MessageSquareText className="size-3.5 shrink-0" />
        <span className="flex-1 truncate">{record.title}</span>
      </button>
      {(delStatus === "idle" || delStatus === "menu") && (
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Conversation options"
                className="size-6 shrink-0 opacity-0 transition-opacity group-hover/row:opacity-100 focus-visible:opacity-100"
              />
            }
          >
            <MoreHorizontal className="size-3.5" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            <DropdownMenuItem variant="destructive" onClick={() => { del.open(); del.chooseDelete(); setDelStatus(del.status) }}>
              <Trash2 />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
      {(delStatus === "confirming" || delStatus === "error") && (
        <div className="flex shrink-0 items-center gap-1 text-xs" role="alert">
          <span className="max-w-36 truncate text-destructive">
            {delStatus === "error" ? "Could not delete — try again" : "Delete?"}
          </span>
          <Button variant="ghost" size="icon-sm" className="size-6" aria-label="Confirm delete" onClick={confirmDelete}>
            <Trash2 className="size-3.5 text-destructive" />
          </Button>
          <Button variant="ghost" size="icon-sm" className="size-6" aria-label="Cancel delete" onClick={() => { del.cancel(); setDelStatus(del.status) }}>
            ×
          </Button>
        </div>
      )}
      {delStatus === "in-flight" && <RefreshCw className="size-3.5 shrink-0 animate-spin" aria-label="Deleting" />}
    </div>
  )
}

export function ChatHistory({
  records,
  status,
  hasMore,
  loadingMore,
  activeDifyId,
  onOpen,
  onRetry,
  onLoadMore,
  onDelete,
}: {
  records: ConversationRecord[]
  status: "idle" | "loading" | "ready" | "error"
  hasMore: boolean
  loadingMore: boolean
  activeDifyId?: string
  onOpen: (record: ConversationRecord) => void
  onRetry: () => void
  onLoadMore: () => void
  onDelete: (record: ConversationRecord) => Promise<void>
}) {
  if (status === "loading") {
    return (
      <div className="space-y-2 px-2 py-3" aria-busy="true" aria-label="Loading chat history">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-7 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    )
  }

  if (status === "error") {
    return (
      <div className="space-y-2 p-3 text-xs text-muted-foreground" role="alert">
        <span className="flex items-center gap-1.5">
          <Clock className="size-3.5 shrink-0" />
          Chat history is unavailable right now. New chats still work.
        </span>
        <Button variant="outline" size="sm" className="h-7 w-full" onClick={onRetry}>
          <RefreshCw className="size-3.5" />
          Retry
        </Button>
      </div>
    )
  }

  const groups = groupConversations(records)

  return (
    <div className="space-y-4">
      {groups.map((group) => (
        <div key={group.id}>
          <div className="px-2 pt-2 pb-1.5 text-xs font-medium text-muted-foreground">
            {group.label}
          </div>
          {group.items.map((c) => (
            <DeleteRow
              key={c.difyId}
              record={c}
              active={c.difyId === activeDifyId}
              onOpen={onOpen}
              onDelete={onDelete}
            />
          ))}
        </div>
      ))}
      {hasMore && (
        <div className="px-2 pb-3">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-full text-xs"
            onClick={onLoadMore}
            disabled={loadingMore}
          >
            {loadingMore ? (
              <RefreshCw className="size-3.5 animate-spin" />
            ) : (
              <ChevronDown className="size-3.5" />
            )}
            Load more
          </Button>
        </div>
      )}
    </div>
  )
}
