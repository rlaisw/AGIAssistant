# Quickstart: Application Log File with Leveled Logging

**Feature**: `specs/008-app-logging`

Validates the feature end-to-end, including the error paths. Automated suite first (no live system needed), then a short live check on the running sidecar.

## Prerequisites

- Python 3.12 env with deps installed (`pip install -e ".[dev]"`)
- (Live check only) the Docker sidecar running

## 1. Automated validation (CI-grade)

```bash
pytest tests/unit/test_logging_setup.py tests/contract/test_logging_contract.py \
       tests/integration/test_logging_integration.py -q
```

Expected: all green — the [contract test matrix](contracts/logging.md) (C1–C2, U1–U7, I1–I4, X1), including the error paths: invalid level → honest WARN + default; unwritable log path → server still starts console-only with `status.logging.writable=false`; rotation bounds; redaction of bearer tokens/secrets/download URLs at every level; INFO-scan proving no question text or file names above DEBUG.

Regression gate (existing suites untouched — the state_db-derived log path is what keeps them isolated):

```bash
pytest -q
```

## 2. Live check (running sidecar)

1. **Default INFO**: `docker exec agentic-rag tail -5 /root/.config/agentic-rag-mcp/logs/server.log` — startup, watcher cycle, and request lines present at INFO; ask a question in the Dify chat, then verify the INFO record names the operation and outcome but **not** your question text.
2. **status exposure**: ask the Dify agent "what is the log level?" — it answers from `status.logging` (level INFO, file path, writable true).
3. **DEBUG session**: set `LOG_LEVEL=DEBUG` in the container environment (or `level = "DEBUG"` in config.toml) and recreate the sidecar; repeat a question and read the file — the full trace appears (tool entry with your question → routing decision → hit counts → freshness probe → completion). Restore INFO afterward.
4. **Error path demo**: point `[logging] log_file` at an unwritable path and restart — the server comes up, an ERROR record explains the fallback on the console, `status` reports `writable: false`, and everything else keeps working.
5. **Rotation sanity**: leave defaults running — after sustained operation the directory holds at most `server.log` + 5 rotations (~50 MB ceiling).
6. **Failure logging**: attempt to embed a nonexistent OneDrive path — the per-file `not_found` outcome in the tool response has a matching WARN/ERROR record with the same reason.

## Expected outcomes summary

| Step | Observable result |
|---|---|
| Any operation | UTC-timestamped, leveled, component-named record in the persistent file (+ console mirror) |
| Working-as-expected ops | INFO records with counts/outcomes — no user text |
| Failures | WARN/ERROR with reasons — never silent |
| DEBUG enabled | one-question end-to-end trace readable from the file |
| Credentials | never on disk or console at any level |
| Log disk | bounded by rotation |
| `status` | reports level, file, writability |
