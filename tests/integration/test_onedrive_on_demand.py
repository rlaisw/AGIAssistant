"""On-demand invariants (spec 007; matrix I1/I5, SC-001/SC-004 context):
a connected OneDrive source never ingests on its own — not at add, not after
sign-in, not on watcher cycles; the watcher makes zero Graph requests."""

import json
import time

import httpx

import agentic_rag_mcp.sources.graph_auth as ga
from agentic_rag_mcp.config import Config
from agentic_rag_mcp.server import build_server
from agentic_rag_mcp.store.state import StateStore


def call(server, name, args):
    import asyncio
    raw = asyncio.run(server.call_tool(name, args))
    structured = [b["result"] for b in raw if isinstance(b, dict) and "result" in b]
    if structured:
        return structured[0]
    texts = [getattr(b, "text", "") for b in raw if getattr(b, "text", "")]
    joined = "".join(texts).strip()
    return json.loads(joined) if joined else None


def _server(tmp_path, monkeypatch):
    import agentic_rag_mcp.server as server_mod
    monkeypatch.setattr(server_mod, "build_providers", lambda cfg: [])
    cfg = Config(state_db=tmp_path / "s.sqlite3", vector_dir=tmp_path / "v",
                 decider_enabled=False)
    return build_server(cfg), cfg


def _graph_spy(monkeypatch):
    """Any httpx.get call is a Graph request — record and fail the test loudly."""
    calls = []

    def spy(url, *a, **kw):
        calls.append(str(url))
        raise AssertionError(f"unexpected Graph/web HTTP call: {url}")

    monkeypatch.setattr(httpx, "get", spy)
    return calls


def test_connect_never_ingests_across_watcher_cycles(tmp_path, monkeypatch):
    """SC-001/I1: add + sign-in + watcher cycles → 0 embedded documents."""
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    graph_calls = _graph_spy(monkeypatch)
    srv, cfg = _server(tmp_path, monkeypatch)

    out = call(srv, "sources_add", {"type": "onedrive", "config": {"client_id": "x"}})
    assert out["status"] == "ok"
    sid = out["source_id"]

    # full watcher cycle via the manual-sync tool: local+sqlite processed, onedrive skipped
    results = call(srv, "sources_sync", {})
    assert sid not in results  # watcher made no entry — zero Graph traffic

    assert StateStore(cfg.state_db).doc_count() == 0  # nothing ingested, ever
    assert graph_calls == []


def test_auth_completion_never_ingests(tmp_path, monkeypatch):
    """FR-002/C5: sign-in completes → source healthy → zero documents, zero Graph calls."""
    import msal
    graph_calls = _graph_spy(monkeypatch)
    monkeypatch.setattr(ga.GraphAuth, "device_sign_in", lambda self, flow=None: {"ok": True})
    monkeypatch.setattr(
        msal.PublicClientApplication, "initiate_device_flow",
        lambda self, scopes=None, **kw: {"user_code": "CODE",
                                         "verification_uri": "https://microsoft.com/devicelogin"})
    srv, cfg = _server(tmp_path, monkeypatch)

    add_out = call(srv, "sources_add", {"type": "onedrive", "config": {"client_id": "x"}})
    sid = add_out["source_id"]
    call(srv, "sources_auth", {"source_id": sid})

    deadline = time.time() + 5
    store = StateStore(cfg.state_db)
    while time.time() < deadline:
        if store.get_source(sid)["health"] == "healthy":
            break
        time.sleep(0.1)
    assert store.get_source(sid)["health"] == "healthy"  # sign-in completed

    assert store.doc_count() == 0  # and nothing was ingested by it
    assert graph_calls == []


# ---- SC-002/I2: embed only the named files; exactly those become searchable --

import re


def _drive_graph(monkeypatch):
    """Graph fake: 50 files listed (metadata), only 3 resolvable+downloadable."""
    items = [{"id": f"ID{i}", "name": f"file{i:02}.docx", "size": 1000,
              "lastModifiedDateTime": "2026-10-05T10:00:00Z", "file": {}}
             for i in range(50)]
    content = {"/file00.docx": b"alpha revenue figures in the report",
               "/file17.docx": b"beta budget lines and costs",
               "/file42.docx": b"gamma roadmap items for next year"}
    ids = {p: f"ID{int(p[5:7])}" for p in content}
    calls = {"downloads": 0, "resolves": []}

    def fake_get(url, headers=None, params=None, timeout=None, follow_redirects=None):
        u = str(url)
        if "children" in u:
            return httpx.Response(200, json={"value": items}, request=httpx.Request("GET", u))
        m = re.search(r"root:(/\S+)$", u)
        if m and m.group(1) in content:
            path = m.group(1)
            calls["resolves"].append(path)
            return httpx.Response(200, json={
                "id": ids[path], "name": path.lstrip("/"), "size": 1000,
                "lastModifiedDateTime": "2026-10-05T10:00:00Z",
                "@microsoft.graph.downloadUrl": f"https://dl.example{path}"},
                request=httpx.Request("GET", u))
        if u.startswith("https://dl.example/"):
            calls["downloads"] += 1
            return httpx.Response(200, content=content[u.replace("https://dl.example", "")],
                                  request=httpx.Request("GET", u))
        return httpx.Response(404, json={}, request=httpx.Request("GET", u))

    monkeypatch.setattr(httpx, "get", fake_get)
    return calls


