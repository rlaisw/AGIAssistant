"""Contract: completion-page routes + additive ppt_export result (spec 010).

Hermetic (fake scripts); the real toolchain is exercised in
tests/integration/test_ppt_completion_pipeline.py. Matrix refs: D01, D05,
D07–D12. Reuses the spec 009 fake-script conventions.
"""

from __future__ import annotations

import asyncio
import json
import textwrap
from pathlib import Path

import pytest

from agentic_rag_mcp.config import Config
from agentic_rag_mcp.server import build_server

PASSING_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
    '<g id="t" data-pptx-bounds="64 64 400 100"><text x="64" y="100" '
    'font-size="24" fill="#212121">Hello</text></g></svg>'
)


def call(server, name, args):
    raw = asyncio.run(server.call_tool(name, args))
    structured = [b["result"] for b in raw if isinstance(b, dict) and "result" in b]
    if structured:
        return structured[0]
    texts = [getattr(b, "text", "") for b in raw if getattr(b, "text", "")]
    joined = "".join(texts).strip()
    return json.loads(joined) if joined else None


def fake_scripts(scripts_root: Path) -> None:
    scripts = scripts_root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / "project_manager.py").write_text(textwrap.dedent("""
        import os, sys
        name = sys.argv[2]
        pid = f"{name}_20260101"
        root = os.environ["PPT_PROJECTS_ROOT"]
        os.makedirs(os.path.join(root, pid, "svg_output"), exist_ok=True)
        print(f"[OK] Project initialized: projects/{pid}")
    """))
    (scripts / "icon_sync.py").write_text("import sys\nprint('[OK] 0 icon(s)')\n")
    (scripts / "svg_quality_checker.py").write_text("import sys\nprint('[REPORT] done')\n")
    (scripts / "svg_to_pptx.py").write_text(textwrap.dedent("""
        import os, sys
        ws = sys.argv[1]
        out = f"{ws}/exports"
        os.makedirs(out, exist_ok=True)
        with open(f"{out}/deck_120000.pptx", "wb") as f:
            f.write(b"PK\\x03\\x04fake")
        print(f"[PPTX] {out}/deck_120000.pptx")
    """))
    (scripts / "finalize_svg.py").write_text(textwrap.dedent("""
        import os, pathlib, sys
        ws = pathlib.Path(sys.argv[1])
        out = ws / "svg_final"
        out.mkdir(parents=True, exist_ok=True)
        names = sorted((ws / "svg_output").glob("*.svg"))
        for n in names:
            (out / n.name).write_text(n.read_text())
        print("[OK] finalize done")
    """))


def make_deck(server, tmp_path, pages=1, pid_name="dify"):
    pid = call(server, "ppt_project_init", {"name": pid_name})["project_id"]
    for i in range(1, pages + 1):
        call(server, "ppt_write_page", {"project_id": pid, "page_number": i,
                                        "name": f"p{i}", "svg": PASSING_SVG})
    call(server, "ppt_check", {"project_id": pid})  # fake checker writes no report; export gate reads fixture
    return pid


def write_passing_report(projects_root, pid):
    vdir = Path(projects_root) / pid / "validation"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "svg_quality_report.json").write_text(json.dumps({
        "summary": {"total": 1, "passed": 1, "warnings": 0, "errors": 0},
        "files": [{"file": "01_p1.svg", "errors": [], "warnings": []}],
    }))


@pytest.fixture
def env(tmp_path):
    root = tmp_path / "pptm"
    scripts = root / "skills" / "ppt-master"
    fake_scripts(scripts)
    (root / "projects").mkdir(parents=True)
    cfg = Config(
        state_db=tmp_path / "s.sqlite3",
        vector_dir=tmp_path / "v",
        decider_enabled=False,
        ppt_scripts_root=scripts,
        ppt_projects_root=root / "projects",
        ppt_exports_url_base="http://test/exports",
    )
    srv = build_server(cfg)
    return {"server": srv, "cfg": cfg, "root": root}


# ---------------------------------------------------------------- routes (D07–D10)

def _page(app, url):
    client = _client(app)
    return client.get(url)


def _client(app):
    from starlette.testclient import TestClient

    return TestClient(app)


