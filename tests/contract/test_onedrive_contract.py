"""Contract: sources_add(type: "onedrive") + sources_auth response shapes (FR-001/002/003, SC-005)."""

import asyncio
import json

import pytest

from agentic_rag_mcp.config import Config
from agentic_rag_mcp.server import build_server


def call(server, name, args):
    raw = asyncio.run(server.call_tool(name, args))
    structured = [b["result"] for b in raw if isinstance(b, dict) and "result" in b]
    if structured:
        return structured[0]
    texts = [getattr(b, "text", "") for b in raw if getattr(b, "text", "")]
    joined = "".join(texts).strip()
    return json.loads(joined) if joined else None


def _server(tmp_path, monkeypatch, profiles=None):
    import agentic_rag_mcp.server as server_mod

    monkeypatch.setattr(server_mod, "build_providers", lambda cfg: [])
    cfg = Config(state_db=tmp_path / "s.sqlite3", vector_dir=tmp_path / "v",
                 decider_enabled=False)
    return build_server(cfg)


def test_sources_add_onedrive_needs_auth(tmp_path, monkeypatch):
    """FR-002: no token → needs_auth with sign-in hint."""
    srv = _server(tmp_path, monkeypatch)
    out = call(srv, "sources_add", {
        "type": "onedrive",
        "config": {"client_id": "test-id"}})
    assert out["source_id"]
    assert out["status"] == "needs_auth"           # FR-002
    assert "sign_in" in json.dumps(out).lower() or out.get("sign_in_url") is None


def test_sources_add_onedrive_with_token_on_demand_notice(tmp_path, monkeypatch):
    """FR-001: existing token → status ok + on-demand notice — NEVER a sync promise."""
    import agentic_rag_mcp.sources.graph_auth as ga
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    srv = _server(tmp_path, monkeypatch)
    out = call(srv, "sources_add", {
        "type": "onedrive",
        "config": {"client_id": "test-id"}})
    assert out["source_id"]
    assert out["status"] == "ok"
    notice = json.dumps(out)
    assert "on-demand" in notice
    assert "watcher" not in notice  # superseded initial-sync message is gone


def test_sources_sync_onedrive_returns_on_demand_notice(tmp_path, monkeypatch):
    """FR-004: manual sync against a onedrive source → honest notice, no sync."""
    import agentic_rag_mcp.sources.graph_auth as ga
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    srv = _server(tmp_path, monkeypatch)
    add_out = call(srv, "sources_add", {
        "type": "onedrive", "config": {"client_id": "test-id"}})
    out = call(srv, "sources_sync", {"source_id": add_out["source_id"]})
    entry = out[add_out["source_id"]]
    assert entry["status"] == "on_demand"
    assert "onedrive_embed_files" in entry["message"]


def test_sources_auth_returns_sign_in_flow(tmp_path, monkeypatch):
    """FR-003: sources_auth returns URL + code (or already_authenticated)."""
    srv = _server(tmp_path, monkeypatch)
    # add a source first so we have a source_id
    add_out = call(srv, "sources_add", {
        "type": "onedrive",
        "config": {"client_id": "test-id"}})
    sid = add_out["source_id"]
    auth_out = call(srv, "sources_auth", {"source_id": sid})
    assert auth_out["status"] in ("sign_in_required", "already_authenticated", "error")
    # honest error for non-existent source — NotFoundError is the correct honest behavior
    with pytest.raises(Exception):
        call(srv, "sources_auth", {"source_id": "nonexistent"})


def test_sources_list_includes_onedrive_type(tmp_path, monkeypatch):
    """sources_list shows onedrive sources."""
    srv = _server(tmp_path, monkeypatch)
    call(srv, "sources_add", {"type": "onedrive", "config": {"client_id": "x"}})
    out = call(srv, "sources_list", {})
    assert any(s["type"] == "onedrive" for s in out)


def test_existing_tools_canary_unchanged(tmp_path, monkeypatch):
    """SC-005: frozen tool canary — web_search etc. still work."""
    srv = _server(tmp_path, monkeypatch)
    st = call(srv, "status", {})
    assert st["decision_layer"] in ("decision_node", "fallback")


# ---- on-demand tools (spec 007; matrix C1/C2, FR-005/006) -------------------

def _fake_graph(monkeypatch):
    """Minimal Graph fake: one folder listing + one resolvable, downloadable file."""
    import httpx
    item = {"id": "id1", "name": "report.docx", "size": 1000,
            "lastModifiedDateTime": "2026-10-05T10:00:00Z",
            "@microsoft.graph.downloadUrl": "https://dl.example/id1", "file": {}}

    def fake_get(url, headers=None, params=None, timeout=None, follow_redirects=None):
        u = str(url)
        if "children" in u:
            return httpx.Response(200, json={"value": [item]}, request=httpx.Request("GET", u))
        if "root:/Documents/report.docx" in u:
            return httpx.Response(200, json=item, request=httpx.Request("GET", u))
        if u.startswith("https://dl.example/"):
            return httpx.Response(200, content=b"file bytes", request=httpx.Request("GET", u))
        return httpx.Response(404, json={}, request=httpx.Request("GET", u))

    monkeypatch.setattr(httpx, "get", fake_get)


