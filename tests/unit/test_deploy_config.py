"""Unit: deploy config resolution and redaction (spec 011, P01-P02)."""

from __future__ import annotations

from agentic_rag_mcp.config import Config
from agentic_rag_mcp.deploy.config import ConfigError, DeployConfig, redact, resolve


def test_defaults(tmp_path):
    cfg = Config(state_db=tmp_path / "s.sqlite3", vector_dir=tmp_path / "v",
                 decider_enabled=False)
    d = resolve(cfg)
    assert d.console_url == "http://localhost"
    assert d.sidecar_image == "agentic-rag-mcp:latest"
    assert d.container == "agentic-rag"
    assert d.db_container == "docker-db_postgres-1"
    assert d.console_email == "" and d.console_password == "" and d.api_key == ""


def test_config_file_section(tmp_path):
    cfg = Config(state_db=tmp_path / "s.sqlite3", vector_dir=tmp_path / "v",
                 decider_enabled=False,
                 raw={"dify": {"console_url": "http://dify.local",
                               "console_email": "a@b.c",
                               "console_password": "pw-file",
                               "api_key": "app-file"},
                      "deploy": {"container": "agentic-rag"}})
    d = resolve(cfg)
    assert d.console_url == "http://dify.local"
    assert d.console_email == "a@b.c"
    assert d.console_password == "pw-file"
    assert d.api_key == "app-file"


def test_env_overrides_file(tmp_path, monkeypatch):
    monkeypatch.setenv("DIFY_CONSOLE_EMAIL", "env@b.c")
    monkeypatch.setenv("DIFY_CONSOLE_PASSWORD", "env-pw")
    monkeypatch.setenv("DIFY_API_KEY", "app-env")
    monkeypatch.setenv("DIFY_CONSOLE_URL", "http://envhost")
    cfg = Config(state_db=tmp_path / "s.sqlite3", vector_dir=tmp_path / "v",
                 decider_enabled=False,
                 raw={"dify": {"console_email": "file@b.c",
                               "console_password": "file-pw"}})
    d = resolve(cfg)
    assert d.console_email == "env@b.c"
    assert d.console_password == "env-pw"
    assert d.api_key == "app-env"
    assert d.console_url == "http://envhost"


def test_redaction_masks_secrets(tmp_path):
    d = DeployConfig(console_password="s3cret-pw", api_key="app-k3y")
    text = "login with s3cret-pw and app-k3y at http://x"
    out = redact(text, d.secrets)
    assert "s3cret-pw" not in out and "app-k3y" not in out
    assert "***" in out


def test_redaction_ignores_empty_secrets():
    assert redact("plain", []) == "plain"


def test_require_console_raises(tmp_path):
    d = DeployConfig()
    try:
        d.require_console()
        raised = False
    except ConfigError as exc:
        raised = True
        assert "console_email" in str(exc)
    assert raised
