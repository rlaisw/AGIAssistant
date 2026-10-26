"""Deploy-automation configuration and redaction (spec 011).

Resolution order: environment overrides config file; defaults match DEPLOY.md.
Secrets never reach the repo and are masked in every evidence string.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..config import Config

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ConfigError(Exception):
    """Raised when required configuration is missing — maps to exit code 2."""


@dataclass
class DeployConfig:
    console_url: str = "http://localhost"
    console_email: str = ""
    console_password: str = ""
    api_key: str = ""
    app_name: str = "AGI Assistant"
    chat_ui_url: str = "http://localhost:3000"
    sidecar_image: str = "agentic-rag-mcp:latest"
    container: str = "agentic-rag"
    db_container: str = "docker-db_postgres-1"
    api_container: str = "docker-api-1"
    retention_days: int = 30
    dsl_path: str = os.path.join(
        REPO_ROOT, "dify", "Chatflow Basic (AgenticRAG Agent + PPT-Master).yml"
    )

    @property
    def secrets(self) -> list[str]:
        return [s for s in (self.console_password, self.api_key) if s]

    def require_console(self) -> None:
        if not self.console_email or not self.console_password:
            raise ConfigError(
                "console credentials required: set [dify] console_email/console_password "
                "in config.toml or DIFY_CONSOLE_EMAIL/DIFY_CONSOLE_PASSWORD"
            )


def resolve(cfg: Config) -> DeployConfig:
    raw = getattr(cfg, "raw", {}) or {}
    dify = raw.get("dify", {}) or {}
    deploy = raw.get("deploy", {}) or {}
    return DeployConfig(
        console_url=os.environ.get("DIFY_CONSOLE_URL")
        or str(dify.get("console_url", "http://localhost")),
        console_email=os.environ.get("DIFY_CONSOLE_EMAIL")
        or str(dify.get("console_email", "")),
        console_password=os.environ.get("DIFY_CONSOLE_PASSWORD")
        or str(dify.get("console_password", "")),
        api_key=os.environ.get("DIFY_API_KEY") or str(dify.get("api_key", "")),
        app_name=str(dify.get("app_name", "AGI Assistant")),
        chat_ui_url=str(deploy.get("chat_ui_url", "http://localhost:3000")),
        sidecar_image=str(deploy.get("sidecar_image", "agentic-rag-mcp:latest")),
        container=str(deploy.get("container", "agentic-rag")),
        db_container=str(deploy.get("db_container", "docker-db_postgres-1")),
        api_container=str(deploy.get("api_container", "docker-api-1")),
        retention_days=int(deploy.get("retention_days", 30)),
        dsl_path=str(dify.get("dsl_path")
                     or os.path.join(
                         REPO_ROOT, "dify", "Chatflow Basic (AgenticRAG Agent + PPT-Master).yml"
                     )),
    )


def redact(text: str, secrets: list[str]) -> str:
    out = text
    for secret in secrets:
        if secret:
            out = out.replace(secret, "***")
    return out
