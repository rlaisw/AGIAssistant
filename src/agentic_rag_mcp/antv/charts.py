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


def generate_chart(cfg: Config, chart_type: str, data: list, title: str = "") -> dict:
    _validate(chart_type, data, title)
    payload = {"type": chart_type, "data": data}
    if title:
        payload["title"] = title
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
