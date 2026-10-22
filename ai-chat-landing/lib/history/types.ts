export type BucketId =
  | "today"
  | "yesterday"
  | "previous-7-days"
  | "last-month"
  | "few-months-ago"

export const BUCKET_ORDER: BucketId[] = [
  "today",
  "yesterday",
  "previous-7-days",
  "last-month",
  "few-months-ago",
]

export const BUCKET_LABELS: Record<BucketId, string> = {
  today: "Today",
  yesterday: "Yesterday",
  "previous-7-days": "Previous 7 days",
  "last-month": "Last month",
  "few-months-ago": "Few months ago",
}

export type ConversationRecord = {
  difyId: string
  title: string
  lastActivityAt: number | null
}

export type BucketedConversations = {
  id: BucketId
  label: string
  items: ConversationRecord[]
}[]

export type HistoryErrorCode =
  | "history_unavailable"
  | "messages_unavailable"
  | "delete_failed"

export class HistoryError extends Error {
  readonly code: HistoryErrorCode

  constructor(code: HistoryErrorCode, message?: string, readonly cause?: unknown) {
    super(message ?? code)
    this.name = "HistoryError"
    this.code = code
  }
}

export type ConversationPage = {
  conversations: ConversationRecord[]
  hasMore: boolean
  nextCursor: string | null
}
