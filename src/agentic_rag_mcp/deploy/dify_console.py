"""Dify console client: login, MCP provider lifecycle, chatflow import/update/publish (spec 011, R2/R3/R4)."""

from __future__ import annotations

import httpx

from .config import DeployConfig


class ConsoleError(Exception):
    pass


class DifyConsole:
    def __init__(self, dcfg: DeployConfig) -> None:
        self.dcfg = dcfg
        self.base = dcfg.console_url.rstrip("/") + "/console/api"
        self.client = httpx.Client(timeout=60)

    def login(self) -> str:
        import base64

        resp = self.client.post(
            f"{self.base}/login",
            json={"email": self.dcfg.console_email,
                  "password": base64.b64encode(
                      self.dcfg.console_password.encode()).decode()},
        )
        if resp.status_code != 200:
            raise ConsoleError(
                f"console login failed ({resp.status_code}): check [dify] "
                "console_email/console_password"
            )
        token = resp.cookies.get("access_token")
        if not token:
            raise ConsoleError("console login returned no access token")
        self._csrf = resp.cookies.get("csrf_token") or ""
        return token

    def _headers(self) -> dict:
        return {"X-CSRF-Token": self._csrf} if self._csrf else {}

    def _get(self, path: str, **kw):
        resp = self.client.get(f"{self.base}{path}", headers=self._headers(), **kw)
        if resp.status_code == 401:
            raise ConsoleError("console request unauthorized (401)")
        if resp.status_code != 200:
            raise ConsoleError(f"{path} failed ({resp.status_code})")
        return resp.json()

    def _post(self, path: str, payload: dict, ok_codes=(200, 201)):
        resp = self.client.post(f"{self.base}{path}", headers=self._headers(),
                                json=payload)
        if resp.status_code == 401:
            raise ConsoleError(f"console request unauthorized (401) at {path}")
        if resp.status_code not in ok_codes:
            raise ConsoleError(f"{path} failed ({resp.status_code}): {resp.text[:200]}")
        return resp.json()

    def list_mcp_providers(self) -> list[dict]:
        body = self._get("/workspaces/current/tool-providers", params={"type": "mcp"})
        items = body.get("data") if isinstance(body, dict) else body or []
        return [p for p in items if p.get("type", "mcp") == "mcp"]

    def create_mcp_provider(self, name: str, server_url: str) -> dict:
        return self._post(
            "/workspaces/current/tool-provider/mcp",
            {
                "server_url": server_url,
                "name": name,
                "icon": "🧩",
                "icon_type": "emoji",
                "icon_background": "#EFF1F5",
                "server_identifier": name,
            },
        )

    def find_app(self, name: str) -> dict | None:
        body = self._get("/apps", params={"page": 1, "limit": 100})
        for app in body.get("data", []):
            if app.get("name") == name:
                return app
        return None

    def import_app(self, yaml_content: str) -> str:
        body = self._post("/apps/imports",
                          {"mode": "yaml-dsl", "yaml_content": yaml_content})
        app_id = (body.get("app_id") or body.get("imported_app_id")
                  or (body.get("data") or {}).get("app_id"))
        if not app_id:
            raise ConsoleError(f"app import returned no app id: {str(body)[:200]}")
        return app_id

    def update_workflow_draft(self, app_id: str, workflow: dict) -> None:
        current = self._get(f"/apps/{app_id}/workflows/draft")
        self._post(
            f"/apps/{app_id}/workflows/draft",
            {
                "hash": current.get("hash"),
                "graph": workflow.get("graph", {}),
                "features": workflow.get("features", {}),
                "conversation_variables": workflow.get("conversation_variables", []),
            },
        )

    def publish(self, app_id: str) -> None:
        self._post(f"/apps/{app_id}/workflows/publish", {})