def test_embed_only_named_files_searchable(tmp_path, monkeypatch):
    """SC-002: list all 50, embed 3 → exactly 3 searchable; other 47 never return."""
    import agentic_rag_mcp.ingestion.pipeline as pl
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    monkeypatch.setattr(pl, "extract_text", lambda path: path.read_text())
    calls = _drive_graph(monkeypatch)
    srv, cfg = _server(tmp_path, monkeypatch)

    sid = call(srv, "sources_add", {"type": "onedrive", "config": {"client_id": "x"}})["source_id"]
    listing = call(srv, "onedrive_list_files", {"source_id": sid})
    assert len(listing["files"]) == 50          # metadata for the whole drive view
    assert listing["truncated"] is False
    assert calls["downloads"] == 0               # listing downloaded nothing

    out = call(srv, "onedrive_embed_files",
               {"source_id": sid,
                "files": ["/file00.docx", "/file17.docx", "/file42.docx"]})
    assert out["embedded"] == 3 and out["failed"] == 0
    assert StateStore(cfg.state_db).doc_count() == 3
    assert calls["downloads"] == 3              # only the named files were downloaded

    hits = call(srv, "search", {"query": "revenue figures report"})
    assert hits, "embedded file00 must be searchable"
    assert all(h["title"] in ("file00.docx", "file17.docx", "file42.docx") for h in hits)
    # never-embedded files never become searchable: any query only ever hits the 3
    other = call(srv, "search", {"query": "delta inventory"})
    assert all(h["title"] in ("file00.docx", "file17.docx", "file42.docx") for h in other)


# ---- SC-003/I3: staleness reminder on cited answers (FR-010..FR-013) --------

def _mutable_graph(monkeypatch):
    """Graph fake with mutable cloud state: edit the file, the probe must notice."""
    cloud = {"last_modified": "2026-10-05T10:00:00Z", "name": "file00.docx"}
    downloads = {"n": 0}
    item = {"id": "ID00", "size": 1000, "file": {},
            "lastModifiedDateTime": "2026-10-05T10:00:00Z",
            "@microsoft.graph.downloadUrl": "https://dl.example/file00.docx"}

    def fake_get(url, headers=None, params=None, timeout=None, follow_redirects=None):
        u = str(url)
        if "children" in u:
            return httpx.Response(200, json={"value": [
                {"id": "ID00", "name": cloud["name"], "size": 1000, "file": {},
                 "lastModifiedDateTime": cloud["last_modified"]}]},
                request=httpx.Request("GET", u))
        if "root:/file00.docx" in u:
            return httpx.Response(200, json={**item, "name": cloud["name"],
                                             "lastModifiedDateTime": cloud["last_modified"]},
                                  request=httpx.Request("GET", u))
        if u.endswith("/items/ID00"):  # freshness probe (metadata only)
            return httpx.Response(200, json={
                "id": "ID00", "name": cloud["name"],
                "lastModifiedDateTime": cloud["last_modified"], "eTag": '"w1"',
                "parentReference": {"path": "/drive/root:"}},
                request=httpx.Request("GET", u))
        if u.startswith("https://dl.example/"):
            downloads["n"] += 1
            return httpx.Response(200, content=b"alpha revenue figures in the report",
                                  request=httpx.Request("GET", u))
        return httpx.Response(404, json={}, request=httpx.Request("GET", u))

    monkeypatch.setattr(httpx, "get", fake_get)
    return cloud, downloads


def test_staleness_reminder_on_ask_same_turn(tmp_path, monkeypatch):
    """SC-003: cloud edit → answer carries the reminder + both timestamps; no download."""
    import agentic_rag_mcp.ingestion.pipeline as pl
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    monkeypatch.setattr(pl, "extract_text", lambda path: path.read_text())
    cloud, downloads = _mutable_graph(monkeypatch)
    srv, _cfg = _server(tmp_path, monkeypatch)

    sid = call(srv, "sources_add", {"type": "onedrive", "config": {"client_id": "x"}})["source_id"]
    call(srv, "onedrive_embed_files", {"source_id": sid, "files": ["/file00.docx"]})
    assert downloads["n"] == 1

    cloud["last_modified"] = "2026-10-09T09:00:00Z"  # the user edits the file in OneDrive

    result = call(srv, "ask", {"question": "what does the report say about revenue?", "mode": "fast"})
    warnings = result["freshness_warnings"]
    assert len(warnings) == 1 and warnings[0]["kind"] == "stale"
    assert warnings[0]["modified_at"] == "2026-10-09T09:00:00Z"
    assert warnings[0]["embedded_at"].startswith("2026-10-")  # snapshot timestamp present
    assert "older copy" in result["answer"]  # reminder appended to the answer text
    assert downloads["n"] == 1  # FR-011: the reminder NEVER triggers a download

    cloud["last_modified"] = "2026-10-05T10:00:00Z"  # unchanged → no reminder
    result2 = call(srv, "ask", {"question": "what does the report say about revenue?", "mode": "fast"})
    assert result2["freshness_warnings"] == []


