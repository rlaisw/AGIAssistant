"""Unit: ppt bridge — error envelope, subprocess failure modes, sanitization (spec 009).

Hermetic: fake scripts and temp dirs only; no ppt-master install needed.
Matrix refs (contracts/ppt-tools.md): T03, T08-T12, T16, T23, T24.
"""

from __future__ import annotations

import json
import textwrap

import pytest

from agentic_rag_mcp.config import Config
from agentic_rag_mcp.ppt import bridge
from agentic_rag_mcp.ppt.errors import (
    ExportBlocked,
    InvalidInput,
    InvalidProject,
    MissingIcon,
    PptError,
    ScriptFailure,
    ScriptTimeout,
    WorkspaceError,
    envelope,
)

CODES = {
    InvalidProject: "PPT_INVALID_PROJECT",
    InvalidInput: "PPT_INVALID_INPUT",
    MissingIcon: "PPT_MISSING_ICON",
    ScriptTimeout: "PPT_SCRIPT_TIMEOUT",
    ScriptFailure: "PPT_SCRIPT_FAILED",
    ExportBlocked: "PPT_EXPORT_BLOCKED",
    WorkspaceError: "PPT_WORKSPACE_ERROR",
}

PASSING_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
    '<g id="t" data-pptx-bounds="64 64 400 100"><text x="64" y="100" '
    'font-size="24" fill="#212121">Hello</text></g></svg>'
)


def make_cfg(tmp_path, **over):
    # layout mirrors the real toolchain: <root>/skills/ppt-master -> projects at <root>/projects
    root = tmp_path / "pptm"
    cfg = Config(
        state_db=tmp_path / "s.sqlite3",
        vector_dir=tmp_path / "v",
        decider_enabled=False,
        ppt_scripts_root=over.get("scripts_root", root / "skills" / "ppt-master"),
        ppt_projects_root=root / "projects",
        ppt_script_timeout_s=over.get("script_timeout_s", 30.0),
        ppt_max_pages=over.get("max_pages", 5),
    )
    return cfg


def real_root(cfg):
    from agentic_rag_mcp.ppt.bridge import projects_root
    return projects_root(cfg)


def write_script(scripts_root: str, name: str, body: str) -> None:
    import sys
    from pathlib import Path

    path = Path(scripts_root) / "scripts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body))
    path.chmod(0o755)
    assert sys.executable


# ---------------------------------------------------------------- envelope (T23)

@pytest.mark.parametrize("exc_class,expected", list(CODES.items()))
def test_envelope_shape_every_code(exc_class, expected):
    exc = exc_class("boom")
    env = envelope(exc)
    assert set(env) == {"error"}
    assert set(env["error"]) == {"code", "message", "hint"}
    assert env["error"]["code"] == expected
    assert env["error"]["message"] == "boom"
    assert env["error"]["hint"]  # non-empty, agent-actionable


def test_envelope_all_codes_covered():
    assert len(CODES) == 7  # the contract's 8 codes minus PPT_CHECK_FAILED (a result, not a raise)


# ---------------------------------------------------------------- subprocess (T16, T24)

def test_run_script_timeout(tmp_path):
    write_script(make_cfg(tmp_path).ppt_scripts_root, "slow.py", """
        import time
        time.sleep(5)
    """)
    cfg = make_cfg(tmp_path, script_timeout_s=0.3)
    with pytest.raises(ScriptTimeout) as ei:
        bridge._run(cfg, "slow.py", [])
    assert envelope(ei.value)["error"]["code"] == "PPT_SCRIPT_TIMEOUT"


def test_run_script_failure_carries_stderr(tmp_path):
    write_script(make_cfg(tmp_path).ppt_scripts_root, "boom.py", """
        import sys
        sys.stderr.write("ValueError: bad thing happened\\n")
        sys.exit(1)
    """)
    cfg = make_cfg(tmp_path)
    with pytest.raises(ScriptFailure) as ei:
        bridge._run(cfg, "boom.py", [])
    env = envelope(ei.value)
    assert env["error"]["code"] == "PPT_SCRIPT_FAILED"
    assert "bad thing happened" in env["error"]["message"]  # verbatim stderr (T24)


def test_run_script_missing_scripts_root(tmp_path):
    cfg = make_cfg(tmp_path, scripts_root=tmp_path / "nope")
    with pytest.raises(ScriptFailure):
        bridge._run(cfg, "whatever.py", [])


def test_stderr_truncated_to_2000_chars(tmp_path):
    write_script(make_cfg(tmp_path).ppt_scripts_root, "noisy.py", """
        import sys
        sys.stderr.write("x" * 9000)
        sys.exit(1)
    """)
    cfg = make_cfg(tmp_path)
    with pytest.raises(ScriptFailure) as ei:
        bridge._run(cfg, "noisy.py", [])
    assert len(ei.value.message) <= 2000


# ---------------------------------------------------------------- validation (T02, T06, T09, T12)

def test_project_init_bad_names(tmp_path):
    cfg = make_cfg(tmp_path)
    for bad in ["", "   ", "x" * 65, "bad/name", "../escape", "na me!"]:
        with pytest.raises(InvalidInput):
            bridge.project_init(cfg, bad)


def test_validate_project_unknown(tmp_path):
    cfg = make_cfg(tmp_path)
    real_root(cfg).mkdir(parents=True)
    with pytest.raises(InvalidProject):
        bridge.check(cfg, "nonexistent_project")


