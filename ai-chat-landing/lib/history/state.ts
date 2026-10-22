import type { ConversationPage, ConversationRecord } from "./types"
import { HistoryError } from "./types"

export type FetchPage = (cursor?: string) => Promise<ConversationPage>

export type HistoryStatus = "idle" | "loading" | "ready" | "error"

export function createHistoryState({ fetchPage }: { fetchPage: FetchPage }) {
  let status: HistoryStatus = "idle"
  let records: ConversationRecord[] = []
  let hasMore = false
  let nextCursor: string | null = null
  let error: HistoryError | undefined
  let loadingMore = false
  let loadInFlight: Promise<void> | null = null

  const toError = (err: unknown): HistoryError =>
    err instanceof HistoryError
      ? err
      : new HistoryError("history_unavailable", undefined, err)

  /** FR-003/005 (spec 015): drop a record after a successful backend delete. */
  function remove(difyId: string): void {
    records = records.filter((r) => r.difyId !== difyId)
  }

  /** FR-006: session activity refreshes a record's lastActivityAt (Today). */
  function touch(difyId: string): void {
    const i = records.findIndex((r) => r.difyId === difyId)
    if (i >= 0) {
      records[i] = { ...records[i], lastActivityAt: Date.now() }
    }
  }

  /** FR-014: promote a draft (or refresh a resumed chat) into the records. */
  function upsert(record: ConversationRecord): void {
    const i = records.findIndex((r) => r.difyId === record.difyId)
    if (i >= 0) records[i] = { ...records[i], ...record }
    else records = [record, ...records]
  }

  const run = async (p: Promise<ConversationPage>): Promise<void> => {
    try {
      const page = await p
      records = [...records, ...page.conversations]
      hasMore = page.hasMore
      nextCursor = page.nextCursor
      status = "ready"
      error = undefined
    } catch (err) {
      error = toError(err)
      status = "error"
    }
  }

  return {
    load(): Promise<void> {
      if (loadInFlight) return loadInFlight
      records = []
      hasMore = false
      nextCursor = null
      status = "loading"
      error = undefined
      loadInFlight = run(fetchPage()).finally(() => {
        loadInFlight = null
      })
      return loadInFlight
    },
    retry(): Promise<void> {
      return this.load()
    },
    loadMore(): Promise<void> {
      if (loadingMore || !hasMore || !nextCursor) return Promise.resolve()
      loadingMore = true
      const done = run(fetchPage(nextCursor)).finally(() => {
        loadingMore = false
      })
      return done
    },
    get status() {
      return status
    },
    get records() {
      return records
    },
    get hasMore() {
      return hasMore
    },
    get error(): HistoryError | undefined {
      return error
    },
    touch,
    upsert,
    remove,
  }
}
