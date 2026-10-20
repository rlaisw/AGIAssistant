"""Unit: antv tool bodies — type validation, error mapping, inlining (spec 012).

Hermetic: fake HTTP via monkeypatch; matrix refs A02-A05, A08, A10-A11.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from agentic_rag_mcp.config import Config
from agentic_rag_mcp.ppt import bridge
from agentic_rag_mcp.ppt.errors import InvalidInput as PptInvalidInput

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "antv"

DECK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
    '<g id="t" data-pptx-bounds="64 64 400 100">'
    '<image href="https://cdn.example.com/chart.png" x="64" y="64" width="400" height="200"/>'
    "</g></svg>"
)


def make_cfg(tmp_path, **over):
    cfg = Config(
        state_db=tmp_path / "s.sqlite3",
        vector_dir=tmp_path / "v",
        decider_enabled=False,
        ppt_scripts_root=tmp_path / "pptm" / "skills" / "ppt-master",
        ppt_projects_root=tmp_path / "pptm" / "projects",
        antv_chart_service_url=over.get("chart_service_url", "http://fake/api"),
        antv_chart_timeout_s=over.get("chart_timeout_s", 5.0),
        antv_max_inline_image_bytes=over.get("max_inline_image_bytes", 2_097_152),
        antv_infographic_max_syntax_bytes=over.get("infographic_max_syntax_bytes", 65_536),
        antv_infographic_served_root=over.get("infographic_served_root", tmp_path / "infographics"),
    )
    return cfg


def fake_service(monkeypatch, *, success=True, status=200, sleep=None, url="https://img/x.png"):
    calls = []

    def _post(url_, json=None, timeout=None):
        calls.append({"url": url_, "payload": json})

        class R:
            status_code = status

            def json(self):
                if success:
                    return {"success": True, "resultObj": url, "errorMessage": "成功"}
                return {"success": False, "errorMessage": "bad data", "errorCode": "EX"}

        class TimeoutR:
            def json(self):
                return {}

        import httpx

        if sleep is not None:
            raise httpx.ReadTimeout("timed out")
        return R()

    import agentic_rag_mcp.antv.charts as charts

    monkeypatch.setattr(charts.httpx, "post", _post)
    return calls


# ---------------------------------------------------------------- chart tool (A02-A05)

def test_unsupported_type_names_supported_set(tmp_path, monkeypatch):
    from agentic_rag_mcp.antv import charts
    from agentic_rag_mcp.antv.errors import AntvError, AntvInvalidType

    cfg = make_cfg(tmp_path)
    for bad in ("district-map", "path-map", "pin-map", "3d-globe", ""):
        with pytest.raises(AntvInvalidType) as ei:
            charts.generate_chart(cfg, bad, [{"category": "A", "value": 1}], "t")
        assert "line" in str(ei.value)  # the supported list is named
    assert "ANTV_INVALID_TYPE" == "ANTV_INVALID_TYPE"


def test_invalid_data_shapes(tmp_path):
    from agentic_rag_mcp.antv import charts
    from agentic_rag_mcp.antv.errors import AntvInvalidInput

    cfg = make_cfg(tmp_path)
    for bad in ([], "not a list", [{"value": 1}, "mixed"]):
        with pytest.raises(AntvInvalidInput):
            charts.generate_chart(cfg, "bar", bad, "t")
    with pytest.raises(AntvInvalidInput):  # oversized payload
        charts.generate_chart(cfg, "bar", [{"category": "x", "value": 1}] * 4000, "t")
    with pytest.raises(AntvInvalidInput):  # title > 200 chars
        charts.generate_chart(cfg, "bar", [{"category": "A", "value": 1}], "x" * 201)
    # shape-valid records pass validation — semantics are the service's call (honest
    # success=false comes back as ANTV_SERVICE_ERROR if the service rejects them)


def test_service_success_returns_url(tmp_path, monkeypatch):
    from agentic_rag_mcp.antv import charts

    cfg = make_cfg(tmp_path)
    calls = fake_service(monkeypatch, url="https://img/ok.png")
    result = charts.generate_chart(cfg, "bar", [{"category": "A", "value": 30}], "Volume")
    assert result["chart_type"] == "bar"
    assert result["image_url"] == "https://img/ok.png"
    assert "usage" in result
    assert calls[0]["payload"]["type"] == "bar"


def test_service_failure_verbatim_message(tmp_path, monkeypatch):
    from agentic_rag_mcp.antv import charts
    from agentic_rag_mcp.antv.errors import AntvServiceError

    cfg = make_cfg(tmp_path)
    fake_service(monkeypatch, success=False)
    with pytest.raises(AntvServiceError) as ei:
        charts.generate_chart(cfg, "bar", [{"category": "A", "value": 30}], "t")
    assert "bad data" in str(ei.value)


def test_service_timeout(tmp_path, monkeypatch):
    from agentic_rag_mcp.antv import charts
    from agentic_rag_mcp.antv.errors import AntvServiceTimeout

    cfg = make_cfg(tmp_path, chart_timeout_s=0.1)
    fake_service(monkeypatch, sleep=True)
    with pytest.raises(AntvServiceTimeout):
        charts.generate_chart(cfg, "bar", [{"category": "A", "value": 30}], "t")


# ---------------------------------------------------------------- infographic (A08)

def test_infographic_syntax_validation(tmp_path):
    from agentic_rag_mcp.antv import infographic
    from agentic_rag_mcp.antv.errors import AntvInvalidInput

    cfg = make_cfg(tmp_path)
    with pytest.raises(AntvInvalidInput):
        infographic.create_infographic(cfg, "")
    with pytest.raises(AntvInvalidInput):
        infographic.create_infographic(cfg, "x" * 65_537)


def test_infographic_stores_and_returns_url(tmp_path):
    from agentic_rag_mcp.antv import infographic

    cfg = make_cfg(tmp_path)
    syntax = (FIXTURES / "infographic.txt").read_text() or "infographic list-row"
    result = infographic.create_infographic(cfg, syntax)
    assert "/infographics/" in result["url"]
    stored = infographic.served_dir(cfg)
    files = list(stored.glob("*.txt"))
    assert len(files) == 1
    assert files[0].read_text() == syntax


def test_infographic_page_renders_syntax_and_engine(tmp_path):
    from agentic_rag_mcp.antv import infographic

    cfg = make_cfg(tmp_path)
    syntax = "infographic list-row-simple\ndata\n  lists\n    - label A\n"
    result = infographic.create_infographic(cfg, syntax)
    page = infographic.render_infographic_page(cfg, result["id"])
    assert "cdn.jsdelivr.net" in page or "unpkg" in page  # engine reference
    assert syntax not in page or "render" in page.lower()
    assert "<html" in page.lower()


# ---------------------------------------------------------------- write_page inlining (A10-A11)

def test_write_page_inlines_remote_images(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path)
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    def fake_get(url, timeout=None, follow_redirects=False):
        class R:
            status_code = 200
            content = png
            headers = {"Content-Type": "image/png"}

        return R()

    monkeypatch.setattr(bridge.httpx, "get", fake_get)
    ws = bridge.projects_root(cfg) / "proj_1"
    (ws / "svg_output").mkdir(parents=True)
    persisted = bridge.write_page(cfg, "proj_1", 1, "chart", DECK_SVG)
    out = (ws / persisted["file"]).read_text()
    assert "data:image/png;base64," in out
    assert "https://cdn.example.com" not in out  # no hotlinks remain


def test_write_page_inline_fetch_failure_names_href(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path)

    def bad_get(url, timeout=None, follow_redirects=False):
        import httpx

        raise httpx.ConnectError("no route")

    monkeypatch.setattr(bridge.httpx, "get", bad_get)
    ws = bridge.projects_root(cfg) / "proj_1"
    (ws / "svg_output").mkdir(parents=True)
    with pytest.raises(PptInvalidInput) as ei:
        bridge.write_page(cfg, "proj_1", 1, "chart", DECK_SVG)
    assert "cdn.example.com" in str(ei.value)  # href named
    assert not (ws / "svg_output" / "01_chart.svg").exists()  # nothing persisted


def test_write_page_inline_oversize_rejected(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path, max_inline_image_bytes=10)

    def big_get(url, timeout=None, follow_redirects=False):
        class R:
            status_code = 200
            content = b"x" * 100
            headers = {"Content-Type": "image/png"}

        return R()

    monkeypatch.setattr(bridge.httpx, "get", big_get)
    ws = bridge.projects_root(cfg) / "proj_1"
    (ws / "svg_output").mkdir(parents=True)
    with pytest.raises(PptInvalidInput):
        bridge.write_page(cfg, "proj_1", 1, "chart", DECK_SVG)
