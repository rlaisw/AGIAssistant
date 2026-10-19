"""PPT-Master bridge: expose ppt-master as MCP tools (spec 009)."""

from . import bridge
from .errors import (
    CheckFailed,
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

__all__ = [
    "bridge",
    "envelope",
    "PptError",
    "InvalidProject",
    "InvalidInput",
    "MissingIcon",
    "ScriptTimeout",
    "ScriptFailure",
    "CheckFailed",
    "ExportBlocked",
    "WorkspaceError",
]