def build_app(cfg):
    from starlette.applications import Starlette
    from starlette.routing import Route

    from agentic_rag_mcp.ppt.completion import (
        artifact_exists,
        render_completion_page,
        resolve_slide,
    )
    from agentic_rag_mcp.ppt.errors import InvalidInput
    from agentic_rag_mcp.ppt.http_exports import PPTX_CONTENT_TYPE

    async def decks_page(request):
        from starlette.responses import HTMLResponse, Response

        try:
            if not artifact_exists(cfg, request.path_params["project_id"],
                                    request.path_params["stem"]):
                return Response("not found", status_code=404)
            return HTMLResponse(render_completion_page(
                cfg, request.path_params["project_id"], request.path_params["stem"]))
        except InvalidInput:
            return Response("bad request", status_code=400)

    async def slide(request):
        from starlette.responses import FileResponse, Response

        try:
            path = resolve_slide(cfg, request.path_params["project_id"],
                                 request.path_params["stem"],
                                 request.path_params["filename"])
        except InvalidInput:
            return Response("bad request", status_code=400)
        except FileNotFoundError:
            return Response("not found", status_code=404)
        return FileResponse(path, media_type="image/svg+xml")

    return Starlette(routes=[
        Route("/decks/{project_id}/{stem}/", decks_page, methods=["GET"]),
        Route("/decks/{project_id}/{stem}/slides/{filename}", slide, methods=["GET"]),
    ]), PPTX_CONTENT_TYPE


def test_completion_page_served(env):
    pid = make_deck(env["server"], None)
    write_passing_report(env["root"] / "projects", pid)
    exported = call(env["server"], "ppt_export", {"project_id": pid})
    app, _ = build_app(env["cfg"])
    resp = _page(app, exported["page_url"].replace("http://test", ""))
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert exported["url"] in resp.text  # download control → frozen URL
    assert "revise page" in resp.text.lower()  # edit path
    assert exported["url"] == f"http://test/exports/{pid}/deck_120000.pptx"  # D01 frozen


def test_slide_asset_content_type(env):
    pid = make_deck(env["server"], None)
    write_passing_report(env["root"] / "projects", pid)
    exported = call(env["server"], "ppt_export", {"project_id": pid})
    app, _ = build_app(env["cfg"])
    resp = _page(app, exported["page_url"].replace("http://test", "") + "slides/01_p1.svg")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/svg+xml"  # D09
    assert b"svg" in resp.content


def test_unknown_artifact_404(env):
    pid = make_deck(env["server"], None)
    app, _ = build_app(env["cfg"])
    assert _page(app, f"/decks/{pid}/nope_deck/").status_code == 404  # D07
    assert _page(app, "/decks/ghost/deck_1/").status_code == 404


def test_traversal_and_malformed_rejected(env):
    pid = make_deck(env["server"], None)
    app, _ = build_app(env["cfg"])
    assert _page(app, f"/decks/{pid}/deck_1/slides/..%2F..%2Fetc.svg").status_code in (400, 404)  # D08
    assert _page(app, f"/decks/{pid}/deck_1/slides/%2Fabs.svg").status_code in (400, 404)
    assert _page(app, f"/decks/{pid}/deck_1/slides/nosvg.txt").status_code in (400, 404)
    assert _page(app, "/decks/bad%20id/deck_1/").status_code == 400  # D10


# ---------------------------------------------------------------- degraded (D05)

def test_degraded_artifact_renders_honestly(env):
    pid = make_deck(env["server"], None)
    write_passing_report(env["root"] / "projects", pid)
    exported = call(env["server"], "ppt_export", {"project_id": pid})
    preview_dir = (env["root"] / "projects" / pid / "previews" / "deck_120000")
    for f in preview_dir.glob("*.svg"):
        f.unlink()
    (preview_dir / ".degraded").write_text("forced\n")
    app, _ = build_app(env["cfg"])
    resp = _page(app, exported["page_url"].replace("http://test", ""))
    assert resp.status_code == 200
    assert "preview unavailable" in resp.text.lower()
    assert exported["url"] in resp.text  # download intact
    assert "<img" not in resp.text


# ---------------------------------------------------------------- tool contract (D01, D12)

def test_export_result_additive_field(env):
    pid = make_deck(env["server"], None)
    write_passing_report(env["root"] / "projects", pid)
    exported = call(env["server"], "ppt_export", {"project_id": pid})
    assert set(exported) == {"file", "url", "page_url"}  # D01: exactly additive
    assert exported["page_url"] == f"http://test/decks/{pid}/deck_120000/"


def test_export_error_envelope_unchanged(env):
    result = call(env["server"], "ppt_export", {"project_id": "ghost"})
    assert result["error"]["code"] == "PPT_INVALID_PROJECT"  # D12: no regression
