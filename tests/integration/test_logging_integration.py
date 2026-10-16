"""Logging integration (spec 008; matrix I1/I2/I4, SC-001/002/004/005):
session events land as leveled records in the file; failures are never
silent; rotation caps disk; user input stays out of INFO records."""

import json
import logging

import httpx

import agentic_rag_mcp.sources.graph_auth as ga
from agentic_rag_mcp.config import Config
from agentic_rag_mcp.server import build_server


def call(server, name, args):
    import asyncio
    raw = asyncio.run(server.call_tool(name, args))
    structured = [b["result"] for b in raw if isinstance(b, dict) and "result" in b]
    if structured:
        return structured[0]
    texts = [getattr(b, "text", "") for b in raw if getattr(b, "text", "")]
    joined = "".join(texts).strip()
    return json.loads(joined) if joined else None


def _server(tmp_path, monkeypatch, **log_kw):
    import agentic_rag_mcp.server as server_mod
    monkeypatch.setattr(server_mod, "build_providers", lambda cfg: [])
    kw = {"log_level": "INFO", "log_file": tmp_path / "log" / "server.log"}
    kw.update(log_kw)
    cfg = Config(state_db=tmp_path / "s.sqlite3", vector_dir=tmp_path / "v",
                 decider_enabled=False, **kw)
    return build_server(cfg), cfg.log_file


def _flush():
    for h in logging.getLogger().handlers:
        h.flush()


def _text(path):
    _flush()
    return path.read_text(errors="replace") if path.exists() else ""


def _info_lines(text):
    return [ln for ln in text.splitlines() if " INFO " in ln]


def test_session_events_recorded_at_info(tmp_path, monkeypatch):
    """SC-001/I1: startup, watcher cycle, embed, answer → INFO records;
    question text and file names stay out of INFO lines."""
    import agentic_rag_mcp.sources.local_folder as lf
    monkeypatch.setattr(lf, "extract_text", lambda path: f"local text {path.name}")
    srv, log = _server(tmp_path, monkeypatch)

    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "note.pdf").write_bytes(b"x")
    call(srv, "sources_add", {"type": "local_folder", "config": {"path": str(folder)}})
    call(srv, "sources_sync", {})
    call(srv, "ask", {"question": "xyzzymarker secret question", "mode": "fast"})

    text = _text(log)
    assert "logging configured" in text                       # startup record (FR-001)
    assert any("periodic sync" in ln for ln in _info_lines(text))     # watcher cycle
    assert any("local sync" in ln and "1 ingested" in ln
               for ln in _info_lines(text))                   # embed counts (FR-002)
    assert any("ask answered" in ln for ln in _info_lines(text))      # answer event
    joined = "\n".join(_info_lines(text))
    assert "xyzzymarker" not in joined                         # question text: DEBUG-only
    assert "note.pdf" not in joined                            # file names: DEBUG-only


def test_failures_logged_with_reasons(tmp_path, monkeypatch):
    """SC-002/I2: user-visible failures have matching WARN/ERROR records."""
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")

    def fake_get(url, headers=None, params=None, timeout=None, follow_redirects=None):
        return httpx.Response(404, json={}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    srv, log = _server(tmp_path, monkeypatch)

    sid = call(srv, "sources_add", {"type": "onedrive", "config": {"client_id": "x"}})["source_id"]
    out = call(srv, "onedrive_embed_files", {"source_id": sid, "files": ["/missing.docx"]})
    assert out["results"][0]["status"] == "not_found"          # honest tool outcome
    text = _text(log)
    assert "missing.docx" in text and "not_found" in text       # …and its WARN twin
    assert "WARNING" in text

    with __import__("pytest").raises(Exception):
        call(srv, "onedrive_list_files", {"source_id": "bogus"})  # unknown source
    text = _text(log)
    assert "bogus" in text and "source not found" in text       # tool guard logged too


def test_rotation_caps_disk(tmp_path, monkeypatch):
    """SC-004/I4: sustained writes past the threshold stay bounded."""
    _srv, log = _server(tmp_path, monkeypatch, rotation_size_mb=0.001, rotation_count=2)
    for i in range(80):
        logging.getLogger("agentic_rag_mcp.it").info("filler record %03d padded", i)
    _flush()
    gens = sorted(log.parent.glob("server.log*"))
    assert len(gens) >= 2                                       # rollover happened
    total = sum(p.stat().st_size for p in gens)
    assert total <= int(0.001 * 1024 * 1024) * 3 + 1024         # bounded usage


# ---- SC-003/I3 + SC-005: DEBUG tracing + user-input scans -------------------

def test_debug_trace_end_to_end(tmp_path, monkeypatch):
    """SC-003: DEBUG on — one ask traces entry(question) → routing → hits → completion."""
    srv, log = _server(tmp_path, monkeypatch, log_level="DEBUG")
    call(srv, "ask", {"question": "tracemarker question", "mode": "fast"})
    text = _text(log)
    lines = text.splitlines()

    def first(marker):
        return next(i for i, ln in enumerate(lines) if marker in ln)

    entry = first("tracemarker question")        # tool entry carries the question (DEBUG)
    route = next(i for i, ln in enumerate(lines) if "routing" in ln and " DEBUG " in ln)
    hits = next(i for i, ln in enumerate(lines) if "retrieval[" in ln and " DEBUG " in ln)
    done = first("ask answered")
    assert entry < route < hits < done           # ordered, readable from the file alone


def test_user_input_absent_above_debug(tmp_path, monkeypatch):
    """SC-005: question text and file names appear ONLY in DEBUG records."""
    import agentic_rag_mcp.sources.local_folder as lf
    monkeypatch.setattr(lf, "extract_text", lambda path: f"local text {path.name}")
    srv, log = _server(tmp_path, monkeypatch, log_level="DEBUG")
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "secretfile.pdf").write_bytes(b"x")
    call(srv, "sources_add", {"type": "local_folder", "config": {"path": str(folder)}})
    call(srv, "ask", {"question": "scanmarker question", "mode": "fast"})

    text = _text(log)
    info_lines = "\n".join(_info_lines(text))
    assert "scanmarker" not in info_lines          # question text never above DEBUG
    assert "secretfile.pdf" not in info_lines     # file names never above DEBUG
    # …while the DEBUG records do carry them (the trace is genuinely there)
    assert any("scanmarker" in ln for ln in text.splitlines() if " DEBUG " in ln)
    assert any("secretfile" in ln for ln in text.splitlines() if " DEBUG " in ln)


def test_sqlite_sync_records_summary(tmp_path, monkeypatch):
    """US1/AC2 (convergence T018): sqlite syncs get their count-based INFO record."""
    import sqlite3

    db = tmp_path / "notes.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT)")
        conn.execute("INSERT INTO notes (body) VALUES ('sqlite logging probe')")
        conn.commit()
    srv, log = _server(tmp_path, monkeypatch)
    call(srv, "sources_add", {"type": "sqlite",
                              "config": {"db_path": str(db), "table": "notes"}})
    call(srv, "sources_sync", {})
    text = _text(log)
    assert any("sqlite sync" in ln and "1 added" in ln for ln in _info_lines(text))
