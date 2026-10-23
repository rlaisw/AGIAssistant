# Data Model: Dedicated Documents Mount

No persistence changes — one deployment-owned volume mapping added to the
container spec.

## The volume mapping (the feature's only entity)

```text
MOUNTS entry: ("~/agentic-rag-docs", "/data/rag-docs")
  host:      /home/administrator/agentic-rag-docs/   (mkdir -p by the deploy CLI, operator-owned)
  container: /data/rag-docs                          (dot-free path — sidesteps the scanner's
                                                      hidden-dir limitation)
```

## The source registration (state.sqlite3, existing schema)

```text
type:  local_folder
config: { "path": "/data/rag-docs" }
```

One source; the 5-minute watcher and `sources_add`'s auto-sync keep the
index in step. A sqlite db in the same folder would register as its own
`sqlite` source pointing at the same container path (out of scope, spec
Clarifications).

## Removed

```text
- source registration pointing at /opt/ppt-master/rag-docs
- host folder ppt-master/rag-docs/ (after the PDF migrates)
```
