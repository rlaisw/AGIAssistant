"""Typed PPT-tool error taxonomy -> honest MCP error envelopes (spec 009, FR-010).

Envelope: {"error": {"code", "message", "hint"}} — code is machine-readable,
message carries verbatim script diagnostics, hint is the remediation the
Dify agent can act on without human help.
"""

from __future__ import annotations

import logging

log = logging.getLogger("agentic_rag_mcp.ppt")


class PptError(Exception):
    code = "PPT_SCRIPT_FAILED"

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint or self._default_hint()

    def _default_hint(self) -> str:
        return "Retry the tool call; if it keeps failing, report the error to the user."

    def to_envelope(self) -> dict:
        return {"error": {"code": self.code, "message": self.message, "hint": self.hint}}


class InvalidProject(PptError):
    code = "PPT_INVALID_PROJECT"

    def _default_hint(self) -> str:
        return "Call ppt_project_init first and use the returned project_id."


class InvalidInput(PptError):
    code = "PPT_INVALID_INPUT"

    def _default_hint(self) -> str:
        return "Fix the named input and retry the same tool call."


class MissingIcon(PptError):
    code = "PPT_MISSING_ICON"

    def _default_hint(self) -> str:
        return "Re-pick each missing icon from the library (tabler-outline, simple-icons) and retry."


class ScriptTimeout(PptError):
    code = "PPT_SCRIPT_TIMEOUT"

    def _default_hint(self) -> str:
        return "Retry the call; if it repeats, reduce page count or complexity."


class ScriptFailure(PptError):
    code = "PPT_SCRIPT_FAILED"

    def _default_hint(self) -> str:
        return "Read the message for the script's own diagnostics and adjust the call."


class CheckFailed(PptError):
    code = "PPT_CHECK_FAILED"

    def _default_hint(self) -> str:
        return "Fix the listed page issues with ppt_write_page, then rerun ppt_check."


class ExportBlocked(PptError):
    code = "PPT_EXPORT_BLOCKED"

    def _default_hint(self) -> str:
        return "Fix every blocking issue via ppt_write_page and pass ppt_check before exporting."


class WorkspaceError(PptError):
    code = "PPT_WORKSPACE_ERROR"

    def _default_hint(self) -> str:
        return "Verify the ppt-master mount and [ppt] config paths, then retry."


def envelope(exc: PptError) -> dict:
    return exc.to_envelope()
