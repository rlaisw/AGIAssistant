"""Integration: live chart call, infographic serving, deck self-containment (spec 012).

Network-gated: the live chart call requires outbound internet; the deck test
runs against the real toolchain. Matrix refs A06, A12.
"""

from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path

import httpx
import pytest

from agentic_rag_mcp.config import Config, load_config
from agentic_rag_mcp.antv import charts, infographic
from agentic_rag_mcp.ppt import bridge

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "antv"
PPT_MASTER = Path("/kilocode/AGIAssistant/ppt-master")
SCRIPTS = PPT_MASTER / "skills" / "ppt-master"
PPT_PY = PPT_MASTER / ".venv" / "bin" / "python"

HAS_TOOLCHAIN = (SCRIPTS / "scripts" / "project_manager.py").is_file() and PPT_PY.is_file()


def _has_network() -> bool:
    try:
        httpx.get("https://antv-studio.alipay.com", timeout=5)
        return True
    except httpx.HTTPError:
        return False


DECK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
    'font-family="Segoe UI, sans-serif">'
    '<rect id="bg" data-pptx-role="background" x="0" y="0" width="1280" height="720" fill="#FAFAFA"/>'
    '<g id="t" data-pptx-bounds="64 64 1152 300">'
    '<text x="64" y="100" font-size="44" font-weight="bold" fill="#212121">Chart Deck</text>'
    '<image href="https://mdn.alipayobjects.com/afts/img/70B7RLKFRtAAAAAAQpAAAAgAoEACAQFr/original" '
    'x="64" y="140" width="640" height="360"/>'
    "</g></svg>"
)


@pytest.fixture
def cfg(tmp_path):
    return Config(
        state_db=tmp_path / "s.sqlite3",
        vector_dir=tmp_path / "v",
        decider_enabled=False,
        antv_infographic_served_root=tmp_path / "infographics",
    )


def test_live_chart_call_returns_serving_image(cfg):
    if not _has_network():
        pytest.skip("no outbound internet to the chart service")
    result = charts.generate_chart(
        cfg, "bar",
        [{"category": "Q1", "value": 30}, {"category": "Q2", "value": 55},
         {"category": "Q3", "value": 80}],
        "Live smoke chart",
    )
    assert result["chart_type"] == "bar"
    img = httpx.get(result["image_url"], timeout=60, follow_redirects=True)
    assert img.status_code == 200
    assert img.headers.get("Content-Type", "").startswith("image/")
    assert len(img.content) > 1000


def test_infographic_route_serves_syntax(cfg):
    syntax = "infographic list-row-simple-horizontal-arrow\ndata\n  lists\n    - label Step 1\n      desc Start\n"
    created = infographic.create_infographic(cfg, syntax)
    page = infographic.render_infographic_page(cfg, created["id"])
    assert "cdn.jsdelivr.net" in page
    assert "render" in page.lower()
    stored = (cfg.antv_infographic_served_root / f"{created['id']}.txt").read_text()
    assert stored == syntax


@pytest.mark.skipif(not HAS_TOOLCHAIN, reason="ppt-master clone or its venv not installed")
@pytest.mark.skipif(not _has_network(), reason="no outbound internet for the image fetch")
def test_deck_with_remote_chart_exports_selfcontained(tmp_path):
    deck_cfg = Config(
        state_db=tmp_path / "s.sqlite3",
        vector_dir=tmp_path / "v",
        decider_enabled=False,
        ppt_scripts_root=SCRIPTS,
        ppt_projects_root=tmp_path / "projects",
        ppt_python=str(PPT_PY),
        ppt_exports_url_base="http://test/exports",
        ppt_script_timeout_s=300.0,
    )
    # fresh chart from the live service, then embed it like the agent would
    chart = charts.generate_chart(
        deck_cfg, "bar",
        [{"category": "Q1", "value": 30}, {"category": "Q2", "value": 55}],
        "Chart Deck",
    )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
        'font-family="Segoe UI, sans-serif" data-pptx-page-role="content">'
        '<rect id="bg" data-pptx-role="background" x="0" y="0" width="1280" height="720" fill="#FAFAFA"/>'
        f'<image href="{chart["image_url"]}" x="64" y="64" width="640" height="360"/>'
        "</svg>"
    )
    pid = bridge.project_init(deck_cfg, "chartdeck")["project_id"]
    persisted = bridge.write_page(deck_cfg, pid, 1, "chart", svg)

    # A10 (real fetch): the persisted page holds only data: URIs
    page = (bridge.projects_root(deck_cfg) / pid / persisted["file"]).read_text()
    assert "data:image/" in page
    assert 'href="https' not in page  # no remote hrefs remain

    # A12: the exported deck carries the image bytes (no hotlink)
    bridge.check(deck_cfg, pid)
    exported = bridge.export_pptx(deck_cfg, pid)
    artifact = bridge.projects_root(deck_cfg) / pid / exported["file"]
    with zipfile.ZipFile(artifact) as z:
        media = [n for n in z.namelist() if n.startswith("ppt/media/")]
        assert media, "exported deck must contain embedded media"
        slide_xml = z.read("ppt/slides/slide1.xml").decode("utf-8", errors="ignore")
        assert "r:embed" in slide_xml  # referenced, not hotlinked

    import shutil

    shutil.rmtree(bridge.projects_root(deck_cfg) / pid, ignore_errors=True)
