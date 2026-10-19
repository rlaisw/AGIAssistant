"""Subprocess bridge to the ppt-master toolchain (spec 009, research R1).

Wraps the installed ppt-master clone's scripts — never edits them:
  project_manager.py / icon_sync.py / svg_quality_checker.py / svg_to_pptx.py
Page writing and SVG sanitization are native (no script involved).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from ..config import Config
from .errors import (
    ExportBlocked,
    InvalidInput,
    InvalidProject,
    MissingIcon,
    ScriptFailure,
    ScriptTimeout,
    WorkspaceError,
)

MAX_STDERR_CHARS = 2000
MAX_SVG_BYTES = 256 * 1024
CANONICAL_VIEWBOX = "0 0 1280 720"
_PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_FORBIDDEN = [
    ("<script", "script element"),
    ("<foreignObject", "foreignObject element"),
    ("<style", "style element"),
    ("textPath", "textPath element"),
]
_EVENT_ATTR_RE = re.compile(r"\son\w+\s*=", re.IGNORECASE)
_CLASS_ATTR_RE = re.compile(r"\sclass\s*=", re.IGNORECASE)
_HREF_RE = re.compile(r'(?:xlink:)?href\s*=\s*"([^"]*)"')


def _tail(text: str) -> str:
    return text.strip()[-MAX_STDERR_CHARS:]


def _subprocess_env(cfg: Config) -> dict:
    env = dict(os.environ)
    env["PPT_PROJECTS_ROOT"] = str(projects_root(cfg))
    return env


def _run(cfg: Config, script: str, args: list[str]) -> subprocess.CompletedProcess:
    """Run one ppt-master script; map timeout/OSError/exit-code failures to PptError."""
    exe = cfg.ppt_python or sys.executable
    cmd = [exe, str(Path(cfg.ppt_scripts_root) / "scripts" / script), *args]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=cfg.ppt_script_timeout_s,
            cwd=str(cfg.ppt_scripts_root),
            env=_subprocess_env(cfg),
        )
    except subprocess.TimeoutExpired as exc:
        raise ScriptTimeout(f"{script} exceeded {cfg.ppt_script_timeout_s}s") from exc
    except OSError as exc:
        raise ScriptFailure(
            f"cannot run {script}: {exc}",
            hint="Verify [ppt] scripts_root and the ppt-master mount, then retry.",
        ) from exc
    if proc.returncode != 0:
        detail = proc.stderr or proc.stdout or f"exit code {proc.returncode}"
        raise ScriptFailure(_tail(f"{script} failed: {detail}"))
    return proc


def projects_root(cfg: Config) -> Path:
    """ppt-master hardcodes PROJECTS_ROOT = <repo>/projects (project_management/paths.py);
    derive it from scripts_root so tool ops always match where the scripts write."""
    return Path(cfg.ppt_scripts_root).parent.parent / "projects"


def _workspace(cfg: Config, project_id: str) -> Path:
    if not project_id or not _PROJECT_ID_RE.match(project_id):
        raise InvalidProject(f"invalid project id: {project_id!r}")
    ws = projects_root(cfg) / project_id
    if not ws.is_dir():
        raise InvalidProject(f"unknown project: {project_id}")
    return ws


# ------------------------------------------------------------------ sanitization

def sanitize_svg(svg: str) -> None:
    """Validate an agent-authored page before persisting (matrix T08/T10/T11)."""
    if not svg or not svg.strip():
        raise InvalidInput("svg is empty")
    if len(svg.encode("utf-8")) > MAX_SVG_BYTES:
        raise InvalidInput(f"svg exceeds {MAX_SVG_BYTES} bytes")
    lowered = svg.lower()
    for needle, what in _FORBIDDEN:
        if needle.lower() in lowered:
            raise InvalidInput(f"svg contains forbidden {what}")
    if _EVENT_ATTR_RE.search(svg):
        raise InvalidInput("svg contains an event attribute (on*)")
    if _CLASS_ATTR_RE.search(svg):
        raise InvalidInput("svg contains a class attribute")
    for href in _HREF_RE.findall(svg):
        if not (href.startswith("data:") or href.startswith("https:") or href.startswith("#")):
            raise InvalidInput(f"svg references a non-https external href: {href[:80]}")
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        raise InvalidInput(f"svg is not well-formed XML: {exc}") from exc
    if root.tag.endswith("svg") is False or root.get("viewBox") != CANONICAL_VIEWBOX:
        raise InvalidInput(f"svg root must declare viewBox='{CANONICAL_VIEWBOX}'")


# ------------------------------------------------------------------ tool bodies

MINIMAL_SPEC_LOCK = """<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: en-US

