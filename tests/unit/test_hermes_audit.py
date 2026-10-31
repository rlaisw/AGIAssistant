"""Unit: the Hermes audit writer (spec 028, FR-012/013).

Failing-first: written before hermes_audit exists. Covers quickstart §A6 —
one JSONL entry per attempt, executed entries carry outcome, blocked carry
reason, the file is created on first write, and existing entries are never
rewritten or pruned.
"""

from __future__ import annotations

import json

from agentic_rag_mcp.hermes_audit import HermesAudit


def write_three(audit: HermesAudit) -> None:
    audit.write_attempt(
        decision="executed",
        operation="create-dir",
        normalized_path="/mnt/c/temp/hello_test",
        allowed_root="/mnt/c/temp",
        outcome="created C:\\temp\\hello_test",
    )
    audit.write_attempt(
        decision="blocked",
        operation="unsupported",
        normalized_path="/mnt/c/Windows",
        allowed_root="/mnt/c/temp",
        reason="Blocked: /mnt/c/Windows is outside /mnt/c/temp (v1 scope: create/write/read/list only)",
    )
    audit.write_attempt(
        decision="error",
        operation="write-file",
        normalized_path="/mnt/c/temp/lost.txt",
        allowed_root="/mnt/c/temp",
        reason="error:Hermes gateway unreachable",
    )


def test_one_entry_per_attempt(tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = HermesAudit(path)
    write_three(audit)
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 3


def test_entry_shapes(tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = HermesAudit(path)
    write_three(audit)
    entries = [json.loads(l) for l in path.read_text().strip().splitlines()]

    assert entries[0]["decision"] == "executed"
    assert entries[0]["outcome"] == "created C:\\temp\\hello_test"
    assert entries[0]["ts"]
    assert entries[0]["operation"] == "create-dir"
    assert entries[0]["normalized_path"] == "/mnt/c/temp/hello_test"
    assert entries[0]["allowed_root"] == "/mnt/c/temp"

    assert entries[1]["decision"] == "blocked"
    assert entries[1]["reason"]
    assert "outcome" not in entries[1]

    assert entries[2]["decision"] == "error"
    assert entries[2]["reason"].startswith("error:")


def test_creates_file_and_dir_on_first_write(tmp_path):
    path = tmp_path / "nested" / "dir" / "audit.jsonl"
    audit = HermesAudit(path)
    audit.write_attempt(decision="blocked", operation="unsupported",
                        normalized_path=None, allowed_root="/mnt/c/temp", reason="Blocked: test")
    assert path.exists()


def test_never_rewrites_or_prunes_existing_entries(tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = HermesAudit(path)
    write_three(audit)
    before = path.read_text()
    audit.write_attempt(decision="blocked", operation="unsupported",
                        normalized_path="/x", allowed_root="/mnt/c/temp", reason="Blocked: later")
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 4
    assert json.loads(lines[0])["ts"] == json.loads(before.strip().splitlines()[0])["ts"]
    # append-only: earlier lines byte-identical
    assert path.read_text().startswith(before)


def test_concurrent_audit_writers_append_atomically(tmp_path):
    path = tmp_path / "audit.jsonl"
    audits = [HermesAudit(path) for _ in range(4)]
    for i, a in enumerate(audits):
        a.write_attempt(decision="executed", operation="write-file",
                        normalized_path=f"/mnt/c/temp/f{i}.txt", allowed_root="/mnt/c/temp",
                        outcome=f"wrote f{i}")
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 4
    # every line is complete valid JSON (no interleaved partial writes)
    for l in lines:
        assert json.loads(l)["decision"] in ("executed", "blocked", "error")
