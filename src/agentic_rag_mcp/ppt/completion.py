"""Completion-page machinery: per-artifact preview snapshots + served page (spec 010).

Research R1/R2/R4: snapshots reuse the pipeline's own self-contained renderings
(finalize step), are write-once per export artifact, and degrade honestly —
a preview failure never blocks the export, it writes the .degraded marker.
"""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

from ..config import Config
from .errors import InvalidInput

_PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_SLIDE_FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*\.svg$")

_PAGE_CSS = """
body{margin:0;font-family:system-ui,-apple-system,'Segoe UI',sans-serif;background:#fafafa;color:#212121}
main{max-width:960px;margin:0 auto;padding:24px 16px}
h1{font-size:20px;margin:0 0 4px}
.meta{color:#5f6b7a;font-size:14px;margin:4px 0}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;align-items:center}
.btn{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:10px;
     text-decoration:none;font-weight:600;font-size:15px}
.download{background:#1565c0;color:#fff}
.edit{border:1px solid #d5dce5;color:#0d47a1;background:#fff}
.slide{margin:28px 0}
.slide img{width:100%;height:auto;border:1px solid #d5dce5;border-radius:8px;background:#fff;display:block}
.unavailable{border:1px dashed #d5dce5;border-radius:8px;padding:48px 16px;text-align:center;
              color:#5f6b7a;background:#fff}
footer{color:#9aa4b2;font-size:12px;margin-top:32px}
@media (prefers-color-scheme: dark){
  body{background:#101418;color:#e8eaed}
  .edit{background:#1a2029;color:#7ea6e0;border-color:#2a323d}
  .unavailable{background:#161b22;border-color:#2a323d}
  .slide img{background:#161b22;border-color:#2a323d}
}
"""


def projects_root(cfg: Config) -> Path:
    from .bridge import projects_root as _root

    return _root(cfg)


def _validate_ids(project_id: str, stem: str) -> None:
    if not project_id or not _PROJECT_ID_RE.match(project_id):
        raise InvalidInput(f"invalid project id: {project_id!r}")
    if not stem or not _PROJECT_ID_RE.match(stem):
        raise InvalidInput(f"invalid artifact stem: {stem!r}")


def artifact_exists(cfg: Config, project_id: str, stem: str) -> bool:
    _validate_ids(project_id, stem)
    return (projects_root(cfg) / project_id / "exports" / f"{stem}.pptx").is_file()


def snapshot_previews(cfg: Config, project_id: str, stem: str) -> bool:
    """Snapshot the pipeline's self-contained renderings for one artifact.

    Returns True when previews are ready; False when degraded. Never raises
    (research R4: preview failure never blocks the export).
    """
    from .bridge import _run_allow_failure, _workspace

    _validate_ids(project_id, stem)
    ws = _workspace(cfg, project_id)
    dest = ws / "previews" / stem
    if dest.is_dir():  # write-once per artifact (FR-007)
        return not (dest / ".degraded").exists()
    try:
        _run_allow_failure(cfg, "finalize_svg.py", [str(ws)])
        src = ws / "svg_final"
        files = sorted(src.glob("*.svg")) if src.is_dir() else []
        if not files:
            raise RuntimeError("finalize produced no slide renderings")
        dest.mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.copy2(f, dest / f.name)
        return True
    except Exception:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / ".degraded").write_text("preview generation failed\n", encoding="utf-8")
        return False


def _slides_for(cfg: Config, project_id: str, stem: str) -> tuple[list[str], bool]:
    dest = projects_root(cfg) / project_id / "previews" / stem
    if not dest.is_dir():
        return [], True
    degraded = (dest / ".degraded").is_file()
    return sorted(p.name for p in dest.glob("*.svg")), degraded


def render_completion_page(cfg: Config, project_id: str, stem: str) -> str:
    """The completion page: slide previews, download control, edit path."""
    _validate_ids(project_id, stem)
    if not artifact_exists(cfg, project_id, stem):
        raise FileNotFoundError(f"no artifact {stem} in project {project_id}")
    slides, degraded = _slides_for(cfg, project_id, stem)
    download_url = f"{cfg.ppt_exports_url_base.rstrip('/')}/{project_id}/{stem}.pptx"
    title = html.escape(f"{project_id} · {stem}")

    if degraded or not slides:
        body_slides = (
            f'<div class="unavailable">Preview unavailable for this export — '
            f"the file itself is intact.</div>"
        )
        meta = "preview degraded"
    else:
        body_slides = "".join(
            f'<div class="slide"><p class="meta">Page {i}</p>'
            f'<img src="slides/{html.escape(name)}" alt="Slide {i}" loading="lazy"></div>'
            for i, name in enumerate(slides, start=1)
        )
        meta = f"{len(slides)} slide(s)"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Deck ready — {title}</title>
<style>{_PAGE_CSS}</style>
</head>
<body>
<main>
<h1>PowerPoint deck ready</h1>
<p class="meta">{title} · {meta}</p>
<div class="actions">
<a class="btn download" href="{html.escape(download_url)}" download>&#11015; Download .pptx</a>
<span class="btn edit" title="Revisions happen in the chat">&#9998; Edit — ask in chat</span>
</div>
<p class="meta">To edit: return to the chat and ask, for example, &ldquo;revise page 2 of
this deck&rdquo;. The downloaded file is fully editable in PowerPoint.</p>
{body_slides}
<footer>Generated by PPT-Master &middot; previews are the exact page renderings of this export</footer>
</main>
</body>
</html>
"""


def resolve_slide(cfg: Config, project_id: str, stem: str, filename: str) -> Path:
    """Traversal-safe slide-asset resolution for the /decks/.../slides/ route."""
    _validate_ids(project_id, stem)
    if not filename or not _SLIDE_FILE_RE.match(filename):
        raise InvalidInput(f"invalid slide filename: {filename!r}")
    dest = projects_root(cfg) / project_id / "previews" / stem
    path = (dest / filename).resolve()
    if not path.is_relative_to(dest.resolve()):
        raise InvalidInput("path escapes the slide directory")
    if not path.is_file():
        raise FileNotFoundError(f"no slide named {filename} in this artifact")
    return path
