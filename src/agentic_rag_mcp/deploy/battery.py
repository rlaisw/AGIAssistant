"""Headless verification battery (spec 011, R5).

Scenario registry per contracts/deploy-cli.md; unique verify_<ts> project
names; teardown sweep; exit code = failed-scenario count (FR-011 cleanup).
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import time

import httpx

from .config import DeployConfig, redact

FIXTURE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
    'font-family="Segoe UI, sans-serif">'
    '<rect id="bg" data-pptx-role="background" x="0" y="0" width="1280" '
    'height="720" fill="#FAFAFA"/>'
    '<g id="t" data-pptx-bounds="64 64 1152 100">'
    '<text x="64" y="120" font-size="44" font-weight="bold" fill="#212121">'
    "Battery Deck</text>"
    '<text x="64" y="160" font-size="24" fill="#5F6B7A">'
    "verify battery fixture</text></g></svg>"
)

MCP_URL = "http://localhost:28080/mcp"


def mcp_call(name: str, arguments: dict) -> dict:
    resp = httpx.post(
        MCP_URL,
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
              "params": {"name": name, "arguments": arguments}},
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"},
        timeout=600,
    )
    for line in resp.text.splitlines():
        if line.startswith("data:") and '"result"' in line:
            content = json.loads(line[5:])["result"]["content"]  # noqa: F821
            try:
                return json.loads(content[0]["text"])
            except (json.JSONDecodeError, KeyError, IndexError):
                return {"raw": content[0].get("text", "")[:200]}
    raise RuntimeError(f"tool {name} returned no result: {resp.text[:200]}")


def projects_roots() -> list[pathlib.Path]:
    """All host-visible projects roots: the config-derived one and the repo's
    ppt-master clone (the container mounts it, so host-side sweeps find it here)."""
    import os

    from ..config import load_config
    from ..ppt.bridge import projects_root as _derived

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    candidates = [_derived(load_config()),
                  pathlib.Path(os.path.join(repo_root, "ppt-master", "projects"))]
    seen, roots = set(), []
    for c in candidates:
        key = str(c.resolve()) if c.exists() else str(c)
        if key not in seen:
            seen.add(key)
            roots.append(c)
    return roots


def _sweep(report: list) -> None:
    for root in projects_roots():
        if not root.is_dir():
            continue
        for p in root.glob("verify_*"):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
                report.append(f"swept {p.name}")


def scenario_health(dcfg: DeployConfig) -> tuple[bool, str]:
    r = httpx.get("http://localhost:28080/healthz", timeout=10)
    return r.status_code == 200 and r.json().get("status") == "ok", f"healthz={r.status_code}"


def scenario_tools_surface(dcfg: DeployConfig) -> tuple[bool, str]:
    from .tool_sync import fetch_live_tools

    tools = fetch_live_tools()
    names = sorted(t["name"] for t in tools)
    ppt = [n for n in names if n.startswith("ppt_")]
    return len(ppt) == 5, f"tools={len(names)} ppt={len(ppt)} ({', '.join(ppt)})" if ppt else f"tools={len(names)}, no ppt tools"


def scenario_deck_roundtrip(dcfg: DeployConfig) -> tuple[bool, str]:
    pid = mcp_call("ppt_project_init", {"name": f"verify_{int(time.time())}"})["project_id"]
    mcp_call("ppt_write_page", {"project_id": pid, "page_number": 1,
                                "name": "battery", "svg": FIXTURE_SVG})
    check = mcp_call("ppt_check", {"project_id": pid})
    if not check.get("passing"):
        return False, f"check not passing: {str(check.get('details'))[:150]}"
    exported = mcp_call("ppt_export", {"project_id": pid})
    ok = exported.get("url") and exported.get("page_url")
    return bool(ok), f"project={pid} url={'yes' if ok else 'missing'}"


def scenario_completion_page(dcfg: DeployConfig) -> tuple[bool, str]:
    pid = mcp_call("ppt_project_init", {"name": f"verify_page_{int(time.time())}"})["project_id"]
    mcp_call("ppt_write_page", {"project_id": pid, "page_number": 1,
                                "name": "battery", "svg": FIXTURE_SVG})
    mcp_call("ppt_check", {"project_id": pid})
    exported = mcp_call("ppt_export", {"project_id": pid})
    page = httpx.get(exported["page_url"], timeout=30)
    if page.status_code != 200 or "Download" not in page.text:
        return False, f"page={page.status_code}"
    m = re.search(r'src="(slides/[^"]+)"', page.text)
    if not m:
        return False, "no slide asset in page"
    slide = httpx.get(exported["page_url"] + m.group(1), timeout=30)
    dl = httpx.get(exported["url"], timeout=60)
    return (slide.headers.get("content-type", "").startswith("image/svg+xml")
            and dl.content[:2] == b"PK",
            f"page=200 slide={slide.status_code} pptx={len(dl.content)}B")


def scenario_honest_errors(dcfg: DeployConfig) -> tuple[bool, str]:
    r404 = httpx.get("http://localhost:28080/decks/ghost/none/", timeout=10)
    r400 = httpx.get(
        "http://localhost:28080/decks/ghost/none/slides/..%2F..%2Fetc.svg", timeout=10
    )
    ok = r404.status_code == 404 and r400.status_code in (400, 404)
    return ok, f"unknown={r404.status_code} traversal={r400.status_code}"


def scenario_chat_ui_liveness(dcfg: DeployConfig) -> tuple[bool, str]:
    try:
        r = httpx.get(dcfg.chat_ui_url, timeout=15, follow_redirects=True)
        return r.status_code == 200, f"chat-ui={r.status_code}"
    except httpx.HTTPError as exc:
        return False, f"chat-ui unreachable: {exc.__class__.__name__}"


def scenario_chat_journey(dcfg: DeployConfig) -> tuple[bool, str]:
    if not dcfg.api_key:
        return True, "skipped: no DIFY_API_KEY configured (notice, not failure)"
    with httpx.stream(
        "POST",
        dcfg.console_url.rstrip("/") + "/v1/chat-messages",
        headers={"Authorization": f"Bearer {dcfg.api_key}"},
        json={"inputs": {},
              "query": "generate a one-page deck about deploy automation: "
                       "one command rebuilds, deploys, and verifies the stack",
              "response_mode": "streaming",
              "conversation_id": "",
              "user": "deploy-battery"},
        timeout=600,
    ) as resp:
        if resp.status_code != 200:
            return False, f"chat-messages={resp.status_code}"
        answer = ""
        for line in resp.iter_lines():
            if line.startswith("data:"):
                try:
                    event = json.loads(line[5:])
                except json.JSONDecodeError:
                    continue
                if event.get("event") in ("message", "agent_message"):
                    answer += event.get("answer") or ""
    link = re.search(r"https?://\S*(?:/exports/|/decks/)\S+", answer)
    if not link:
        return False, f"no deck link in answer ({len(answer)} chars): {answer[:120]!r}"
    url = link.group(0).rstrip("*).,]'\"_`")  # strip markdown/bold closing punctuation
    target = httpx.get(url, timeout=60, follow_redirects=True)
    served = (target.status_code == 200
              and ("text/html" in target.headers.get("content-type", "")
                   or target.content[:2] == b"PK"))
    return served, f"link={url} serves={target.status_code}"


def registry(skip_chat: bool = False) -> list[tuple[str, object]]:
    scenarios = [
        ("health", scenario_health),
        ("tools-surface", scenario_tools_surface),
        ("deck-roundtrip", scenario_deck_roundtrip),
        ("completion-page", scenario_completion_page),
        ("honest-errors", scenario_honest_errors),
        ("chat-ui-liveness", scenario_chat_ui_liveness),
    ]
    if not skip_chat:
        scenarios.append(("chat-journey", scenario_chat_journey))
    return scenarios


def run_battery(dcfg: DeployConfig, skip_chat: bool = False) -> tuple[list[tuple[str, bool, str]], list[str]]:
    results: list[tuple[str, bool, str]] = []
    cleanup_notes: list[str] = []
    _sweep(cleanup_notes)
    for name, fn in registry(skip_chat=skip_chat):
        try:
            ok, evidence = fn(dcfg)
        except Exception as exc:  # noqa: BLE001 — battery reports, never crashes
            ok, evidence = False, f"{exc.__class__.__name__}: {exc}"
        results.append((name, ok, evidence))
        print(f"[{'✓' if ok else '✗'}] {name}: {redact(evidence, dcfg.secrets)}",
              flush=True)
    _sweep(cleanup_notes)
    return results, cleanup_notes