def test_validate_project_rejects_traversal(tmp_path):
    cfg = make_cfg(tmp_path)
    real_root(cfg).mkdir(parents=True)
    (real_root(cfg) / "real").mkdir()
    with pytest.raises(InvalidProject):
        bridge.write_page(cfg, "../../etc", 1, "x", PASSING_SVG)


# ---------------------------------------------------------------- sanitize (T08, T10, T11)

@pytest.mark.parametrize("bad", [
    '<svg xmlns="x" viewBox="0 0 1280 720"><script>alert(1)</script></svg>',
    '<svg xmlns="x" viewBox="0 0 1280 720"><foreignObject/></svg>',
    '<svg xmlns="x" viewBox="0 0 1280 720"><style>.a{}</style></svg>',
    '<svg xmlns="x" viewBox="0 0 1280 720"><text class="a">hi</text></svg>',
    '<svg xmlns="x" viewBox="0 0 1280 720" onload="go()"><text>hi</text></svg>',
    '<svg xmlns="x" viewBox="0 0 1280 720"><image href="http://evil/x.png"/></svg>',
])
def test_sanitize_rejects_forbidden(bad):
    with pytest.raises(InvalidInput) as ei:
        bridge.sanitize_svg(bad)
    msg = str(ei.value)
    assert any(k in msg for k in ("script", "foreignObject", "style", "class",
                                  "event", "onload", "href"))


def test_sanitize_rejects_malformed_xml():
    with pytest.raises(InvalidInput):
        bridge.sanitize_svg("<svg xmlns='x' viewBox='0 0 1280 720'><text>unclosed")


def test_sanitize_rejects_wrong_viewbox():
    with pytest.raises(InvalidInput):
        bridge.sanitize_svg('<svg xmlns="x" viewBox="0 0 800 600"/>')
    with pytest.raises(InvalidInput):
        bridge.sanitize_svg('<svg xmlns="x"/>')


def test_sanitize_rejects_oversized():
    filler = "<!-- " + "x" * (300 * 1024) + " -->"
    svg = f'<svg xmlns="x" viewBox="0 0 1280 720">{filler}</svg>'
    with pytest.raises(InvalidInput):
        bridge.sanitize_svg(svg)


def test_sanitize_accepts_valid():
    bridge.sanitize_svg(PASSING_SVG)  # no raise


# ---------------------------------------------------------------- write_page (T07, T09)

def test_write_page_persists_file(tmp_path):
    cfg = make_cfg(tmp_path)
    ws = real_root(cfg) / "proj_20260101"
    (ws / "svg_output").mkdir(parents=True)
    out = bridge.write_page(cfg, "proj_20260101", 2, "overview", PASSING_SVG)
    assert out["file"] == "svg_output/02_overview.svg"
    assert (ws / "svg_output" / "02_overview.svg").read_text() == PASSING_SVG
    assert out["bytes"] == len(PASSING_SVG)


def test_write_page_rejects_bad_name(tmp_path):
    cfg = make_cfg(tmp_path)
    (real_root(cfg) / "proj_20260101" / "svg_output").mkdir(parents=True)
    for bad in ["../x", "a/b", "UPPER", "sp ace", ""]:
        with pytest.raises(InvalidInput):
            bridge.write_page(cfg, "proj_20260101", 1, bad, PASSING_SVG)


def test_write_page_bounds(tmp_path):
    cfg = make_cfg(tmp_path, max_pages=5)
    (real_root(cfg) / "proj_20260101" / "svg_output").mkdir(parents=True)
    for page in (0, 6, -1):
        with pytest.raises(InvalidInput):
            bridge.write_page(cfg, "proj_20260101", page, "x", PASSING_SVG)


# ---------------------------------------------------------------- check parsing (T13, T14)

def test_check_parses_report(tmp_path):
    cfg = make_cfg(tmp_path)
    ws = real_root(cfg) / "proj_20260101"
    (ws / "svg_output").mkdir(parents=True)
    (ws / "validation").mkdir(parents=True)
    (ws / "validation" / "svg_quality_report.json").write_text(json.dumps({
        "summary": {"total": 1, "passed": 0, "warnings": 1, "errors": 2},
        "files": [{"file": "01_a.svg",
                   "errors": ["overflow 10%", "title off-canvas"],
                   "warnings": ["advisory"]}],
    }))
    write_script(make_cfg(tmp_path).ppt_scripts_root, "svg_quality_checker.py", "print('[OK] done')\n")
    pass  # scripts root is make_cfg default
    result = bridge.check(cfg, "proj_20260101")
    assert result["passing"] is False
    assert result["blocking_errors"] == 2
    assert result["warnings"] == 1
    assert "overflow 10%" in " ".join(result["details"])


def test_export_blocked_on_failing_pages(tmp_path):
    cfg = make_cfg(tmp_path)
    ws = real_root(cfg) / "proj_20260101"
    (ws / "svg_output").mkdir(parents=True)
    (ws / "validation").mkdir(parents=True)
    (ws / "validation" / "svg_quality_report.json").write_text(json.dumps({
        "summary": {"total": 1, "passed": 0, "warnings": 0, "errors": 1},
        "files": [{"file": "01_a.svg", "errors": ["text overflow"], "warnings": []}],
    }))
    write_script(make_cfg(tmp_path).ppt_scripts_root, "svg_quality_checker.py", "print('[OK]')\n")
    pass  # scripts root is make_cfg default
    with pytest.raises(ExportBlocked) as ei:
        bridge.export_pptx(cfg, "proj_20260101")
    env = envelope(ei.value)
    assert env["error"]["code"] == "PPT_EXPORT_BLOCKED"
    assert "text overflow" in env["error"]["message"]  # fixable summary included