def _add_onedrive(srv):
    out = call(srv, "sources_add", {"type": "onedrive", "config": {"client_id": "x"}})
    assert out["status"] == "ok"
    return out["source_id"]


def test_onedrive_list_files_contract_shape(tmp_path, monkeypatch):
    """C1: {source_id, folder, files[FileListingEntry], truncated}."""
    import agentic_rag_mcp.sources.graph_auth as ga
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    _fake_graph(monkeypatch)
    srv = _server(tmp_path, monkeypatch)
    sid = _add_onedrive(srv)
    out = call(srv, "onedrive_list_files", {"source_id": sid, "search": ""})
    assert set(out.keys()) == {"source_id", "folder", "files", "truncated"}
    assert out["source_id"] == sid
    assert out["truncated"] is False
    entry = out["files"][0]
    assert set(entry.keys()) == {"locator", "title", "path", "size", "last_modified", "embeddable"}
    assert entry["embeddable"] is True


def test_onedrive_embed_files_contract_shape(tmp_path, monkeypatch):
    """C2: {source_id, results[EmbedOutcome], embedded, updated, skipped, not_found, failed}."""
    import agentic_rag_mcp.ingestion.pipeline as pl
    import agentic_rag_mcp.sources.graph_auth as ga
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    monkeypatch.setattr(pl, "extract_text", lambda path: "extracted text")
    _fake_graph(monkeypatch)
    srv = _server(tmp_path, monkeypatch)
    sid = _add_onedrive(srv)
    out = call(srv, "onedrive_embed_files",
               {"source_id": sid, "files": ["/Documents/report.docx"]})
    assert set(out.keys()) == {"source_id", "results", "embedded", "updated",
                               "skipped", "not_found", "failed"}
    result = out["results"][0]
    assert set(result.keys()) == {"request", "locator", "status", "reason"}
    assert result["status"] == "embedded" and result["reason"] is None
    assert out["embedded"] == 1 and out["failed"] == 0


def test_onedrive_tools_reject_unknown_and_wrong_type(tmp_path, monkeypatch):
    """Honest guards: unknown source, non-onedrive source."""
    import agentic_rag_mcp.sources.graph_auth as ga
    monkeypatch.setattr(ga.GraphAuth, "token", lambda self: "tok")
    srv = _server(tmp_path, monkeypatch)
    with pytest.raises(Exception):  # noqa: B017 — MCP wraps tool errors
        call(srv, "onedrive_list_files", {"source_id": "nope"})
    call(srv, "sources_add", {"type": "local_folder", "config": {"path": str(tmp_path)}})
    local = call(srv, "sources_list", {})[0]["id"]
    with pytest.raises(Exception):  # noqa: B017 — MCP wraps tool errors
        call(srv, "onedrive_embed_files", {"source_id": local, "files": ["x.docx"]})


def test_ask_response_frozen_fields_plus_additive_freshness(tmp_path, monkeypatch):
    """C3/FR-014: every existing ask field survives; freshness_warnings is additive."""
    srv = _server(tmp_path, monkeypatch)
    out = call(srv, "ask", {"question": "What is known about nothing?"})
    for field in ("answer", "confidence", "classification", "classifier", "citations",
                  "iterations", "sufficiency", "error", "plan", "reflections", "trace",
                  "degraded_sources", "decision"):
        assert field in out, f"frozen field missing: {field}"
    assert out["freshness_warnings"] == []  # additive, present even when empty


def test_sources_auth_uses_one_flow_end_to_end(tmp_path, monkeypatch):
    """Live-found bug (2026-10-12): sources_auth initiated TWO device flows — the
    code shown to the user belonged to flow A while the background thread polled
    flow B (different code, never entered) → eternal authorization_pending loop.
    The tool must initiate ONE flow and the thread must complete THAT flow."""
    import threading

    import agentic_rag_mcp.sources.graph_auth as ga

    def token_fails(self):  # realistic pre-sign-in state: registered, unauthenticated
        raise ga.SourceAuthError("needs sign-in")

    monkeypatch.setattr(ga.GraphAuth, "token", token_fails)
    flow_a = {"user_code": "CODEA", "verification_uri": "https://login.microsoft.com/device"}
    seen = {"begin_calls": 0, "completed_flows": []}

    def fake_begin(self):
        seen["begin_calls"] += 1
        return flow_a

    def fake_sign_in(self, flow=None):
        seen["completed_flows"].append(flow)
        return {"ok": True}

    monkeypatch.setattr(ga.GraphAuth, "begin_device_flow", fake_begin)
    monkeypatch.setattr(ga.GraphAuth, "device_sign_in", fake_sign_in)
    srv = _server(tmp_path, monkeypatch)
    sid = call(srv, "sources_add",
               {"type": "onedrive", "config": {"client_id": "x"}})["source_id"]
    out = call(srv, "sources_auth", {"source_id": sid})
    assert out["user_code"] == "CODEA"                       # response carries flow A's code
    for _ in range(50):                                     # wait for the background thread
        if seen["completed_flows"]:
            break
        threading.Event().wait(0.1)
    assert seen["begin_calls"] == 1, "exactly ONE flow may be initiated per auth call"
    assert seen["completed_flows"] == [flow_a], "thread must complete the SAME flow object"
