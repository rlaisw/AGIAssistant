"""Incremental ingestion pipeline (FR-004): detect add/change/delete,
parse, dedup, embed, upsert into LanceDB, record per-item status.
"""

from __future__ import annotations

import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from ..errors import RagError, SourceAuthError
from ..sources.local_folder import LocalFolderSource, ParseSkipped
from ..sources.onedrive import SUPPORTED_EXTENSIONS
from .dedup import content_hash
from .parsers import extract_text

log = logging.getLogger("agentic_rag_mcp.pipeline")


def _now() -> str:
    return datetime.now(UTC).isoformat()


class IngestionPipeline:
    def __init__(self, state, vectors, embedder, collection: str = "default") -> None:
        self.state = state
        self.vectors = vectors
        self.embedder = embedder
        self.collection = collection

    def sync_local_folder(self, source_id: str, folder: str | Path) -> dict:
        src = LocalFolderSource(folder)
        stats = {"added": 0, "updated": 0, "deleted": 0, "skipped": []}
        seen = set()
        for path in src.scan():
            locator = str(path)
            seen.add(locator)
            try:
                text, mtype = src.read_item(path)
            except ParseSkipped as exc:
                stats["skipped"].append({"locator": locator, "reason": str(exc)})
                continue
            except RagError as exc:
                stats["skipped"].append({"locator": locator, "reason": exc.message})
                continue
            doc_id, outcome, orphan_id = self.state.upsert_document(
                content_hash=content_hash(text),
                title=path.name,
                extracted_text=text,
                media_type=mtype,
                source_id=source_id,
                locator=locator,
            )
            count = self.vectors.upsert_document(
                collection=self.collection,
                document_id=doc_id,
                title=path.name,
                text=text,
                embedder=self.embedder,
            )
            if orphan_id:  # evicted by a content change — drop its stale chunks
                self.vectors.delete_document(self.collection, orphan_id)
            if outcome == "created":
                stats["added"] += 1
            elif outcome == "updated":
                stats["updated"] += 1
            log.debug("ingested %s (%s chunks)", locator, count)  # locator: DEBUG-only
        # deletions: origins under this source not seen this cycle
        existing = self.state.get_source(source_id)
        prev = set((existing or {}).get("sync_state", {}).get("locators", []))
        for stale in prev - seen:
            doc = self.state.remove_origin(source_id, stale)
            if doc:
                self.vectors.delete_document(self.collection, doc)
            stats["deleted"] += 1
        self.state.set_sync_state(source_id, {"locators": sorted(seen)})
        self.state.set_health(source_id, "healthy", None)
        log.info("local sync %s: %d ingested, %d updated, %d removed",
                 source_id, stats["added"], stats["updated"], stats["deleted"])
        return stats

    def _onedrive_max_bytes(self, source_id: str) -> int:
        cfg = (self.state.get_source(source_id) or {}).get("config", {})
        return cfg.get("max_file_size_mb", 50) * 1024 * 1024

    def embed_onedrive_files(self, source_id: str, source, files: list[str]) -> dict:
        """Embed ONLY the named files, one-time per call (FR-006..FR-009, research.md D9).

        Sequential, no per-command cap; per-file honest outcomes; mid-batch cloud
        failures (429/5xx/network) continue the batch; every success records a
        freshness snapshot. SourceAuthError propagates to the tool (sign-in gate).
        """
        max_bytes = self._onedrive_max_bytes(source_id)
        counts = {"embedded": 0, "updated": 0, "skipped": 0, "not_found": 0, "failed": 0}
        results = []
        for request in files:
            outcome = self._embed_one_onedrive(source_id, source, request, max_bytes)
            results.append(outcome)
            counts[outcome["status"]] += 1
            if outcome["status"] not in ("embedded", "updated"):  # no silent failures (FR-002)
                log.warning("embed %s → %s (%s)", request, outcome["status"],
                            outcome["reason"])
        log.info("onedrive embed %s: %d embedded, %d updated, %d skipped, "
                 "%d not_found, %d failed", source_id, counts["embedded"],
                 counts["updated"], counts["skipped"], counts["not_found"],
                 counts["failed"])
        return {"source_id": source_id, "results": results, **counts}

    def _embed_one_onedrive(self, source_id: str, source, request: str, max_bytes: int) -> dict:
        try:
            item = source.resolve(request)
        except SourceAuthError:
            raise  # tool-level gate: the source needs sign-in, nothing embedded
        except RagError as exc:
            return {"request": request, "locator": None, "status": "failed", "reason": exc.message}
        if not item:
            return {"request": request, "locator": None, "status": "not_found",
                    "reason": "no file at this path/id"}
        locator, ext, size = item["locator"], item["ext"], item["size"]
        if f".{ext}" not in SUPPORTED_EXTENSIONS:
            return {"request": request, "locator": locator, "status": "skipped",
                    "reason": f"unsupported format: .{ext or '(none)'}"}
        if size > max_bytes:
            return {"request": request, "locator": locator, "status": "skipped",
                    "reason": f"file too large: {size // (1024 * 1024)} MB > {max_bytes // (1024 * 1024)} MB"}
        if not item["download_url"]:
            return {"request": request, "locator": locator, "status": "failed",
                    "reason": "no download URL"}
        prev = self.state.get_origin_snapshot(source_id, locator)
        if prev and prev.get("last_modified") == item["last_modified"]:
            return {"request": request, "locator": locator, "status": "skipped",
                    "reason": "already current — embedded content matches the cloud copy"}
        try:
            content = source.download(item["download_url"])
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td) / f"{locator}.{ext}"
                tmp.write_bytes(content)
                text = extract_text(tmp)  # same parser chain as local files
        except ParseSkipped as exc:
            return {"request": request, "locator": locator, "status": "skipped",
                    "reason": str(exc)}
        except SourceAuthError:
            raise
        except RagError as exc:
            return {"request": request, "locator": locator, "status": "failed",
                    "reason": exc.message}
        doc_id, outcome, orphan_id = self.state.upsert_document(
            content_hash=content_hash(text),
            title=item["title"],
            extracted_text=text,
            media_type=ext,
            source_id=source_id,
            locator=locator,
        )
        self.vectors.upsert_document(
            collection=self.collection,
            document_id=doc_id,
            title=item["title"],
            text=text,
            embedder=self.embedder,
        )
        if orphan_id:  # content changed at this origin — drop the stale chunks
            self.vectors.delete_document(self.collection, orphan_id)
        self.state.set_origin_snapshot(source_id, locator, {
            "item_id": locator, "last_modified": item["last_modified"],
            "etag": None, "embedded_at": _now()})
        log.debug("embedded %s (%s) from onedrive", item["title"], request)  # name: DEBUG-only
        return {"request": request, "locator": locator,
                "status": "embedded" if outcome == "created" else "updated", "reason": None}

    def migrate_onedrive_sources(self, sources_by_id: dict) -> dict:
        """One-time migration (FR-016, research.md D7): re-embed every legacy
        onedrive origin lacking a freshness snapshot. Idempotent by construction —
        success writes the snapshot which removes the origin from the pending set;
        failures (deleted/throttled) are retried on the next startup, never
        silently dropped. Returns {locator: status} for honest reporting."""
        report = {}
        for sid, source in sources_by_id.items():
            for pending in self.state.onedrive_origins_without_snapshot(sid):
                locator = pending["locator"]
                try:
                    outcome = self._embed_one_onedrive(sid, source, locator,
                                                       self._onedrive_max_bytes(sid))
                except SourceAuthError:
                    self.state.set_health(sid, "degraded", "needs sign-in")
                    log.warning("migration: source %s needs sign-in — retried next startup", sid)
                    break  # dead token: nothing more will succeed for this source
                report[locator] = outcome["status"]
                if outcome["status"] in ("embedded", "updated"):
                    log.info("migration re-embedded %s", locator)
                else:
                    log.warning("migration: %s → %s (%s)", locator,
                                outcome["status"], outcome["reason"])
        return report

    def sync_sqlite(self, source_id: str, source) -> dict:
        stats = {"added": 0, "updated": 0, "deleted": 0, "skipped": []}
        seen = set()
        for row in source.rows():
            seen.add(row["locator"])
            doc_id, outcome, orphan_id = self.state.upsert_document(
                content_hash=row["hash"],
                title=row["title"],
                extracted_text=row["text"],
                media_type="sqlite_record",
                source_id=source_id,
                locator=row["locator"],
            )
            self.vectors.upsert_document(
                collection=self.collection,
                document_id=doc_id,
                title=row["title"],
                text=row["text"],
                embedder=self.embedder,
            )
            if orphan_id:  # evicted by a content change — drop its stale chunks
                self.vectors.delete_document(self.collection, orphan_id)
            if outcome == "created":
                stats["added"] += 1
            elif outcome == "updated":
                stats["updated"] += 1
        existing = self.state.get_source(source_id)
        prev = set((existing or {}).get("sync_state", {}).get("locators", []))
        for stale in prev - seen:
            doc = self.state.remove_origin(source_id, stale)
            if doc:
                self.vectors.delete_document(self.collection, doc)
            stats["deleted"] += 1
        self.state.set_sync_state(source_id, {"locators": sorted(seen)})
        self.state.set_health(source_id, "healthy", None)
        log.info("sqlite sync %s: %d added, %d updated, %d removed",
                 source_id, stats["added"], stats["updated"], stats["deleted"])
        return stats
