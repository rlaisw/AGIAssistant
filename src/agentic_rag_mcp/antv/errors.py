"""AntV tool error taxonomy -> honest MCP error envelopes (spec 012, FR-006).

Uniform with the ppt tools: {"error": {code, message, hint}}.
"""

from __future__ import annotations


class AntvError(Exception):
    code = "ANTV_SERVICE_ERROR"

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint or self._default_hint()

    def _default_hint(self) -> str:
        return "Retry the tool call; if it keeps failing, answer without a chart and say so."

    def to_envelope(self) -> dict:
        return {"error": {"code": self.code, "message": self.message, "hint": self.hint}}


class AntvInvalidType(AntvError):
    code = "ANTV_INVALID_TYPE"

    def _default_hint(self) -> str:
        return "Pick a chart_type from the supported list in the message and retry."


class AntvInvalidInput(AntvError):
    code = "ANTV_INVALID_INPUT"

    def _default_hint(self) -> str:
        return "Fix the named input (data shape, size cap, or title length) and retry."


class AntvServiceError(AntvError):
    code = "ANTV_SERVICE_ERROR"

    def _default_hint(self) -> str:
        return ("The rendering service rejected the request — read the message; "
                "if the service is down, answer without a chart and say so.")


class AntvServiceTimeout(AntvError):
    code = "ANTV_SERVICE_TIMEOUT"

    def _default_hint(self) -> str:
        return "The rendering service timed out — retry once, then answer without a chart and say so."


def envelope(exc: AntvError) -> dict:
    return exc.to_envelope()
