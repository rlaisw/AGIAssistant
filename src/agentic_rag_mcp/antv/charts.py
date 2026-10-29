"""antv_chart tool body: GPT-Vis chart rendering via HTTP (spec 012, R1-R2).

The supported-type list is the honest single source (FR-003): geo types are
excluded by design (region-limited, unsupported in private deployments).
"""

from __future__ import annotations

import json

import httpx

from ..config import Config
from .errors import AntvInvalidInput, AntvInvalidType, AntvServiceError, AntvServiceTimeout

SUPPORTED_TYPES = (
    "line", "area", "bar", "column", "pie", "radar", "scatter",
    "histogram", "funnel", "treemap", "sankey", "dual-axes",
    "word-cloud", "boxplot", "venn", "liquid",
    "flow", "mind-map", "fishbone", "organization", "network",
)
MAX_DATA_SERIALIZED = 65_536
MAX_TITLE = 200


def _validate(chart_type: str, data: list, title: str) -> None:
    if chart_type not in SUPPORTED_TYPES:
        raise AntvInvalidType(
            f"unsupported chart_type {chart_type!r}; supported: {', '.join(SUPPORTED_TYPES)}"
        )
    if not isinstance(data, list) or not data:
        raise AntvInvalidInput("data must be a non-empty list of records")
    if not all(isinstance(d, dict) for d in data):
        raise AntvInvalidInput("data records must be objects (e.g. {\"category\": \"A\", \"value\": 30})")
    if not all(any(v is not None for v in d.values()) for d in data):
        raise AntvInvalidInput("each data record needs at least one non-null field")
    if len(json.dumps(data)) > MAX_DATA_SERIALIZED:
        raise AntvInvalidInput(
            f"data too large (serialized {len(json.dumps(data))} bytes, cap {MAX_DATA_SERIALIZED}) — sample or aggregate first"
        )
    if len(title or "") > MAX_TITLE:
        raise AntvInvalidInput(f"title longer than {MAX_TITLE} chars")


def _normalize_data(chart_type: str, data: list) -> list:
    """Auto-normalize 2-field records to the canonical shape the rendering
    service plots (arbitrary field names render an EMPTY chart — verified
    empirically 2026-10-20). Records with the canonical fields pass through.
    Scatter is x/y-only (verified 2026-10-28: category/value renders an
    empty frame — image bytes do not scale with point count; x/y does)."""
    key_field = "time" if chart_type in ("line", "area") else "category"
    if chart_type == "scatter":
        return _normalize_scatter(data)
    if all(key_field in d and "value" in d for d in data):
        return data
    # exactly two fields: one string-ish -> category/time, one numeric -> value
    normalized = []
    for d in data:
        if len(d) != 2:
            raise AntvInvalidInput(
                "data records must be {\"category\": <name>, \"value\": <number>} "
                f"(or \"time\" for line/area); got fields {list(d.keys())!r}"
            )
        string_key = next((k for k, v in d.items() if isinstance(v, str)), None)
        number_key = next((k for k, v in d.items() if isinstance(v, (int, float))
                           and not isinstance(v, bool)), None)
        if string_key is None or number_key is None:
            raise AntvInvalidInput(
                "data records need one string field (name) and one numeric "
                f"field (value); got {d!r}"
            )
        normalized.append({key_field: d[string_key], "value": d[number_key]})
    return normalized


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _normalize_scatter(data: list) -> list:
    """Scatter plots two numeric axes: {x, y} is canonical and passes through;
    {category, value} with BOTH numeric is mapped to {x, y} so calls made per
    the generic tool description still render (2026-10-28)."""
    if all(_is_num(d.get("x")) and _is_num(d.get("y")) for d in data):
        return data
    if all(_is_num(d.get("category")) and _is_num(d.get("value")) for d in data):
        return [{"x": d["category"], "y": d["value"]} for d in data]
    raise AntvInvalidInput(
        "scatter data records must be {\"x\": <number>, \"y\": <number>} "
        "(height/weight, age/salary, …); {\"category\": <number>, \"value\": <number>} "
        "is also accepted and mapped"
    )


def generate_chart(cfg: Config, chart_type: str, data: list, title: str = "",
                   axis_x_title: str = "", axis_y_title: str = "",
                   width: int = 0, height: int = 0) -> dict:
    _validate(chart_type, data, title)
    if len(axis_x_title) > 60 or len(axis_y_title) > 60:
        raise AntvInvalidInput("axis titles are capped at 60 chars")
    if not (0 <= width <= 4000 and 0 <= height <= 4000):
        raise AntvInvalidInput("width/height must be 0 (service default) or <= 4000")
    data = _normalize_data(chart_type, data)
    payload = {"type": chart_type, "data": data}
    if title:
        payload["title"] = title
    if axis_x_title:
        payload["axisXTitle"] = axis_x_title
    if axis_y_title:
        payload["axisYTitle"] = axis_y_title
    if width:
        payload["width"] = width
    if height:
        payload["height"] = height
    try:
        resp = httpx.post(cfg.antv_chart_service_url, json=payload,
                          timeout=cfg.antv_chart_timeout_s)
    except httpx.TimeoutException as exc:
        raise AntvServiceTimeout(
            f"chart service timed out after {cfg.antv_chart_timeout_s}s"
        ) from exc
    except httpx.HTTPError as exc:
        raise AntvServiceError(
            f"chart service unreachable: {exc.__class__.__name__}"
        ) from exc
    if resp.status_code != 200:
        raise AntvServiceError(
            f"chart service returned HTTP {resp.status_code}: {resp.text[:200]}"
        )
    body = resp.json()
    if not body.get("success"):
        raise AntvServiceError(
            f"chart service rejected the request: {body.get('errorMessage', 'unknown error')}"
        )
    image_url = body.get("resultObj")
    if not image_url:
        raise AntvServiceError("chart service returned success without an image url")
    return {
        "chart_type": chart_type,
        "image_url": image_url,
        "usage": (
            "Embed image_url in your markdown answer as ![chart](<image_url>). "
            "For PPT pages, reference it as <image href=...> — the deck pipeline "
            "downloads and embeds the bytes automatically (self-contained export)."
        ),
    }
