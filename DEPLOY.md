# AgenticRAG — Fresh-Host Deployment Runbook

From `git clone` to a verified MCP sidecar (optionally wired into Dify) on any new host.
The same content ships as the `agenticrag-deploy` skill (`~/.config/kilo/skills/agenticrag-deploy/SKILL.md`).

Runtime state lives OUTSIDE this repo in `~/.config/agentic-rag-mcp/` — a fresh
clone has no config, no LanceDB data, no model checkpoints. Everything below
recreates them.

**Port convention (memorize)**: avoid the crowded common ports on the HOST —
use **28080** for the AgenticRAG sidecar and **28888** for SearXNG. Container ports are
aligned: the number you see IS the port everywhere (host = container). Full topology: [`docs/NETWORK.md`](docs/NETWORK.md).

## Step 0 — Prerequisites (verify before starting)

```bash
git --version && docker --version && python3 --version   # need Python 3.12+
pipx --version || python3 -m pip install --user pipx
df -h ~ | tail -1    # need ~4 GB disk (models) and ~2.5 GB free RAM for the sidecar
```

## Step 1 — Install and initialize

```bash
git clone https://github.com/rlaisw/AgenticRAG.git
pipx install -e AgenticRAG
agentic-rag-mcp --init        # writes ~/.config/agentic-rag-mcp/config.toml (defaults)
```

First use auto-downloads to `~/.cache/huggingface/`: embedding model (~90 MB)
and the Laya decision model (~1.7 GB, ~2 GB RAM loaded). The server pre-loads
it in the background at startup — a first ask before the load finishes falls
back gracefully (provenance: "fallback").

## Step 2 — Tune config for THIS host

Edit `~/.config/agentic-rag-mcp/config.toml`:

```toml
[decider]
timeout = 12.0   # MUST exceed measured warm decision latency on this host.
                 # ~140 ms on Apple Silicon; ~7.4 s on a small ARM cloud CPU.

[web.searxng]
url = "http://searxng:28888"   # container-to-container via Docker DNS (Step 5);
                              # the host port 28888 is NOT used here.
```

Measure the decision latency after the model downloads (Step 6 below), then
set `timeout` comfortably above it.

## Step 3 — Build and run the sidecar

```bash
docker build -f AgenticRAG/dify/docker/mcp-server/Dockerfile -t agentic-rag-mcp:latest AgenticRAG
docker run -d --name agentic-rag \
  --network <DIFY_NETWORK> \
  -v ~/.config/agentic-rag-mcp:/root/.config/agentic-rag-mcp \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 28080:28080 \
  -e LOG_LEVEL=INFO \
  --restart always \
  agentic-rag-mcp:latest
```

Logs (spec 008): the server writes a persistent leveled log to
`~/.config/agentic-rag-mcp/logs/server.log` — the mounted volume, so history
survives container recreation. `LOG_LEVEL` (or `[logging] level` in
config.toml) sets the level: INFO for working-as-expected events, DEBUG for
full developer traces; rotation caps the file at `rotation_size_mb ×
rotation_count` (default 10 MB × 5). Frame request lines and application
records land in the same file.

Port rule: the sidecar binds **28080** inside the container, so `-p 28080:28080`
maps HOST 28080 → CONTAINER 28080 (aligned). Host checks use `localhost:28080`;
containers on the Docker network use `agentic-rag:28080`.

## Step 4 — Dify integration (only if this host runs Dify)

1. Find the network names (they differ per compose project): `docker network ls`
   — on the reference host: `docker_default`, `docker_ssrf_proxy_network`.
   Join the sidecar to both (`docker network connect <net> agentic-rag`).
2. **SSRF allowlist (without this Dify shows "Cannot connect to MCP server")**:
   in the Dify compose `.env` add
   `SSRF_PROXY_ALLOW_PRIVATE_DOMAINS=agentic-rag`, then `docker compose up -d ssrf_proxy`.
3. Dify UI → Tools → MCP → Add Server: `http://agentic-rag:28080/mcp`
   (container DNS name + the aligned container port 28080; never `localhost`),
   no headers, no Dynamic Client Registration.
4. Import the chatflow: `AgenticRAG/dify/Chatflow Basic (AgenticRAG Agent).yml`
   (Studio → Import DSL). Re-select tools in the Agent node if they don't resolve.
5. Rules learned the hard way:
   - Never `localhost`/`127.0.0.1` in the Dify UI — Docker DNS name only.
   - To CHANGE a server: delete + re-add (Dify 1.17's edit path 500s on save).
   - When the server gains/removes tools: refresh Dify's cache (Tools → MCP →
     server → Update), or the agent reports "Tool with name X not found".

## Step 5 — SearXNG (only if web_search is wanted)

The stock image ships WITHOUT the JSON API enabled — the AgenticRAG provider
uses `format=json`, so create the settings first:

```bash
mkdir -p ~/searxng && cat > ~/searxng/settings.yml <<'EOF'
use_default_settings: true
server:
  secret_key: "change-me-to-a-random-string"
  limiter: false
search:
  formats:
    - html
    - json
EOF

docker run -d --name searxng \
  -v ~/searxng:/etc/searxng \
  -p 28888:28888 \
  --restart unless-stopped \
  searxng/searxng
docker network connect <DIFY_NETWORK> searxng
```

