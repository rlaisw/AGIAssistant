"""Integration: completion-page snapshot against the real toolchain (spec 010).

Matrix refs: D01–D04, D17. Skipped when the ppt-master install is absent.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from agentic_rag_mcp.config import Config
from agentic_rag_mcp.ppt import bridge, completion
from agentic_rag_mcp.ppt.errors import PptError

PPT_MASTER = Path("/kilocode/AGIAssistant/ppt-master")
SCRIPTS = PPT_MASTER / "skills" / "ppt-master"
PPT_PY = PPT_MASTER / ".venv" / "bin" / "python"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "ppt"

pytestmark = pytest.mark.skipif(
    not (SCRIPTS / "scripts" / "project_manager.py").is_file() or not PPT_PY.is_file(),
    reason="ppt-master clone or its venv not installed",
)


@pytest.fixture
def cfg(tmp_path):
    c = Config(
        state_db=tmp_path / "s.sqlite3",
        vector_dir=tmp_path / "v",
        decider_enabled=False,
        ppt_scripts_root=SCRIPTS,
        ppt_projects_root=tmp_path / "projects",
        ppt_python=str(PPT_PY),
        ppt_exports_url_base="http://test/exports",
        ppt_script_timeout_s=300.0,
    )
    c._created: list[str] = []
    orig_init = bridge.project_init

    def tracking_init(config, name):
        result = orig_init(config, name)
        config._created.append(result["project_id"])
        return result

    bridge.project_init = tracking_init
    yield c
    bridge.project_init = orig_init
    import shutil

    for pid in c._created:
        shutil.rmtree(bridge.projects_root(c) / pid, ignore_errors=True)


def root(cfg):
    return bridge.projects_root(cfg)


def test_export_snapshots_previews_and_page_url(cfg):  # D01, D02
    pid = bridge.project_init(cfg, "decktest")["project_id"]
    bridge.write_page(cfg, pid, 1, "one",
                      (FIXTURES / "passing.svg").read_text())
    exported = bridge.export_pptx(cfg, pid)
    stem = Path(exported["file"]).stem
    assert exported["page_url"] == f"http://test/decks/{pid}/{stem}/"
    dest = root(cfg) / pid / "previews" / stem
    slides = sorted(dest.glob("*.svg"))
    assert len(slides) == 1 and slides[0].suffix == ".svg"
    html = completion.render_completion_page(cfg, pid, stem)
    assert exported["url"] in html and "revise page" in html.lower()


def test_two_page_ordering(cfg):  # D17
    pid = bridge.project_init(cfg, "ordertest")["project_id"]
    bridge.write_page(cfg, pid, 1, "one",
                      (FIXTURES / "passing.svg").read_text())
    bridge.write_page(cfg, pid, 2, "two",
                      (FIXTURES / "passing2.svg").read_text())
    exported = bridge.export_pptx(cfg, pid)
    dest = root(cfg) / pid / "previews" / Path(exported["file"]).stem
    names = [p.name for p in sorted(dest.glob("*.svg"))]
    assert names == ["01_one.svg", "02_two.svg"]
    html = completion.render_completion_page(cfg, pid, Path(exported["file"]).stem)
    assert html.count("<img") == 2
    assert html.index("slides/01_one.svg") < html.index("slides/02_two.svg")


def test_reexport_isolation(cfg):  # D03, FR-007
    pid = bridge.project_init(cfg, "revtest2")["project_id"]
    svg = (FIXTURES / "passing.svg").read_text()
    bridge.write_page(cfg, pid, 1, "one", svg)
    first = bridge.export_pptx(cfg, pid)
    first_stem = Path(first["file"]).stem

    bridge.write_page(cfg, pid, 1, "one",
                      svg.replace("Fixture Deck", "Revised Deck"))
    second = bridge.export_pptx(cfg, pid)
    second_stem = Path(second["file"]).stem
    assert first_stem != second_stem

    first_dir = root(cfg) / pid / "previews" / first_stem
    first_snapshot = sorted(first_dir.glob("*.svg"))[0].read_text()
    assert "Fixture Deck" in first_snapshot  # old artifact's snapshot unchanged (D03)
    first_html = completion.render_completion_page(cfg, pid, first_stem)
    assert "slides/01_one.svg" in first_html  # page still serves its own snapshot
    assert (root(cfg) / pid / "exports" / f"{first_stem}.pptx").is_file()
    assert second["url"].endswith(f"{second_stem}.pptx")


def test_degraded_export_still_delivers(cfg, monkeypatch):  # D04, FR-008
    pid = bridge.project_init(cfg, "failprev")["project_id"]
    bridge.write_page(cfg, pid, 1, "one",
                      (FIXTURES / "passing.svg").read_text())

    original_run = bridge._run_allow_failure

    def selective_boom(cfg_, script, args):
        if script == "finalize_svg.py":
            raise PptError("forced finalize failure")
        return original_run(cfg_, script, args)

    monkeypatch.setattr(bridge, "_run_allow_failure", selective_boom)
    exported = bridge.export_pptx(cfg, pid)
    stem = Path(exported["file"]).stem
    assert (root(cfg) / pid / "exports" / f"{stem}.pptx").is_file()  # file delivered
    assert exported["page_url"]  # page still returned
    marker = root(cfg) / pid / "previews" / stem / ".degraded"
    assert marker.is_file()
    html = completion.render_completion_page(cfg, pid, stem)
    assert "preview unavailable" in html.lower()
    assert exported["url"] in html  # download intact
