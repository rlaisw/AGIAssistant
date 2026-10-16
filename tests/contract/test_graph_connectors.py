"""Graph connectors with mocked MSAL + Graph API (spec 001 auth tests, updated for the on-demand API)."""

import pytest
import respx
import httpx

from agentic_rag_mcp.errors import ProviderError, SourceAuthError
from agentic_rag_mcp.sources.onedrive import OneDriveSource, SharePointSource


class FakeAuth:
    def token(self):
        return "tok"


class ExpiredAuth:
    def token(self):
        raise SourceAuthError("expired")


@respx.mock
def test_onedrive_list_files_returns_metadata():
    """Listing returns file metadata (paginated children walk)."""
    respx.get("https://graph.microsoft.com/v1.0/me/drive/root/children").mock(
        return_value=httpx.Response(200, json={"value": [
            {"id": "1", "name": "report.docx", "file": {},
             "lastModifiedDateTime": "2026-10-01T00:00:00Z", "size": 500}]}))
    out = OneDriveSource(FakeAuth(), {}).list_files()
    assert out["files"][0]["title"] == "report.docx"
    assert out["files"][0]["embeddable"] is True


@respx.mock
def test_sharepoint_401_raises_auth_error():
    respx.get("https://graph.microsoft.com/v1.0/sites/s1/drive/root/children").mock(
        return_value=httpx.Response(401))
    with pytest.raises(SourceAuthError):
        SharePointSource(FakeAuth(), "s1").files()


def test_expired_token_propagates():
    with pytest.raises(SourceAuthError):
        OneDriveSource(ExpiredAuth(), {}).list_files()


@respx.mock
def test_network_error_is_provider_error():
    respx.get("https://graph.microsoft.com/v1.0/me/drive/root/children").mock(
        side_effect=httpx.ConnectError("down"))
    with pytest.raises(ProviderError):
        OneDriveSource(FakeAuth(), {}).list_files()