# ---- SC-004/I4: one-command explicit refresh --------------------------------

def test_explicit_update_flow_new_content_only(tmp_path, monkeypatch):
    """SC-004: reminder → explicit re-embed → new content only, reminder gone."""
    import agentic_rag_mcp.ingestion.pipeline as pl
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    monkeypatch.setattr(pl, "extract_text", lambda path: path.read_text())
    cloud = {"last_modified": "2026-10-05T10:00:00Z", "content": b"alpha revenue figures"}

    def fake_get(url, headers=None, params=None, timeout=None, follow_redirects=None):
        u = str(url)
        if "children" in u:
            return httpx.Response(200, json={"value": [
                {"id": "ID00", "name": "file00.docx", "size": 1000, "file": {},
                 "lastModifiedDateTime": cloud["last_modified"]}]},
                request=httpx.Request("GET", u))
        if "root:/file00.docx" in u or u.endswith("/items/ID00"):
            return httpx.Response(200, json={
                "id": "ID00", "name": "file00.docx", "size": 1000,
                "lastModifiedDateTime": cloud["last_modified"],
                "@microsoft.graph.downloadUrl": "https://dl.example/f",
                "eTag": '"w1"', "parentReference": {"path": "/drive/root:"}},
                request=httpx.Request("GET", u))
        if u.startswith("https://dl.example/"):
            return httpx.Response(200, content=cloud["content"], request=httpx.Request("GET", u))
        return httpx.Response(404, json={}, request=httpx.Request("GET", u))

    monkeypatch.setattr(httpx, "get", fake_get)
    srv, cfg = _server(tmp_path, monkeypatch)
    sid = call(srv, "sources_add", {"type": "onedrive", "config": {"client_id": "x"}})["source_id"]

    call(srv, "onedrive_embed_files", {"source_id": sid, "files": ["/file00.docx"]})
    cloud["last_modified"] = "2026-10-09T09:00:00Z"
    cloud["content"] = b"beta updated revenue numbers"
    asked = call(srv, "ask", {"question": "revenue?", "mode": "fast"})
    assert asked["freshness_warnings"] and asked["freshness_warnings"][0]["kind"] == "stale"

    out = call(srv, "onedrive_embed_files", {"source_id": sid, "files": ["/file00.docx"]})
    assert out["updated"] == 1  # changed content: replaced, not duplicated
    assert StateStore(cfg.state_db).doc_count() == 1

    asked2 = call(srv, "ask", {"question": "revenue?", "mode": "fast"})
    assert asked2["freshness_warnings"] == []          # reminder cleared
    assert "beta updated revenue numbers" in asked2["answer"]
    assert "alpha revenue figures" not in asked2["answer"]  # old content evicted


# ---- SC-005/I5/I6: local sources keep automatic updates; watcher isolation --

def test_local_autosync_untouched_with_onedrive_registered(tmp_path, monkeypatch):
    """SC-005/US5: local auto-sync still works; watcher never touches onedrive."""
    import agentic_rag_mcp.sources.local_folder as lf
    monkeypatch.setattr(lf, "extract_text", lambda path: f"local text {path.name}")
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    graph_calls = _graph_spy(monkeypatch)
    srv, cfg = _server(tmp_path, monkeypatch)

    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "note.pdf").write_bytes(b"x")
    call(srv, "sources_add", {"type": "local_folder", "config": {"path": str(folder)}})
    assert StateStore(cfg.state_db).doc_count() == 1  # auto-embedded at add

    sid = call(srv, "sources_add", {"type": "onedrive", "config": {"client_id": "x"}})["source_id"]

    (folder / "second.pdf").write_bytes(b"y")
    results = call(srv, "sources_sync", {})  # full watcher cycle
    assert sid not in results                # onedrive skipped by the watcher
    assert StateStore(cfg.state_db).doc_count() == 2  # new local file auto-embedded
    assert graph_calls == []                 # zero Graph traffic

    health = {s["id"]: s["health"] for s in call(srv, "sources_list", {})}
    assert health[sid] == "healthy"  # watcher never transitions onedrive health


def test_watcher_file_has_no_graph_references():
    """Constitution V pin: the watcher structurally cannot call Graph."""
    import re
    from pathlib import Path

    src = (Path(__file__).resolve().parents[2] / "src/agentic_rag_mcp/ingestion/watchers.py").read_text()
    for banned in ("graph_auth", "OneDriveSource", "sync_onedrive", "httpx"):
        assert banned not in src, f"watchers.py must not reference {banned}"
    assert not re.search(r"\bdelta\b", src), "watchers.py must not reference delta sync"
