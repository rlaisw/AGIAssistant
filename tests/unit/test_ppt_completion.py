"""Unit: completion-page snapshot, rendering, and slide resolution (spec 010).

Hermetic: fake scripts + temp dirs. Matrix refs: D02, D05, D06.
"""

from __future__ import annotations

import json
import textwrap

import pytest

from agentic_rag_mcp.config import Config
from agentic_rag_mcp.ppt import completion
from agentic_rag_mcp.ppt.errors import InvalidInput

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
       '<text x="64" y="100" font-size="24">slide</text></svg>')


def make_cfg(tmp_path):
    root = tmp_path / "pptm"
    cfg = Config(
        state_db=tmp_path / "s.sqlite3",
        vector_dir=tmp_path / "v",
        decider_enabled=False,
        ppt_scripts_root=root / "skills" / "ppt-master",
        ppt_projects_root=root / "projects",
        ppt_exports_url_base="http://test/exports",
    )
    return cfg


def fake_finalize(scripts_root, slide_names=("01_a.svg",)):
    scripts = scripts_root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    listing = "".join(f'  print("  wrote {n}")\n' for n in slide_names)
    (scripts / "finalize_svg.py").write_text(
        "import sys, pathlib\n"
        "ws = pathlib.Path(sys.argv[1])\n"
        "out = ws / 'svg_final'\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        + "".join(f"(out / '{n}').write_text('<svg/>')\n" for n in slide_names)
        + "print('[OK] done')\n"
    )


def project(cfg, pid="proj_20260101", pages=1):
    ws = completion.projects_root(cfg) / pid
    (ws / "svg_output").mkdir(parents=True, exist_ok=True)
    (ws / "exports").mkdir(parents=True, exist_ok=True)
    for i in range(1, pages + 1):
        (ws / "svg_output" / f"{i:02d}_p.svg").write_text(SVG)
    (ws / "exports" / "deck_1.pptx").write_bytes(b"PK")
    return ws


# ---------------------------------------------------------------- snapshot (D02)

def test_snapshot_copies_ordered_slides(tmp_path):
    cfg = make_cfg(tmp_path)
    fake_finalize(cfg.ppt_scripts_root, ["02_b.svg", "01_a.svg"])
    project(cfg)
    ready = completion.snapshot_previews(cfg, "proj_20260101", "deck_1")
    dest = completion.projects_root(cfg) / "proj_20260101" / "previews" / "deck_1"
    assert ready is True
    assert [p.name for p in sorted(dest.glob("*.svg"))] == ["01_a.svg", "02_b.svg"]


def test_snapshot_write_once(tmp_path):
    cfg = make_cfg(tmp_path)
    fake_finalize(cfg.ppt_scripts_root, ["01_a.svg"])
    ws = project(cfg)
    dest = ws / "previews" / "deck_1"
    dest.mkdir(parents=True)
    (dest / "01_a.svg").write_text("<svg>original</svg>")
    ready = completion.snapshot_previews(cfg, "proj_20260101", "deck_1")
    assert ready is True
    assert (dest / "01_a.svg").read_text() == "<svg>original</svg>"  # never overwritten


def test_snapshot_finalize_failure_degrades(tmp_path):  # D04 shape
    cfg = make_cfg(tmp_path)
    scripts = cfg.ppt_scripts_root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "finalize_svg.py").write_text("import sys; sys.exit(1)\n")
    project(cfg)
    ready = completion.snapshot_previews(cfg, "proj_20260101", "deck_1")
    dest = completion.projects_root(cfg) / "proj_20260101" / "previews" / "deck_1"
    assert ready is False
    assert (dest / ".degraded").is_file()


def test_snapshot_empty_output_degrades(tmp_path):
    cfg = make_cfg(tmp_path)
    fake_finalize(cfg.ppt_scripts_root, [])
    project(cfg)
    ready = completion.snapshot_previews(cfg, "proj_20260101", "deck_1")
    assert ready is False
    dest = completion.projects_root(cfg) / "proj_20260101" / "previews" / "deck_1"
    assert (dest / ".degraded").is_file()


# ---------------------------------------------------------------- rendering (D06)

def test_render_page_contains_download_edit_slides(tmp_path):
    cfg = make_cfg(tmp_path)
    ws = project(cfg, pages=2)
    dest = ws / "previews" / "deck_1"
    dest.mkdir(parents=True)
    (dest / "01_p.svg").write_text(SVG)
    (dest / "02_p.svg").write_text(SVG)
    html = completion.render_completion_page(cfg, "proj_20260101", "deck_1")
    assert "http://test/exports/proj_20260101/deck_1.pptx" in html  # frozen URL family
    assert "ask in chat" in html.lower() or "revise page" in html.lower()  # edit path
    assert html.count("<img") == 2
    assert "slides/01_p.svg" in html and "slides/02_p.svg" in html
    assert 'name="viewport"' in html  # responsive (T008)


def test_render_degraded_page_honest(tmp_path):  # D05
    cfg = make_cfg(tmp_path)
    ws = project(cfg)
    dest = ws / "previews" / "deck_1"
    dest.mkdir(parents=True)
    (dest / ".degraded").write_text("failed\n")
    html = completion.render_completion_page(cfg, "proj_20260101", "deck_1")
    assert "preview unavailable" in html.lower()
    assert "http://test/exports/proj_20260101/deck_1.pptx" in html  # download intact
    assert "<img" not in html  # no fabricated slides


# ---------------------------------------------------------------- slide resolution (D08)

def test_resolve_slide_valid(tmp_path):
    cfg = make_cfg(tmp_path)
    ws = project(cfg)
    dest = ws / "previews" / "deck_1"
    dest.mkdir(parents=True)
    (dest / "01_p.svg").write_text(SVG)
    path = completion.resolve_slide(cfg, "proj_20260101", "deck_1", "01_p.svg")
    assert path.name == "01_p.svg"


def test_resolve_slide_traversal_rejected(tmp_path):
    cfg = make_cfg(tmp_path)
    project(cfg)
    for bad in ("../x.svg", "..%2F", "/abs.svg", "sub/dir/a.svg", "no_svg.txt"):
        with pytest.raises((InvalidInput, FileNotFoundError)):
            completion.resolve_slide(cfg, "proj_20260101", "deck_1", bad)


def test_resolve_slide_unknown_project(tmp_path):
    cfg = make_cfg(tmp_path)
    project(cfg)
    with pytest.raises(FileNotFoundError):
        completion.resolve_slide(cfg, "ghost", "deck_1", "01_p.svg")
