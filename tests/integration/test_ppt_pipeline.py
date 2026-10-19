"""Integration: real ppt-master toolchain round-trips on temp projects (spec 009).

Skipped when the ppt-master install (clone + venv) is absent — the host or a
CI image with the clone runs these; matrix refs T01, T04, T05, T07, T13, T14,
T17, T18, T20.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from agentic_rag_mcp.config import Config
from agentic_rag_mcp.ppt import bridge
from agentic_rag_mcp.ppt.errors import ExportBlocked, MissingIcon

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
    for pid in c._created:  # keep the real clone's projects/ clean
        import shutil

        shutil.rmtree(bridge.projects_root(c) / pid, ignore_errors=True)


def root(cfg):
    return bridge.projects_root(cfg)


def test_full_pipeline_passing(cfg):
    result = bridge.project_init(cfg, "difytest")
    pid = result["project_id"]
    assert (root(cfg) / pid).is_dir()  # T01
    assert pid.startswith("difytest_")

    icons = bridge.icon_sync(cfg, pid, ["tabler-outline/star", "simple-icons/dify"])
    assert icons["synced"] == ["tabler-outline/star", "simple-icons/dify"]  # T04

    svg = (FIXTURES / "passing.svg").read_text()
    written = bridge.write_page(cfg, pid, 1, "overview", svg)
    assert (root(cfg) / pid / written["file"]).is_file()  # T07

    check = bridge.check(cfg, pid)
    assert check["passing"] is True, check["details"]  # T13

    exported = bridge.export_pptx(cfg, pid)
    artifact = root(cfg) / pid / exported["file"]
    assert artifact.is_file()
    assert exported["url"].endswith(artifact.name)
    with zipfile.ZipFile(artifact) as z:  # T17: native editable content
        slide_xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "<a:t>" in slide_xml, "exported slide must contain native text runs"


def test_failing_page_blocks_export(cfg):
    pid = bridge.project_init(cfg, "failtest")["project_id"]
    svg = (FIXTURES / "failing.svg").read_text()
    bridge.write_page(cfg, pid, 1, "broken", svg)

    check = bridge.check(cfg, pid)  # T14
    assert check["passing"] is False
    assert check["blocking_errors"] >= 1
    assert any("exceeds" in d for d in check["details"])

    with pytest.raises(ExportBlocked) as ei:  # T18
        bridge.export_pptx(cfg, pid)
    assert "overflow" in str(ei.value).lower() or "exceeds" in str(ei.value)
    assert not list((root(cfg) / pid / "exports").glob("*.pptx"))


def test_missing_icon_real(cfg):
    pid = bridge.project_init(cfg, "icontest")["project_id"]
    with pytest.raises(MissingIcon) as ei:  # T05
        bridge.icon_sync(cfg, pid, ["tabler-outline/definitely-not-an-icon"])
    assert "definitely-not-an-icon" in str(ei.value)


def test_revision_reexport_keeps_old_artifact(cfg):
    pid = bridge.project_init(cfg, "revtest")["project_id"]
    svg = (FIXTURES / "passing.svg").read_text()
    bridge.write_page(cfg, pid, 1, "one", svg)
    bridge.export_pptx(cfg, pid)
    first = sorted((root(cfg) / pid / "exports").glob("*.pptx"))

    bridge.write_page(cfg, pid, 1, "one", svg.replace("Fixture Deck", "Revised Deck"))
    bridge.export_pptx(cfg, pid)  # T20
    second = sorted((root(cfg) / pid / "exports").glob("*.pptx"))
    assert len(second) >= len(first)
    assert all(p.is_file() for p in first)  # old link target still exists
