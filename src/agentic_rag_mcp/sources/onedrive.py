"""OneDrive source: on-demand connector (spec 007; research.md D1/D2/D4).

Metadata-only listing (recursive children traversal, paginated, filterable),
one-call file resolution, freshness probe, download. The superseded delta-sync
machinery is deleted (Constitution V / FR-015).
"""

from __future__ import annotations

import httpx

from ..errors import ProviderError, SourceAuthError

GRAPH = "https://graph.microsoft.com/v1.0"
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx"}
LIST_SELECT = "id,name,size,file,lastModifiedDateTime"


class GraphBase:
    type = "graph"

    def __init__(self, auth) -> None:
        self._auth = auth

    def _get(self, url: str, params: dict | None = None) -> dict:
        """GET with auth token, following @odata.nextLink pagination."""
        items: list[dict] = []
        next_url = f"{GRAPH}{url}"
        first = True
        while next_url:
            if first:
                resp = self._request(next_url, params)
                first = False
            else:
                resp = self._request(next_url, None)
            items.extend(resp.get("value", []))
            next_url = resp.get("@odata.nextLink")
        return {"items": items}

    def _request(self, url: str, params: dict | None, allow_404: bool = False,
                 timeout: float = 30.0) -> dict | None:
        try:
            token = self._auth.token()
        except SourceAuthError:  # noqa: TRY203 — deliberate: must not become ProviderError
            raise
        try:
            resp = httpx.get(url, headers={"Authorization": f"Bearer {token}"},
                             params=params or {}, timeout=timeout)
            if resp.status_code in (401, 403):
                raise SourceAuthError(f"graph auth failed: {resp.status_code}")
            if resp.status_code == 429:
                raise ProviderError("graph rate limited (429) — retry this file")
            if allow_404 and resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except SourceAuthError:
            raise
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"graph request failed: {exc}") from exc


class OneDriveSource(GraphBase):
    type = "onedrive"

    def __init__(self, auth, config: dict) -> None:
        super().__init__(auth)
        self._config = config

    # ---- helpers ---------------------------------------------------------

    def _prefix(self) -> str:
        user = self._config.get("user", "")
        return f"/users/{user}" if user else "/me"

    def _max_bytes(self) -> int:
        return self._config.get("max_file_size_mb", 50) * 1024 * 1024

    def _entry(self, item: dict, folder: str) -> dict:
        name = item.get("name", "")
        ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
        size = item.get("size", 0)
        path = f"{folder.rstrip('/')}/{name}" if folder != "/" else f"/{name}"
        return {
            "locator": item["id"],
            "title": name,
            "path": path,
            "size": size,
            "last_modified": item.get("lastModifiedDateTime", ""),
            "embeddable": ext in SUPPORTED_EXTENSIONS and size <= self._max_bytes(),
        }

    # ---- U1: metadata-only listing (FR-005, research.md D1) -----------------

    def list_files(self, search: str = "", folder: str | None = None, limit: int = 100) -> dict:
        """Recursive metadata-only listing from the folder scope root.
        Returns {files: [FileListingEntry], truncated: bool}. Never downloads content."""
        root = folder or self._config.get("folder_path", "/") or "/"
        files: list[dict] = []
        self._walk(root, search, files)
        # ponytail: collects all metadata then slices — fine at single-user drive
        # scale; stream+early-stop if a huge drive makes this slow
        truncated = len(files) > limit
        return {"files": files[:limit], "truncated": truncated}

    def _walk(self, folder: str, search: str, out: list[dict]) -> None:
        url = (f"{self._prefix()}/drive/root/children" if folder == "/"
               else f"{self._prefix()}/drive/root:{folder}:/children")
        result = self._get(url, params={"$select": LIST_SELECT})
        for item in result["items"]:
            if "folder" in item:
                if self._config.get("include_subfolders", True):
                    self._walk(self._entry(item, folder)["path"], search, out)
                continue
            if "file" not in item:
                continue
            if search and search.lower() not in item.get("name", "").lower():
                continue
            out.append(self._entry(item, folder))

    # ---- U2: one-call resolution + probe (FR-006/010, research.md D2/D4) ---

    def resolve(self, path_or_id: str) -> dict | None:
        """One Graph call per file: paths ('/' or '.') via root:{path}, bare ids
        via /items/{id}. None on 404 — the caller reports honest not_found."""
        if "/" in path_or_id or "." in path_or_id:
            url = f"{self._prefix()}/drive/root:{path_or_id}"
        else:
            url = f"{self._prefix()}/drive/items/{path_or_id}"
        item = self._request(f"{GRAPH}{url}", None, allow_404=True)
        if not item:
            return None
        name = item.get("name", "")
        return {
            "locator": item["id"],
            "title": name,
            "size": item.get("size", 0),
            "last_modified": item.get("lastModifiedDateTime", ""),
            "download_url": item.get("@microsoft.graph.downloadUrl"),
            "ext": name.rsplit(".", 1)[-1].lower() if "." in name else "",
        }

    def get_metadata(self, item_id: str) -> dict | None:
        """Freshness probe (FR-010): metadata only; None on 404 = genuinely deleted
        (item-id identity survives renames — research.md D4). Short timeout: the
        probe runs inside the answer's 5-second budget."""
        item = self._request(f"{GRAPH}{self._prefix()}/drive/items/{item_id}",
                             {"$select": "id,name,lastModifiedDateTime,eTag,parentReference"},
                             allow_404=True, timeout=4.0)
        if not item:
            return None
        path = None
        parent = (item.get("parentReference") or {}).get("path", "")
        if parent:  # "/drive/root:/Documents" → "/Documents/report.docx"
            base = parent.split(":", 1)[-1] or "/"
            path = f"{base.rstrip('/')}/{item.get('name', '')}"
        return {"locator": item_id, "title": item.get("name", ""), "path": path,
                "last_modified": item.get("lastModifiedDateTime", ""),
                "etag": item.get("eTag")}

    @staticmethod
    def download(download_url: str, timeout: float = 60.0) -> bytes:
        """Download a file via its pre-authenticated Graph downloadUrl."""
        try:
            resp = httpx.get(download_url, timeout=timeout, follow_redirects=True)
            resp.raise_for_status()
            return resp.content
        except Exception as exc:
            raise ProviderError(f"download failed: {exc}") from exc


class SharePointSource(GraphBase):
    type = "sharepoint"

    def __init__(self, auth, site_id: str) -> None:
        super().__init__(auth)
        self.site_id = site_id

    def files(self) -> list[dict]:
        result = self._get(f"/sites/{self.site_id}/drive/root/children")
        return [
            {
                "locator": item["id"],
                "title": item["name"],
                "download_url": item.get("@microsoft.graph.downloadUrl"),
            }
            for item in result["items"]
            if "file" in item
        ]
