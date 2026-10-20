"""antv_infographic tool body: browser-rendered infographics (spec 012, R3).

Stores the declarative syntax on the sidecar; serves an HTML page that loads
the @antv/infographic engine from CDN and renders client-side — no
server-side DOM, no puppeteer (Constitution III).
"""

from __future__ import annotations

import re
import uuid

from ..config import Config
from .errors import AntvInvalidInput

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

_PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Infographic</title>
<style>
body{margin:0;background:#fafafa;font-family:system-ui,sans-serif}
#container{max-width:960px;margin:0 auto;padding:24px 16px}
#error{display:none;padding:48px 16px;text-align:center;color:#b3261e;white-space:pre-wrap}
</style>
</head>
<body>
<div id="container"><div id="error">loading…</div></div>
<script src="https://cdn.jsdelivr.net/npm/@antv/infographic@latest/dist/infographic.min.js"><\/script>
<script>
const syntax = {syntax_json};
const errorEl = document.getElementById('error');
try {
  if (!window.Infographic) throw new Error('engine failed to load (CDN unreachable?)');
  errorEl.style.display = 'none';
  const ig = new window.Infographic({
    container: '#container', width: '100%', height: '100%',
  });
  ig.render(syntax);
} catch (e) {
  errorEl.style.display = 'block';
  errorEl.textContent = 'Infographic error: ' + (e && e.message ? e.message : 'unknown');
}
</script>
</body>
</html>
"""


def served_dir(cfg: Config):
    path = cfg.antv_infographic_served_root
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_id(infographic_id: str) -> None:
    if not infographic_id or not _ID_RE.match(infographic_id):
        raise AntvInvalidInput(f"invalid infographic id: {infographic_id!r}")


def create_infographic(cfg: Config, description: str) -> dict:
    if not description or not description.strip():
        raise AntvInvalidInput("description (the infographic syntax) must be non-empty")
    if len(description.encode("utf-8")) > cfg.antv_infographic_max_syntax_bytes:
        raise AntvInvalidInput(
            f"description too large (cap {cfg.antv_infographic_max_syntax_bytes} bytes)"
        )
    infographic_id = uuid.uuid4().hex[:12]
    (served_dir(cfg) / f"{infographic_id}.txt").write_text(description, encoding="utf-8")
    base = cfg.ppt_exports_url_base.rsplit("/exports", 1)[0].rstrip("/")
    return {
        "id": infographic_id,
        "url": f"{base}/infographics/{infographic_id}/",
        "usage": (
            "Give the user the url as a markdown link — it opens the rendered "
            "infographic in a browser."
        ),
    }


def render_infographic_page(cfg: Config, infographic_id: str) -> str:
    validate_id(infographic_id)
    path = cfg.antv_infographic_served_root / f"{infographic_id}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"no infographic {infographic_id}")
    syntax = path.read_text(encoding="utf-8")
    return _PAGE_TEMPLATE.replace("{syntax_json}", json_dump(syntax))


def json_dump(text: str) -> str:
    import json

    return json.dumps(text)