Verify: `curl -s "http://localhost:28888/search?q=test&format=json" -o /dev/null -w "%{http_code}"`
→ must be 200 (403 = JSON not enabled). The sidecar reaches SearXNG via
`http://searxng:28888` inside the Docker network — the host port is only for
your testing. First query after container recreation is slow (engines warm up).

## Step 6 — Ingest sources (LanceDB starts empty)

Mount host folders into the sidecar first (container-visible paths only), then
via any MCP client or curl: `sources_add {"type": "local_folder", "config":
{"path": "/data/your-docs"}}`. Auto-update: the watcher re-syncs every 5
minutes; `sources_sync` for instant. Verify with `sources_list` → `healthy`.

## OneDrive (on-demand) setup

OneDrive sources are **on-demand** (spec 007): connection ingests zero files;
you browse metadata and embed only the files you explicitly confirm. The
watcher never touches OneDrive.

**Azure app registration (one-time):**

1. Register an app in Entra ID; note the **client_id**
2. Add delegated permission **`Files.Read`** (Microsoft Graph) and grant consent
   — that is the only permission needed; `offline_access` is requested by MSAL
   automatically (never pass it explicitly — MSAL rejects reserved scopes)
3. If the app is **single-tenant**, note the **tenant_id** — it MUST be passed
   at `sources_add` (a `common` authority cannot see single-tenant apps, and
   the device flow will fail to start)
4. Optional app-only path: `client_secret` + **application** `Files.Read.All`
   requires a target `user` (UPN) in the config; the delegated device flow
   above is the normal path and needs no secret

**Connect (via the Dify chat or any MCP client):**

```
sources_add {"type": "onedrive", "config": {"client_id": "<id>", "tenant_id": "<tenant>"}}
sources_auth {"source_id": "<id>"}     → returns sign_in_url + user_code
```

Visit https://login.microsoft.com/device, enter the code, sign in with the
account that owns the OneDrive — complete ALL steps to "You may now close
this window". The connection completes automatically within seconds (the
background thread completes the same flow whose code you entered).

**Then:** `onedrive_list_files` to browse (nothing downloads), confirm the
matches, `onedrive_embed_files` for exactly the confirmed files. Answers citing
a cloud-changed file carry a staleness reminder; re-embedding is always your
explicit command.

## Step 6b — Specialty search profiles (optional, for domain-scoped questions)

Create `~/.config/agentic-rag-mcp/specialty_profiles.json` with your domain profiles:

```bash
cat > ~/.config/agentic-rag-mcp/specialty_profiles.json <<'EOF2'
{
  "microsoft": {
    "sites": ["learn.microsoft.com", "techcommunity.microsoft.com"],
    "description": "Microsoft product documentation and community"
  },
  "huawei": {
    "sites": ["support.huawei.com", "forum.huawei.com"],
    "description": "Huawei networking and enterprise products"
  }
}
EOF2
```

Hot-reloaded: edit the file at any time — new profiles are usable on the very
next search call, no restart needed. The Dify agent calls `specialty_profiles()`
first to discover available topics, then picks the right profile for the question.

## Step 7 — Verify (the 5-minute battery)

```bash
curl -s localhost:28080/healthz                                  # {"status": "ok"}
curl -s -X POST localhost:28080/mcp -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'   # 16 tools
# then exercise: status, search, ask, sources_list, sources_add/sync/remove,
# web_search (live), fetch_url (live), graph_query (honest disabled error)
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Dify: "Cannot connect to MCP server" | SSRF proxy blocks private targets | Step 4.2 allowlist + restart ssrf_proxy |
| `agentic-rag:28080` refused from a container | Wrong path | Container-to-container port = host port (aligned) |
| `localhost:8080` refused on host (old port, now gone) | Old port freed by alignment | Use `localhost:28080` |
| Dify save/edit of MCP server → 500 | Dify identifier-vs-UUID bug | Delete the entry, re-add |
| Every decision is `provenance: "fallback"` | timeout too small for this host | Raise `[decider] timeout` above measured latency |
| `web_search` returns empty | No SearXNG / JSON disabled / not on network | Step 5 (settings.yml + network + 200 check) |
| SearXNG JSON returns 403 | `formats` missing json | Add `- json` to settings.yml, restart container |
| Tool not found after server update | Dify's cached tool list is stale | Update tools in Dify's MCP page |
| Sidecar OOM-killed / host low on RAM | Decision model ~2 GB resident | `[decider] enabled = false` + restart = instant relief |
| Edited file's changes don't appear in answers | Wait for the 5-min watcher cycle or run `sources_sync` | Auto-update replaces old chunks (eviction fix, commit 5c9b4ae) |
| OneDrive device flow fails to start | Single-tenant app + `common` authority, or a reserved scope passed explicitly | Pass the real `tenant_id` at `sources_add`; never include `offline_access`/`profile`/`openid` in scopes — MSAL adds them internally |
| Device sign-in stays "pending" forever | Browser flow not completed (or code expired after 15 min) | Re-run `sources_auth`, complete ALL browser steps to "You may now close this window" — the background thread completes the same flow whose code you entered |
| No DEBUG detail in the log file | Level is INFO | `-e LOG_LEVEL=DEBUG` + recreate; confirm via `status` → `logging.level` |
