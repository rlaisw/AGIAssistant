"""Freshness probe (spec 007 FR-010..FR-013; matrix U6/U7, research.md D4/D5):
stale/unchanged/deleted/timeout/auth outcomes; item-id identity survives renames;
probe failures never fabricate reminders and never break answers."""

import time

import agentic_rag_mcp.sources.onedrive_freshness as fr
from agentic_rag_mcp.errors import ProviderError, SourceAuthError
from agentic_rag_mcp.sources.onedrive_freshness import probe_cited
from agentic_rag_mcp.store.state import StateStore

SNAP = {"item_id": "ID1", "last_modified": "2026-10-05T10:00:00+00:00",
        "etag": '"w1"', "embedded_at": "2026-10-05T10:05:00+00:00"}


class FakeSource:
    def __init__(self, result=None, raises=None, delay=0.0):
        self.result, self.raises, self.delay = result, raises, delay

    def get_metadata(self, item_id):
        if self.delay:
            time.sleep(self.delay)
        if self.raises:
            raise self.raises
        return self.result


def _state_with_origin(tmp_path, snapshot=None, title="report.docx", locator="ID1"):
    store = StateStore(tmp_path / "s.sqlite3")
    sid = store.add_source("onedrive", {"client_id": "x"})
    doc_id, _, _ = store.upsert_document(
        content_hash=f"h{locator}{title}", title=title, extracted_text="text",
        media_type="pdf", source_id=sid, locator=locator)
    if snapshot:
        store.set_origin_snapshot(sid, locator, snapshot)
    return store, sid, doc_id


def _meta(**kw):
    return {"locator": "ID1", "title": kw.get("title", "report.docx"),
            "path": kw.get("path", "/Documents/report.docx"),
            "last_modified": kw.get("last_modified", "2026-10-05T10:00:00+00:00"),
            "etag": kw.get("etag", '"w1"')}


def test_stale_file_produces_reminder_with_timestamps(tmp_path):
    """U6: cloud modified after snapshot → reminder with both timestamps + update handle."""
    store, sid, doc = _state_with_origin(tmp_path, SNAP)
    src = FakeSource(_meta(last_modified="2026-10-09T00:00:00+00:00"))
    out = probe_cited([doc], store, {sid: src})
    assert len(out) == 1
    r = out[0]
    assert r["kind"] == "stale" and r["locator"] == "ID1"
    assert r["embedded_at"] == SNAP["embedded_at"]
    assert r["modified_at"] == "2026-10-09T00:00:00+00:00"
    assert "older copy" in r["message"] and "ID1" in r["message"]


def test_unchanged_file_no_reminder(tmp_path):
    store, sid, doc = _state_with_origin(tmp_path, SNAP)
    src = FakeSource(_meta())  # identical last_modified
    assert probe_cited([doc], store, {sid: src}) == []


def test_deleted_file_last_version_note(tmp_path):
    """FR-012: cloud 404 by id → deleted note, not a fabricated staleness.
    Data-model: modified_at is absent (not null) for the deleted variant."""
    store, sid, doc = _state_with_origin(tmp_path, SNAP)
    src = FakeSource(None)  # get_metadata → None = deleted
    out = probe_cited([doc], store, {sid: src})
    assert out[0]["kind"] == "deleted"
    assert "modified_at" not in out[0]  # absent per data-model.md StalenessReminder
    assert "last available version" in out[0]["message"]
    assert out[0]["title"] == "report.docx"


def test_probe_transient_failure_silent(tmp_path):
    """FR-013: transient errors → no reminder, no error noise, source stays healthy."""
    store, sid, doc = _state_with_origin(tmp_path, SNAP)
    src = FakeSource(raises=ProviderError("graph request failed: boom"))
    assert probe_cited([doc], store, {sid: src}) == []
    assert store.get_source(sid)["health"] == "healthy"


def test_probe_auth_failure_marks_degraded_no_reminder(tmp_path):
    """FR-013: auth failure → source degraded (degraded_sources reports it), no reminder."""
    store, sid, doc = _state_with_origin(tmp_path, SNAP)
    src = FakeSource(raises=SourceAuthError("Microsoft sign-in required"))
    assert probe_cited([doc], store, {sid: src}) == []
    assert store.get_source(sid)["health"] == "degraded"
    assert "sign-in" in store.get_source(sid)["health_reason"]


def test_probe_identity_survives_rename(tmp_path):
    """U7: id probe after a cloud rename/move → reminder carries the NEW title/path."""
    store, sid, doc = _state_with_origin(tmp_path, SNAP)
    src = FakeSource(_meta(title="renamed.docx", path="/Moved/renamed.docx",
                           last_modified="2026-10-08T00:00:00+00:00"))
    r = probe_cited([doc], store, {sid: src})[0]
    assert r["locator"] == "ID1"  # same identity
    assert r["title"] == "renamed.docx" and r["path"] == "/Moved/renamed.docx"


def test_budget_expiry_skips_reminder(tmp_path, monkeypatch):
    """5-second budget: slow probes are abandoned — answer never waits, no crash."""
    monkeypatch.setattr(fr, "PROBE_BUDGET_S", 0.01)
    store, sid, doc = _state_with_origin(tmp_path, SNAP)
    src = FakeSource(_meta(last_modified="2026-10-09T00:00:00+00:00"), delay=0.2)
    assert probe_cited([doc], store, {sid: src}) == []


def test_unverifiable_legacy_origin_no_reminder(tmp_path):
    """Snapshot-less (legacy) origin: cannot compare → no fabricated reminder."""
    store, sid, doc = _state_with_origin(tmp_path, snapshot=None)
    src = FakeSource(_meta(last_modified="2026-10-09T00:00:00+00:00"))
    assert probe_cited([doc], store, {sid: src}) == []


def test_local_origins_never_probed(tmp_path):
    """Local-file citations are out of probe scope (always fresh by auto-sync)."""
    store = StateStore(tmp_path / "s.sqlite3")
    sid = store.add_source("local_folder", {"path": "/p"})
    doc_id, _, _ = store.upsert_document(
        content_hash="hl", title="local.pdf", extracted_text="t",
        media_type="pdf", source_id=sid, locator="/p/local.pdf")
    assert probe_cited([doc_id], store, {}) == []
