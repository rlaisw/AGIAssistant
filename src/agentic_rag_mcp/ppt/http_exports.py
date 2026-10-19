"""Static /exports file serving for generated decks (spec 009, research R2).

Pure path resolution so the HTTP layer stays thin and testable.
"""

from __future__ import annotations

import re
from pathlib import Path

from .errors import InvalidInput

PPTX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.presentation"
)
_PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


class ExportNotFound(Exception):
    """Raised when the requested artifact does not exist (maps to HTTP 404)."""


def resolve_export(projects_root: Path, project_id: str, filename: str) -> Path:
    """Resolve and validate an export file path; traversal-safe (matrix T25)."""
    if not project_id or not _PROJECT_ID_RE.match(project_id):
        raise InvalidInput(f"invalid project id: {project_id!r}")
    if (
        not filename
        or "/" in filename
        or "\\" in filename
        or ".." in filename
        or not filename.endswith(".pptx")
    ):
        raise InvalidInput(f"invalid export filename: {filename!r}")
    root = Path(projects_root).resolve()
    path = (root / project_id / "exports" / filename).resolve()
    if not path.is_relative_to(root):
        raise InvalidInput("path escapes the exports root")
    if not path.is_file():
        raise ExportNotFound(f"no export named {filename} in project {project_id}")
    return path
