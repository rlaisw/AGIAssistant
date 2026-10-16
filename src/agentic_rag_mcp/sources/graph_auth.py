"""MSAL helper for per-user delegated Microsoft Graph auth (clarification Q4)."""

from __future__ import annotations

from pathlib import Path

from ..errors import SourceAuthError

# MSAL automatically requests profile/openid/offline_access for public clients
# (refresh tokens come back without asking); passing any of them explicitly makes
# initiate_device_flow raise "You cannot use any scope value that is reserved".
# Files.Read (delegated) is the minimal scope for OneDrive /me/drive access —
# Sites.Read.All was trimmed: it needs a Delegated grant the app doesn't carry,
# and spec 007 limits scope to the user's own drive (shared-with-me excluded).
SCOPES = ["Files.Read"]


class GraphAuth:
    def __init__(self, client_id: str, cache_path: Path, tenant_id: str = "common") -> None:
        import msal

        self._cache = msal.SerializableTokenCache()
        self._cache_path = cache_path
        if cache_path.exists():
            self._cache.deserialize(cache_path.read_text())
        # single-tenant apps MUST use their own tenant authority — "common"
        # fails device-flow initiation for them (AADSTS: app not found in directory)
        self._app = msal.PublicClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            token_cache=self._cache,
        )

    def _persist(self) -> None:
        if self._cache.has_state_changed:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.write_text(self._cache.serialize())

    def token(self) -> str:
        accounts = self._app.get_accounts()
        result = None
        if accounts:
            result = self._app.acquire_token_silent(SCOPES, account=accounts[0])
        if not result:
            raise SourceAuthError(
                "Microsoft sign-in required", context={"action": "run device sign-in"}
            )
        self._persist()
        return result["access_token"]

    def begin_device_flow(self) -> dict:
        """Initiate the device flow ONCE — the caller relays user_code/URL to the
        user and passes this same flow to device_sign_in(flow) to complete it.
        (Live-found bug 2026-10-12: initiating twice made the user complete an
        unpolled flow while the thread polled a code nobody ever entered.)"""
        flow = self._app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            # MSAL returns error/error_description when initiation fails — surface it
            # honestly instead of a generic "failed to start" (live-found gap 2026-10-11)
            detail = flow.get("error_description") or flow.get("error") or "no user_code issued"
            raise SourceAuthError(f"device flow failed to start: {detail}")
        return flow

    def device_sign_in(self, flow: dict | None = None) -> dict:
        """Complete the given device flow (or initiate one if none passed) and
        cache the token. sources_auth passes the flow whose code the user saw."""
        flow = flow or self.begin_device_flow()
        result = self._app.acquire_token_by_device_flow(flow)
        if "access_token" not in result:
            raise SourceAuthError("sign-in incomplete", context=result.get("error_description", {}))
        self._persist()
        return {"ok": True}


class ClientCredentialsAuth:
    """App-only auth via client secret (no user sign-in). Requires
    Files.Read.All APPLICATION permission on the Azure app registration."""

    def __init__(self, client_id: str, client_secret: str, tenant_id: str) -> None:
        import msal
        self._app = msal.ConfidentialClientApplication(
            client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )
        self._token: str | None = None
        self._expires: float = 0.0

    def token(self) -> str:
        import time
        if self._token and time.time() < self._expires:
            return self._token
        result = self._app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in result:
            desc = result.get("error_description", result.get("error", "unknown"))
            raise SourceAuthError(f"client credentials failed: {desc}")
        self._token = result["access_token"]
        self._expires = time.time() + result.get("expires_in", 3600) - 300  # refresh 5min early
        return self._token
