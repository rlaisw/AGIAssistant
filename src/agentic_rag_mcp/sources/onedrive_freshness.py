"""Answer-time staleness probe (spec 007 FR-010..FR-013; research.md D4/D5).

Metadata-only, bounded (5-second total budget, parallel, per-request timeout),
identity by the cloud-stable item id. Honest outcomes: transient failure → no
reminder, no error noise; auth failure → source degraded, no reminder; deleted →
last-available-version note. Never downloads, never blocks the answer.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime

from ..errors import SourceAuthError

log = logging.getLogger("agentic_rag_mcp.freshness")

PROBE_BUDGET_S = 5.0  # user decision 2026-10-11
MAX_WORKERS = 4


def _parse(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)  # 3.11+: trailing Z accepted natively
    except (ValueError, TypeError):
        return None


def probe_cited(cited_docs: list[str], state, sources_by_id: dict) -> list[dict]:
    """Probe the onedrive origins of the cited documents for staleness.

    `sources_by_id` maps onedrive source_id → OneDriveSource. Origins without a
    snapshot (legacy/unverifiable) and non-onedrive origins are skipped. Returns
    StalenessReminder dicts; never raises into the answer path.
    """
    probes = []  # (doc_title, origin, source)
    for doc_id in cited_docs:
        doc_title = (state.get_document(doc_id) or {}).get("title", "")
        for origin in state.origins_for_document(doc_id):
            src = sources_by_id.get(origin["source_id"])
            if src is None or not origin["snapshot"]:
                continue
            probes.append((doc_title, origin, src))
    if not probes:
        return []

    reminders: list[dict] = []
    deadline = time.monotonic() + PROBE_BUDGET_S
    pool = ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(probes)))
    try:
        futures = {pool.submit(_probe_one, t, o, s, state): o for t, o, s in probes}
        for fut in as_completed(futures, timeout=max(0.0, deadline - time.monotonic())):
            reminder = fut.result()
            if reminder:
                reminders.append(reminder)
    except FuturesTimeoutError:
        log.debug("freshness budget exhausted — %d reminder(s) returned", len(reminders))
    finally:
        # never join slow probes — the answer must not wait (FR-010 budget)
        pool.shutdown(wait=False, cancel_futures=True)
    return reminders


def _probe_one(doc_title: str, origin: dict, src, state) -> dict | None:
    snap = origin["snapshot"]
    try:
        meta = src.get_metadata(snap["item_id"])
    except SourceAuthError:
        state.set_health(origin["source_id"], "degraded", "needs sign-in")
        return None  # honest: degraded_sources reports it; no fabricated reminder
    except Exception as exc:  # noqa: BLE001 — transient: silent, never block the answer
        log.debug("freshness probe failed for %s: %s", snap["item_id"], exc)
        return None
    if meta is None:  # item id unfindable = genuinely deleted (renames keep the id)
        title = doc_title or snap["item_id"]
        log.debug("freshness: %s deleted in cloud — embedded copy is last version", snap["item_id"])
        return {
            "kind": "deleted", "title": title, "path": None, "locator": snap["item_id"],
            "embedded_at": snap.get("embedded_at", ""),
            "message": f"'{title}' no longer exists in OneDrive; the embedded copy from "
                       f"{snap.get('embedded_at', 'unknown time')} is the last available version.",
        }
    cloud_t, snap_t = _parse(meta["last_modified"]), _parse(snap.get("last_modified", ""))
    if not cloud_t or not snap_t or cloud_t <= snap_t:
        log.debug("freshness: %s unchanged (embedded %s)", snap["item_id"],
                  snap.get("last_modified", "?"))
        return None  # unchanged or unverifiable — no fabricated reminder
    log.debug("freshness: %s stale (embedded %s < cloud %s) — reminder emitted",
              snap["item_id"], snap.get("last_modified"), meta["last_modified"])
    update_handle = meta.get("path") or meta["title"]
    return {
        "kind": "stale", "title": meta["title"], "path": meta.get("path"),
        "locator": snap["item_id"], "embedded_at": snap.get("embedded_at", ""),
        "modified_at": meta["last_modified"],
        "message": f"'{meta['title']}' was modified in OneDrive on {meta['last_modified']} — "
                   f"after it was embedded on {snap.get('embedded_at', 'unknown time')}. "
                   f"The answer above is from the older copy. To update it, ask to re-embed "
                   f"'{update_handle}' (or item {snap['item_id']}).",
    }
