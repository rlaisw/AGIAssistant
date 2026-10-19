"""Integration: DifyConsole client against a fake console server (spec 011, P06-P10).

Mirrors the real console's auth: cookie-based tokens + X-CSRF-Token header,
base64-encoded login password, hash-guarded draft updates.
"""

from __future__ import annotations

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from agentic_rag_mcp.deploy.config import DeployConfig
from agentic_rag_mcp.deploy.dify_console import ConsoleError, DifyConsole


class FakeConsole:
    def __init__(self):
        self.requests: list[tuple[str, str, dict | None]] = []
        self.providers: list[dict] = []
        self.apps: list[dict] = [{"id": "11111111-aaaa-bbbb-cccc-000000000001",
                                   "name": "Chatflow Basic (AgenticRAG Agent)"}]
        self.draft_hash = "hash-1"
        self.server = HTTPServer(("127.0.0.1", 0), self._handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def _handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):  # silence
                pass

            def _send(self, code, body, cookies=None):
                data = json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                for name, value in (cookies or {}).items():
                    self.send_header("Set-Cookie", f"{name}={value}; Path=/")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _authed(self) -> bool:
                if "access_token=tok-1" not in self.headers.get("Cookie", ""):
                    self._send(401, {"code": "unauthorized"})
                    return False
                return True

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                outer.requests.append(("POST", self.path, body))
                if self.path == "/console/api/login":
                    email, password = body.get("email"), body.get("password")
                    decoded = base64.b64decode(password).decode() if password else ""
                    if email == "good@x" and decoded == "pw":
                        self._send(200, {"result": "success", "data": None},
                                   cookies={"access_token": "tok-1",
                                            "csrf_token": "csrf-1"})
                    else:
                        self._send(401, {"code": "authentication_failed"})
                    return
                if not self._authed():
                    return
                if self.path == "/console/api/workspaces/current/tool-provider/mcp":
                    outer.providers.append(body)
                    self._send(200, {"data": [{"name": body["name"]}]})
                elif self.path == "/console/api/apps/imports":
                    self._send(200, {"app_id": "22222222-aaaa-bbbb-cccc-000000000002"})
                elif self.path.startswith("/console/api/apps/") and self.path.endswith("/workflows/draft"):
                    if body.get("hash") != outer.draft_hash:
                        self._send(409, {"code": "draft_workflow_not_sync"})
                    else:
                        self._send(200, {"result": "success"})
                elif self.path.endswith("/workflows/publish"):
                    self._send(200, {"result": "success"})
                else:
                    self._send(404, {})

            def do_GET(self):
                outer.requests.append(("GET", self.path, None))
                path = self.path.split("?")[0]
                if path == "/console/api/apps/11111111-aaaa-bbbb-cccc-000000000001/workflows/draft":
                    if not self._authed():
                        return
                    self._send(200, {"hash": outer.draft_hash, "graph": {}})
                    return
                if not self._authed():
                    return
                if path == "/console/api/workspaces/current/tool-providers":
                    self._send(200, {"data": outer.providers})
                elif path.startswith("/console/api/apps"):
                    self._send(200, {"data": outer.apps})
                else:
                    self._send(404, {})

        return Handler

    @property
    def url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.server.shutdown()


@pytest.fixture
def fake_console():
    fc = FakeConsole().start()
    yield fc
    fc.stop()


def dcfg_for(fake_console) -> DeployConfig:
    return DeployConfig(console_url=fake_console.url,
                        console_email="good@x", console_password="pw")


def test_login_success_and_401(fake_console):
    console = DifyConsole(dcfg_for(fake_console))
    assert console.login() == "tok-1"
    bad = DifyConsole(DeployConfig(console_url=fake_console.url,
                                   console_email="wrong@x", console_password="nope"))
    with pytest.raises(ConsoleError, match="login failed"):
        bad.login()


def test_provider_absent_creates_with_documented_fields(fake_console):
    console = DifyConsole(dcfg_for(fake_console))
    console.login()
    console.create_mcp_provider("agentic-rag", "http://agentic-rag:28080/mcp")
    post = next(r for r in fake_console.requests
                if r[0] == "POST" and r[1].endswith("/tool-provider/mcp"))
    body = post[2]
    assert body["server_url"] == "http://agentic-rag:28080/mcp"
    assert body["name"] == "agentic-rag"
    assert body["server_identifier"] == "agentic-rag"
    assert body["icon_type"] == "emoji"


def test_provider_present_no_duplicate_create(fake_console):
    console = DifyConsole(dcfg_for(fake_console))
    console.login()
    fake_console.providers = [{"name": "agentic-rag"}]
    providers = console.list_mcp_providers()
    assert any(p["name"] == "agentic-rag" for p in providers)
    creates = [r for r in fake_console.requests
               if r[0] == "POST" and r[1].endswith("/tool-provider/mcp")]
    assert creates == []  # present → the caller re-syncs instead of creating


def test_app_exists_draft_updates_no_import(fake_console):
    console = DifyConsole(dcfg_for(fake_console))
    console.login()
    app = console.find_app("Chatflow Basic (AgenticRAG Agent)")
    assert app is not None
    console.update_workflow_draft(app["id"], {"graph": {"nodes": []}})
    imports = [r for r in fake_console.requests
               if r[0] == "POST" and r[1].endswith("/apps/imports")]
    assert imports == []  # in-place, no import
    drafts = [r for r in fake_console.requests
              if r[0] == "POST" and r[1].endswith("/workflows/draft")]
    assert drafts and drafts[0][2]["hash"] == "hash-1"  # optimistic concurrency honored


def test_app_absent_imports_and_publishes(fake_console):
    console = DifyConsole(dcfg_for(fake_console))
    console.login()
    assert console.find_app("No Such App") is None
    app_id = console.import_app("app: x")
    console.publish(app_id)
    assert app_id.startswith("22222222")
    paths = [r[1] for r in fake_console.requests]
    assert any(p.endswith("/apps/imports") for p in paths)
    assert any(p.endswith("/workflows/publish") for p in paths)
