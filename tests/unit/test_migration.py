"""One-time migration (spec 007 FR-016, research.md D7; matrix U8/SC-008):
re-embeds only snapshot-less legacy onedrive origins; idempotent by construction;
deleted-at-migration keeps the copy honestly; auth-expired retries next startup."""

import agentic_rag_mcp.ingestion.pipeline as pl
from agentic_rag_mcp.errors import SourceAuthError
from agentic_rag_mcp.ingestion.pipeline import IngestionPipeline
from agentic_rag_mcp.store.state import StateStore


class FakeSource:
    def __init__(self, resolve_map=None, raises=None, content=b"refreshed text"):
        self.resolve_map = resolve_map or {}
        self.raises = raises
        self.content = content
        self.resolve_calls = []

    def resolve(self, request):
        self.resolve_calls.append(request)
        if self.raises:
            raise self.raises
        return self.resolve_map.get(request)

    def download(self, url):
        return self.content


class FakeVectors:
    def upsert_document(self, collection, document_id, title, text, embedder=None):
        return 1

    def delete_document(self, collection, document_id):
        pass


def _legacy_state(tmp_path):
    """sid with 2 legacy (snapshot-less) origins + 1 fresh origin + 1 local origin."""
    store = StateStore(tmp_path / "s.sqlite3")
    sid = store.add_source("onedrive", {"client_id": "x"})
    legacy_docs = []
    for i in range(2):
        doc_id, _, _ = store.upsert_document(
            content_hash=f"old{i}", title=f"f{i}.docx", extracted_text=f"old text {i}",
            media_type="docx", source_id=sid, locator=f"LEG{i}")
        legacy_docs.append(doc_id)
    fresh_id, _, _ = store.upsert_document(
        content_hash="fresh", title="fresh.docx", extracted_text="fresh text",
        media_type="docx", source_id=sid, locator="FRESH")
    store.set_origin_snapshot(sid, "FRESH", {
        "item_id": "FRESH", "last_modified": "2026-10-01T00:00:00Z",
        "etag": None, "embedded_at": "2026-10-01T00:05:00Z"})
    local_sid = store.add_source("local_folder", {"path": "/p"})
    store.upsert_document(content_hash="local", title="local.pdf", extracted_text="l",
                          media_type="pdf", source_id=local_sid, locator="/p/local.pdf")
    return store, sid, legacy_docs, fresh_id, local_sid


def _pipeline(store):
    return IngestionPipeline(store, FakeVectors(), embedder=None)


def _res(locator, last_modified="2026-10-09T00:00:00Z"):
    return {"locator": locator, "title": f"{locator.lower()}.docx", "size": 10,
            "last_modified": last_modified, "download_url": f"https://dl/{locator}",
            "ext": "docx"}


def test_migration_reembeds_only_pending_then_idempotent(tmp_path, monkeypatch):
    """U8/SC-008: exactly the snapshot-less origins are re-embedded; second run is a no-op."""
    monkeypatch.setattr(pl, "extract_text", lambda path: path.read_text())
    store, sid, _legacy_docs, fresh_id, _local = _legacy_state(tmp_path)
    src = FakeSource(resolve_map={f"LEG{i}": _res(f"LEG{i}") for i in range(2)},
                     content=b"refreshed text")
    pipeline = _pipeline(store)

    report = pipeline.migrate_onedrive_sources({sid: src})
    assert set(report.values()) == {"updated"} and len(report) == 2  # replaced, not duplicated
    assert store.onedrive_origins_without_snapshot(sid) == []  # snapshots established
    # fresh origin untouched: same content, same snapshot
    assert store.get_document(fresh_id)["extracted_text"] == "fresh text"
    assert store.get_origin_snapshot(sid, "FRESH")["last_modified"] == "2026-10-01T00:00:00Z"

    calls_after_first = len(src.resolve_calls)
    report2 = pipeline.migrate_onedrive_sources({sid: src})
    assert report2 == {}
    assert len(src.resolve_calls) == calls_after_first  # nothing re-attempted


def test_migration_deleted_file_keeps_copy_and_retries(tmp_path, monkeypatch):
    """U8: cloud-deleted legacy file → existing copy kept; origin stays pending."""
    monkeypatch.setattr(pl, "extract_text", lambda path: path.read_text())
    store, sid, legacy_docs, _, _ = _legacy_state(tmp_path)
    src = FakeSource(resolve_map={"LEG0": _res("LEG0")})  # LEG1 resolves to None (deleted)
    report = _pipeline(store).migrate_onedrive_sources({sid: src})
    assert report["LEG0"] == "updated"  # legacy content replaced
    assert report["LEG1"] == "not_found"
    assert store.get_document(legacy_docs[1])["extracted_text"] == "old text 1"  # copy kept
    assert [p["locator"] for p in store.onedrive_origins_without_snapshot(sid)] == ["LEG1"]


def test_migration_auth_expired_honest_and_retried(tmp_path, monkeypatch):
    """U8: expired token → source degraded, honest report; retried next startup."""
    monkeypatch.setattr(pl, "extract_text", lambda path: path.read_text())
    store, sid, _legacy_docs, _, _ = _legacy_state(tmp_path)
    src = FakeSource(raises=SourceAuthError("Microsoft sign-in required"))
    pipeline = _pipeline(store)
    report = pipeline.migrate_onedrive_sources({sid: src})
    assert report == {}  # nothing embedded
    assert store.get_source(sid)["health"] == "degraded"
    assert len(store.onedrive_origins_without_snapshot(sid)) == 2  # still pending


def test_migration_noop_without_legacy(tmp_path, monkeypatch):
    """U8/SC-008: no onedrive sources (current deployment) → no-op."""
    store = StateStore(tmp_path / "s.sqlite3")
    assert _pipeline(store).migrate_onedrive_sources({}) == {}