## typography
- title_family: Segoe UI, sans-serif
- body_family: Segoe UI, sans-serif
- font_family: Segoe UI, sans-serif
- body: 24
- title: 44

## colors
- background: #FAFAFA
- secondary_bg: #EDF2F8
- primary: #1565C0
- accent: #0D47A1
- secondary_accent: #7EA6E0
- body_text: #212121
- secondary_text: #5F6B7A
- divider: #D5DCE5

## pptx_structure
- mode: flat
"""


def _ensure_spec_lock(ws: Path) -> None:
    """The exporter requires a lock (canvas/language/typography/colors/structure)."""
    lock = ws / "spec_lock.md"
    if not lock.is_file():
        lock.write_text(MINIMAL_SPEC_LOCK, encoding="utf-8")


def project_init(cfg: Config, name: str) -> dict:
    if not name or len(name) > 64 or not _PROJECT_ID_RE.match(name.strip()) or name != name.strip():
        raise InvalidInput(
            "name must be 1-64 chars, url-safe (letters, digits, -, _), no spaces"
        )
    try:
        projects_root(cfg).mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WorkspaceError(f"cannot create projects root: {exc}") from exc

    for candidate in (name, f"{name}_{uuid.uuid4().hex[:4]}"):
        proc = _run_allow_failure(cfg, "project_manager.py", ["init", candidate])
        combined = f"{proc.stdout}\n{proc.stderr}"
        match = re.search(r"Project initialized(?:\s+at)?:\s*(\S+)", combined)
        if match and proc.returncode == 0:
            break
        if proc.returncode != 0 and "exist" not in combined.lower():
            raise ScriptFailure(
                f"project init failed: {_tail(proc.stderr or proc.stdout)}"
            )
    else:
        raise ScriptFailure("project init failed twice on name collision")

    project_id = Path(match.group(1)).name  # noqa: F821 — loop always breaks or raises
    ws = projects_root(cfg) / project_id
    if not ws.is_dir():
        raise WorkspaceError(f"project workspace missing after init: {ws}")
    _ensure_spec_lock(ws)
    return {"project_id": project_id, "workspace": str(ws), "max_pages": cfg.ppt_max_pages}


def _run_allow_failure(cfg: Config, script: str, args: list[str]) -> subprocess.CompletedProcess:
    """Run without the exit-code gate (init parses output instead)."""
    exe = cfg.ppt_python or sys.executable
    cmd = [exe, str(Path(cfg.ppt_scripts_root) / "scripts" / script), *args]
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=cfg.ppt_script_timeout_s, cwd=str(cfg.ppt_scripts_root),
            env=_subprocess_env(cfg),
        )
    except subprocess.TimeoutExpired as exc:
        raise ScriptTimeout(f"{script} exceeded {cfg.ppt_script_timeout_s}s") from exc
    except OSError as exc:
        raise ScriptFailure(
            f"cannot run {script}: {exc}",
            hint="Verify [ppt] scripts_root and the ppt-master mount, then retry.",
        ) from exc


def icon_sync(cfg: Config, project_id: str, icons: list[str]) -> dict:
    ws = _workspace(cfg, project_id)
    if not icons or not all(isinstance(i, str) and i.strip() for i in icons):
        raise InvalidInput("icons must be a non-empty list of library/name strings")
    proc = _run_allow_failure(cfg, "icon_sync.py", [str(ws), *icons])
    combined = f"{proc.stdout}\n{proc.stderr}"
    synced = re.findall(r"^\s+\+\s+(\S+)$", combined, flags=re.MULTILINE)
    missing = re.findall(r"✗\s+(\S+)", combined)
    if proc.returncode != 0 and not synced and not missing:
        raise ScriptFailure(f"icon sync failed: {_tail(proc.stderr or proc.stdout)}")
    if missing:
        raise MissingIcon(
            f"missing icons: {', '.join(missing)}"
            + (f" (synced: {', '.join(synced)})" if synced else ""),
            hint="Re-pick each missing icon from its library "
                 "(tabler-outline, simple-icons, chunk-filled, tabler-filled, "
                 "phosphor-duotone) and retry with only the valid ones.",
        )
    return {"synced": synced, "missing": []}


def write_page(cfg: Config, project_id: str, page_number: int, name: str, svg: str) -> dict:
    ws = _workspace(cfg, project_id)
    if not isinstance(page_number, int) or page_number < 1 or page_number > cfg.ppt_max_pages:
        raise InvalidInput(f"page_number must be an integer in 1..{cfg.ppt_max_pages}")
    if not name or not _NAME_RE.match(name):
        raise InvalidInput("name must be a lowercase url-safe slug (a-z, 0-9, -, _)")
    sanitize_svg(svg)
    out_dir = ws / "svg_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{page_number:02d}_{name}.svg"
    path.write_text(svg, encoding="utf-8")
    return {"file": f"svg_output/{page_number:02d}_{name}.svg", "bytes": path.stat().st_size}


def _read_check_report(cfg: Config, project_id: str) -> dict:
    ws = _workspace(cfg, project_id)
    _run_allow_failure(cfg, "svg_quality_checker.py",
                       [str(ws), "--canonical-authoring", "--stage", "final", "--json"])
    report_path = ws / "validation" / "svg_quality_report.json"
    if not report_path.is_file():
        raise ScriptFailure("checker wrote no report; is svg_output non-empty?")
    import json

    report = json.loads(report_path.read_text())
    files = report.get("files", [])
    blocking = sum(len(f.get("errors", [])) for f in files)
    warnings = sum(len(f.get("warnings", [])) for f in files)
    details = []
    for f in files:
        for issue in f.get("errors", []):
            details.append(f"[ERROR] {f['file']}: {issue}")
        for issue in f.get("warnings", []):
            details.append(f"[WARN] {f['file']}: {issue}")
    return {
        "passing": bool(files) and blocking == 0,
        "blocking_errors": blocking,
        "warnings": warnings,
        "details": details,
    }


def check(cfg: Config, project_id: str) -> dict:
    return _read_check_report(cfg, project_id)


def export_pptx(cfg: Config, project_id: str) -> dict:
    result = _read_check_report(cfg, project_id)
    if not result["passing"]:
        summary = "; ".join(result["details"][:10]) or "no pages found"
        raise ExportBlocked(
            f"pages have {result['blocking_errors']} blocking error(s): {summary}",
            hint="Fix every [ERROR] via ppt_write_page, rerun ppt_check, then export.",
        )
    ws = _workspace(cfg, project_id)
    proc = _run_allow_failure(cfg, "svg_to_pptx.py", [str(ws)])
    match = re.search(r"\[PPTX\]\s+(\S+\.pptx)", f"{proc.stdout}\n{proc.stderr}")
    if match:
        candidate = Path(match.group(1))
        if not candidate.is_absolute():
            candidate = Path(cfg.ppt_scripts_root).parent.parent / candidate
    else:
        candidate = None
    exports = ws / "exports"
    if candidate is None or not candidate.is_file():
        # fall back to the newest artifact in the project's exports dir
        if not exports.is_dir() or not list(exports.glob("*.pptx")):
            raise ScriptFailure(
                f"export produced no pptx: {_tail(proc.stderr or proc.stdout)}"
            )
        candidate = max(exports.glob("*.pptx"), key=lambda p: p.stat().st_mtime)
    # the artifact must live inside this project's exports dir (or be copied there)
    if candidate.parent != exports:
        dest = exports / candidate.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(candidate.read_bytes())
        candidate = dest
    url = f"{cfg.ppt_exports_url_base.rstrip('/')}/{project_id}/{candidate.name}"
    stem = candidate.stem
    from . import completion

    completion.snapshot_previews(cfg, project_id, stem)  # never raises; degrades honestly (spec 010 R4)
    page_root = re.sub(r"/exports/?$", "", cfg.ppt_exports_url_base.rstrip("/"))
    page_url = f"{page_root}/decks/{project_id}/{stem}/"
    return {"file": f"exports/{candidate.name}", "url": url, "page_url": page_url}
