"""StateStore snapshot storage (spec 007, data-model.md; matrix U5):
per-origin freshness snapshot, item_id==locator invariant, probe/migration queries."""

import pytest

from agentic_rag_mcp.store.state import StateStore


def _store(tmp_path):
    return StateStore(tmp_path / "s.sqlite3")


def _origin(store, source_type="onedrive", locator="ITEM1", title="f.pdf", media_type="pdf"):
    config = {"client_id": "x"} if source_type == "onedrive" else {"path": "/p"}
    sid = store.add_source(source_type, config)
    doc_id, _outcome, _orphan = store.upsert_document(
        content_hash=f"hash-{locator}-{title}", title=title, extracted_text="text",
        media_type=media_type, source_id=sid, locator=locator)
    return sid, doc_id


_SNAP = {"item_id": "ITEM1", "last_modified": "2026-10-05T10:00:00Z",
         "etag": '"w1"', "embedded_at": "2026-10-05T10:05:00Z"}


def test_snapshot_roundtrip_and_invariant(tmp_path):
    store = _store(tmp_path)
    sid, _doc = _origin(store)
    assert store.get_origin_snapshot(sid, "ITEM1") is None  # nothing before embed success
    store.set_origin_snapshot(sid, "ITEM1", _SNAP)
    assert store.get_origin_snapshot(sid, "ITEM1") == _SNAP


def test_snapshot_rejects_mismatched_item_id(tmp_path):
    """data-model.md: snapshot.item_id MUST equal the origin's locator."""
    store = _store(tmp_path)
    sid, _doc = _origin(store)
    with pytest.raises(ValueError):
        store.set_origin_snapshot(sid, "ITEM1", {**_SNAP, "item_id": "OTHER"})


def test_origins_for_document(tmp_path):
    store = _store(tmp_path)
    sid, doc = _origin(store, locator="ITEM1")
    rows = store.origins_for_document(doc)
    assert len(rows) == 1
    assert rows[0]["source_id"] == sid
    assert rows[0]["locator"] == "ITEM1"
    assert rows[0]["snapshot"] is None  # present-but-null before first snapshot
    store.set_origin_snapshot(sid, "ITEM1", _SNAP)
    assert store.origins_for_document(doc)[0]["snapshot"] == _SNAP
    assert store.origins_for_document("nonexistent-doc") == []


def test_onedrive_origins_without_snapshot(tmp_path):
    """Migration pending set: only snapshot-less onedrive origins of this source."""
    store = _store(tmp_path)
    sid, _d1 = _origin(store, locator="LEGACY")          # snapshot-less onedrive origin
    _d2 = _origin(store, locator="FRESH")                # snapshotted onedrive origin
    store.set_origin_snapshot(sid, "FRESH", {**_SNAP, "item_id": "FRESH"})
    _local_sid, _d3 = _origin(store, source_type="local_folder",
                              locator="/tmp/local.pdf")  # never part of the set
    pending = store.onedrive_origins_without_snapshot(sid)
    assert [p["locator"] for p in pending] == ["LEGACY"]
    assert pending[0]["document_id"] == _d1
    # a source with no origins at all → empty (no-op migration)
    sid2, _d4 = _origin(store, locator="X2")
    store.set_origin_snapshot(sid2, "X2", {**_SNAP, "item_id": "X2"})
    assert store.onedrive_origins_without_snapshot(sid2) == []
