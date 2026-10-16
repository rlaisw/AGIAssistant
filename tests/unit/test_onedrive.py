"""OneDrive source, on-demand model (spec 007; matrix U1/U2, research.md D1/D2):
metadata-only listing (recursive, paginated, filterable), one-call file resolution,
download, honest auth/rate-limit errors. Supersedes the delta-sync tests."""

import httpx
import pytest

from agentic_rag_mcp.errors import ProviderError, SourceAuthError
from agentic_rag_mcp.sources.onedrive import OneDriveSource


class FakeAuth:
    def token(self):
        return "fake-token"


def _item(item_id, name, size=1000, download_url="https://dl.example/file", **extra):
    d = {"id": item_id, "name": name, "size": size,
         "lastModifiedDateTime": "2026-10-01T00:00:00Z",
         "@microsoft.graph.downloadUrl": download_url, "file": {"mimeType": "application/pdf"}}
    d.update(extra)
    return d


def _mock_graph(monkeypatch, responses):
    """Mock httpx.get returning Graph responses matched by URL substring."""
    calls = []

    def fake_get(url, headers=None, params=None, timeout=None, follow_redirects=None):
        calls.append({"url": url, "params": params})
        for pattern, resp_data in responses:
            if pattern in url:
                return httpx.Response(200, json=resp_data, request=httpx.Request("GET", url))
        return httpx.Response(200, json={"value": []}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    return calls


def _src(config=None):
    return OneDriveSource(FakeAuth(), config or {})


# ---- U1: metadata-only listing (FR-005) -----------------------------------

def test_list_files_recursive_pagination_and_filter(monkeypatch):
    """Nested folders walked, nextLink followed, name filter is case-insensitive."""
    _mock_graph(monkeypatch, [
        ("root/children", {"value": [_item("r1", "report.docx"),
                                     {"id": "sub", "name": "Sub", "folder": {},
                                      "lastModifiedDateTime": "2026-10-01T00:00:00Z"}],
                            "@odata.nextLink": "https://g/page2"}),
        ("page2", {"value": [_item("r2", "other.pdf")]}),
        ("root:/Sub:/children", {"value": [_item("r3", "REPORT2.PDF"),
                                           _item("p1", "photo.png")]}),
    ])
    out = _src().list_files(search="report")
    titles = [f["title"] for f in out["files"]]
    assert titles == ["report.docx", "REPORT2.PDF"]  # recursive + filter, page 2 followed
    assert out["truncated"] is False
    paths = [f["path"] for f in out["files"]]
    assert paths == ["/report.docx", "/Sub/REPORT2.PDF"]


def test_list_files_embeddable_flag(monkeypatch):
    """embeddable = supported extension AND within the size cap."""
    _mock_graph(monkeypatch, [
        ("root/children", {"value": [
            _item("a", "ok.docx"),
            _item("p", "photo.png"),
            _item("big", "huge.pdf", size=60 * 1024 * 1024),
        ]}),
    ])
    out = _src().list_files()
    by_id = {f["locator"]: f for f in out["files"]}
    assert by_id["a"]["embeddable"] is True
    assert by_id["p"]["embeddable"] is False
    assert by_id["big"]["embeddable"] is False


def test_list_files_truncated_over_limit(monkeypatch):
    """Result bound: more files existed than returned → truncated=True."""
    _mock_graph(monkeypatch, [
        ("root/children", {"value": [_item("a", "a.pdf"), _item("b", "b.pdf")]}),
    ])
    out = _src().list_files(limit=1)
    assert len(out["files"]) == 1
    assert out["truncated"] is True


def test_list_files_empty_is_honest(monkeypatch):
    """No matches → files: [], truncated False — no error, no fabrication."""
    _mock_graph(monkeypatch, [("root/children", {"value": []})])
    out = _src().list_files(search="nothing")
    assert out["files"] == []
    assert out["truncated"] is False


def test_list_files_uses_config_folder_scope(monkeypatch):
    """folder_path config scopes the listing root."""
    calls = _mock_graph(monkeypatch, [
        ("root:/Documents:/children", {"value": [
            {"id": "sub", "name": "Sub", "folder": {}}]}),
        ("root:/Documents/Sub:/children", {"value": []}),
    ])
    _src({"folder_path": "/Documents"}).list_files()
    assert any("root:/Documents:/children" in c["url"] for c in calls)
    assert any("root:/Documents/Sub:/children" in c["url"] for c in calls)


def test_list_files_app_only_user_prefix(monkeypatch):
    """App-only config lists via /users/{user}/drive."""
    calls = _mock_graph(monkeypatch, [("children", {"value": []})])
    _src({"user": "user@tenant.example"}).list_files()
    assert any("/users/user@tenant.example/drive/" in c["url"] for c in calls)


# ---- U2: one-call file resolution (FR-006, research.md D2) ------------------

def test_resolve_by_path_single_call(monkeypatch):
    """Path ('/' or '.' present) resolved via /me/drive/root:{path}."""
    calls = _mock_graph(monkeypatch, [
        ("root:/Documents/report.docx", _item("id1", "report.docx")),
    ])
    out = _src().resolve("/Documents/report.docx")
    assert out["locator"] == "id1"
    assert out["title"] == "report.docx"
    assert out["size"] == 1000
    assert out["last_modified"] == "2026-10-01T00:00:00Z"
    assert out["download_url"] == "https://dl.example/file"
    assert out["ext"] == "docx"
    assert len(calls) == 1  # exactly one Graph call per file


def test_resolve_by_item_id(monkeypatch):
    """Bare id (no '/' or '.') resolved via /me/drive/items/{id}."""
    calls = _mock_graph(monkeypatch, [("items/id1", _item("id1", "report.docx"))])
    out = _src().resolve("id1")
    assert out["locator"] == "id1"
    assert any("/me/drive/items/id1" in c["url"] for c in calls)


def test_resolve_404_returns_none(monkeypatch):
    """Missing path → None (caller reports honest not_found)."""
    def fake_get(url, **kw):
        return httpx.Response(404, json={}, request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx, "get", fake_get)
    assert _src().resolve("/nope/missing.pdf") is None


def test_get_metadata_probe_fields(monkeypatch):
    """Freshness probe returns id/name/path/last_modified/etag; 404 → None (deleted)."""
    def fake_get(url, headers=None, params=None, timeout=None, follow_redirects=None):
        if url.endswith("/items/id1"):
            return httpx.Response(200, json={"id": "id1", "name": "report.docx",
                                             "lastModifiedDateTime": "2026-10-09T00:00:00Z",
                                             "eTag": '"w2"',
                                             "parentReference": {"path": "/drive/root:/Documents"}},
                                  request=httpx.Request("GET", url))
        return httpx.Response(404, json={}, request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx, "get", fake_get)
    out = _src().get_metadata("id1")
    assert out == {"locator": "id1", "title": "report.docx", "path": "/Documents/report.docx",
                   "last_modified": "2026-10-09T00:00:00Z", "etag": '"w2"'}
    assert _src().get_metadata("gone-id") is None  # genuinely deleted


# ---- honest errors (FR-007/D9) ----------------------------------------------

def test_auth_error_raises_source_auth_error(monkeypatch):
    def fake_get(url, **kw):
        return httpx.Response(401, json={}, request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(SourceAuthError):
        _src().list_files()


def test_rate_limit_raises_provider_error(monkeypatch):
    def fake_get(url, **kw):
        return httpx.Response(429, json={}, request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(ProviderError, match="rate limited"):
        _src().list_files()


def test_download_returns_bytes(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        return httpx.Response(200, content=b"pdf-bytes", request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx, "get", fake_get)
    assert OneDriveSource.download("https://dl.example/file") == b"pdf-bytes"


# ---- U3/U4/X1: on-demand embed pipeline (FR-006..FR-009, research.md D9) ----

from agentic_rag_mcp.ingestion.parsers import ParseSkipped
from agentic_rag_mcp.ingestion.pipeline import IngestionPipeline
from agentic_rag_mcp.store.state import StateStore


class FakeSource:
    """Stands in for OneDriveSource: scripted resolve/download results."""

    def __init__(self, resolve_map=None, resolve_raise=None, content=b"same text"):
        self.resolve_map = resolve_map or {}
        self.resolve_raise = resolve_raise or {}
        self.content = content

    def resolve(self, request):
        if request in self.resolve_raise:
            raise self.resolve_raise[request]
        return self.resolve_map.get(request)

    def download(self, url):
        return self.content


class FakeVectors:
    def __init__(self):
        self.upserts, self.deleted = [], []

    def upsert_document(self, collection, document_id, title, text, embedder=None):
        self.upserts.append(document_id)
        return 1

    def delete_document(self, collection, document_id):
        self.deleted.append(document_id)


def _pipeline(tmp_path):
    store = StateStore(tmp_path / "s.sqlite3")
    return store, IngestionPipeline(store, FakeVectors(), embedder=None)


def _resolved(locator="ID1", title="report.docx", ext="docx",
              last_modified="2026-10-05T10:00:00Z", size=1000, download_url="auto"):
    return {"locator": locator, "title": title, "size": size, "last_modified": last_modified,
            "download_url": f"https://dl.example/{locator}" if download_url == "auto" else download_url,
            "ext": ext}


def test_embed_outcomes_sequential_no_cap(tmp_path, monkeypatch):
    """U3/FR-006: 60 named files processed in order — no count cap, one outcome each."""
    import agentic_rag_mcp.ingestion.pipeline as pl
    n = iter(range(1000))
    monkeypatch.setattr(pl, "extract_text", lambda path: f"unique text {next(n)}")
    store, pipeline = _pipeline(tmp_path)
    sid = store.add_source("onedrive", {"client_id": "x"})
    src = FakeSource(resolve_map={f"/f{i}.docx": _resolved(locator=f"ID{i}", title=f"f{i}.docx")
                                  for i in range(60)})
    out = pipeline.embed_onedrive_files(sid, src, [f"/f{i}.docx" for i in range(60)])
    assert len(out["results"]) == 60
    assert [r["request"] for r in out["results"]] == [f"/f{i}.docx" for i in range(60)]  # order
    assert out["embedded"] == 60 and out["failed"] == 0
    assert store.get_origin_snapshot(sid, "ID7")["item_id"] == "ID7"  # snapshot per success


def test_embed_error_taxonomy_batch_continues(tmp_path, monkeypatch):
    """X1/D9: every failure mode has an honest per-file reason; the batch continues."""
    import agentic_rag_mcp.ingestion.pipeline as pl

    def fake_extract(path):
        if "corrupt" in path.name:
            raise ParseSkipped(f"no extractable text: {path.name}")
        return path.read_text()

    monkeypatch.setattr(pl, "extract_text", fake_extract)
    store, pipeline = _pipeline(tmp_path)
    sid = store.add_source("onedrive", {"client_id": "x"})
    src = FakeSource(
        resolve_map={
            "/missing.pdf": None,
            "/photo.png": _resolved(locator="P", title="photo.png", ext="png"),
            "/huge.pdf": _resolved(locator="H", title="huge.pdf", size=60 * 1024 * 1024),
            "/nourl.docx": _resolved(locator="N", download_url=None),
            "/corrupt.pdf": _resolved(locator="corrupt", title="corrupt.pdf", ext="pdf"),
            "/ok.docx": _resolved(locator="ok", title="ok.docx"),
        },
        resolve_raise={"/throttled.docx": ProviderError("graph rate limited (429) — retry this file")},
        content=b"good text")
    out = pipeline.embed_onedrive_files(sid, src, [
        "/missing.pdf", "/photo.png", "/huge.pdf", "/nourl.docx",
        "/throttled.docx", "/corrupt.pdf", "/ok.docx"])
    by_req = {r["request"]: r for r in out["results"]}
    assert by_req["/missing.pdf"]["status"] == "not_found" and by_req["/missing.pdf"]["reason"]
    assert by_req["/photo.png"]["status"] == "skipped" and "unsupported" in by_req["/photo.png"]["reason"]
    assert by_req["/huge.pdf"]["status"] == "skipped" and "too large" in by_req["/huge.pdf"]["reason"]
    assert by_req["/nourl.docx"]["status"] == "failed" and "download URL" in by_req["/nourl.docx"]["reason"]
    assert by_req["/throttled.docx"]["status"] == "failed" and "rate limited" in by_req["/throttled.docx"]["reason"]
    assert by_req["/corrupt.pdf"]["status"] == "skipped" and "extractable" in by_req["/corrupt.pdf"]["reason"]
    assert by_req["/ok.docx"]["status"] == "embedded"  # batch continued past every failure
    assert (out["embedded"], out["skipped"], out["not_found"], out["failed"]) == (1, 3, 1, 2)


def test_embed_dedup_idempotent_and_refresh(tmp_path, monkeypatch):
    """U4/FR-008: identical re-embed = honest no-change; changed content evicts old."""
    import agentic_rag_mcp.ingestion.pipeline as pl
    monkeypatch.setattr(pl, "extract_text", lambda path: path.read_text())
    store, pipeline = _pipeline(tmp_path)
    sid = store.add_source("onedrive", {"client_id": "x"})

    first = FakeSource(resolve_map={"/a.docx": _resolved(locator="A", title="a.docx")},
                       content=b"same text")
    out1 = pipeline.embed_onedrive_files(sid, first, ["/a.docx"])
    assert out1["results"][0]["status"] == "embedded"

    # identical content + unchanged cloud metadata → honest "already current", no duplicate
    out2 = pipeline.embed_onedrive_files(sid, first, ["/a.docx"])
    assert out2["results"][0]["status"] == "skipped"
    assert "already current" in out2["results"][0]["reason"]
    assert store.doc_count() == 1

    # changed content → old chunks evicted, snapshot refreshed
    changed = FakeSource(resolve_map={"/a.docx": _resolved(locator="A", title="a.docx",
                                                            last_modified="2026-10-09T00:00:00Z")},
                         content=b"new text")
    out3 = pipeline.embed_onedrive_files(sid, changed, ["/a.docx"])
    assert out3["results"][0]["status"] == "updated"
    assert store.doc_count() == 1  # old document evicted, not duplicated
    assert store.get_origin_snapshot(sid, "A")["last_modified"] == "2026-10-09T00:00:00Z"


def test_multiple_onedrive_sources_independent(tmp_path, monkeypatch):
    """Spec edge case: multiple OneDrive sources are independent — disjoint
    embedded files, per-source snapshots, per-source token caches."""
    import agentic_rag_mcp.ingestion.pipeline as pl
    from agentic_rag_mcp.server import _onedrive_auth
    monkeypatch.setattr(pl, "extract_text", lambda path: path.read_text())
    store, pipeline = _pipeline(tmp_path)
    sid_a = store.add_source("onedrive", {"client_id": "app-a"})
    sid_b = store.add_source("onedrive", {"client_id": "app-b"})
    assert sid_a != sid_b

    src_a = FakeSource(resolve_map={"/a.docx": _resolved(locator="A1", title="a.docx")},
                       content=b"content from drive A")
    src_b = FakeSource(resolve_map={"/b.docx": _resolved(locator="B1", title="b.docx")},
                       content=b"content from drive B")
    pipeline.embed_onedrive_files(sid_a, src_a, ["/a.docx"])
    pipeline.embed_onedrive_files(sid_b, src_b, ["/b.docx"])

    # disjoint embedded files, each with its own snapshot — no cross-source leakage
    assert store.get_origin_snapshot(sid_a, "A1")["item_id"] == "A1"
    assert store.get_origin_snapshot(sid_b, "B1")["item_id"] == "B1"
    assert store.get_origin_snapshot(sid_a, "B1") is None
    assert store.get_origin_snapshot(sid_b, "A1") is None
    assert store.onedrive_origins_without_snapshot(sid_a) == []
    assert store.onedrive_origins_without_snapshot(sid_b) == []

    # per-source token caches: distinct ids → distinct cache paths, own client_id
    from pathlib import Path
    tokens = Path.home() / ".config/agentic-rag-mcp/tokens"
    assert _onedrive_auth(store.get_source(sid_a))._cache_path == tokens / f"{sid_a}.json"
    assert _onedrive_auth(store.get_source(sid_b))._cache_path == tokens / f"{sid_b}.json"


def test_scopes_exclude_msal_reserved_values():
    """Live-found bug (2026-10-11): MSAL reserves profile/openid/offline_access —
    passing any of them explicitly makes initiate_device_flow fail. MSAL requests
    offline_access itself, so refresh tokens still work. Sites.Read.All was also
    trimmed: the app carries it only as an Application permission, and OneDrive
    /me/drive needs just delegated Files.Read (minimal-scope principle)."""
    from agentic_rag_mcp.sources.graph_auth import SCOPES

    assert SCOPES == ["Files.Read"]
    assert not set(SCOPES) & {"profile", "offline_access", "openid"}


def test_graph_auth_uses_tenant_authority(tmp_path, monkeypatch):
    """Live-found bug (2026-10-11): tenant_id was stored but never used — the
    device flow always ran against /common, which rejects single-tenant apps.
    MSAL construction does live OIDC discovery, so the app is mocked (no network)."""
    import msal

    from agentic_rag_mcp.sources.graph_auth import GraphAuth

    seen = []

    class FakeApp:
        def __init__(self, client_id, authority=None, token_cache=None):
            seen.append(authority)

    monkeypatch.setattr(msal, "PublicClientApplication", FakeApp)
    GraphAuth("cid", tmp_path / "t.json", tenant_id="ca1293ac-d322-43f4-ae3b-e18e5fa51fb9")
    assert seen[-1] == "https://login.microsoftonline.com/ca1293ac-d322-43f4-ae3b-e18e5fa51fb9"
    GraphAuth("cid", tmp_path / "t2.json")
    assert seen[-1] == "https://login.microsoftonline.com/common"  # default preserved
