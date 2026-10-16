"""Contract: status additive logging field + config surface (spec 008; C1/C2, FR-003/012)."""

import json

import agentic_rag_mcp.config as config_mod
import agentic_rag_mcp.server as server_mod
from agentic_rag_mcp.config import Config
from agentic_rag_mcp.server import build_server


def call(server, name, args):
    import asyncio
    raw = asyncio.run(server.call_tool(name, args))
    structured = [b["result"] for b in raw if isinstance(b, dict) and "result" in b]
    if structured:
        return structured[0]
    texts = [getattr(b, "text", "") for b in raw if getattr(b, "text", "")]
    joined = "".join(texts).strip()
    return json.loads(joined) if joined else None


def _server(tmp_path, monkeypatch, **cfg_kw):
    monkeypatch.setattr(server_mod, "build_providers", lambda cfg: [])
    cfg = Config(state_db=tmp_path / "s.sqlite3", vector_dir=tmp_path / "v",
                 decider_enabled=False, log_file=tmp_path / "log" / "server.log", **cfg_kw)
    return build_server(cfg)


def test_status_gains_additive_logging_field(tmp_path, monkeypatch):
    """C1/FR-012: every existing status field present + logging{level, log_file, writable}."""
    srv = _server(tmp_path, monkeypatch)
    out = call(srv, "status", {})
    for field in ("version", "decision_layer", "sources", "index"):
        assert field in out, f"frozen status field missing: {field}"
    assert set(out["logging"]) == {"level", "log_file", "writable"}
    assert out["logging"]["level"] == "INFO"
    assert out["logging"]["writable"] is True
    assert out["logging"]["log_file"].endswith("server.log")


def test_status_reflects_debug_level(tmp_path, monkeypatch):
    srv = _server(tmp_path, monkeypatch, log_level="DEBUG")
    out = call(srv, "status", {})
    assert out["logging"]["level"] == "DEBUG"


def test_config_level_from_toml(tmp_path, monkeypatch):
    """C2: [logging] level in config.toml resolves; LOG_LEVEL env overrides it."""

    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text('[logging]\nlevel = "WARNING"\n')
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", cfg_file)
    cfg = config_mod.load_config(cfg_file)
    assert cfg.log_level == "WARNING"

    monkeypatch.setenv("LOG_LEVEL", "ERROR")  # env wins
    cfg = config_mod.load_config(cfg_file)
    assert cfg.log_level == "ERROR"
