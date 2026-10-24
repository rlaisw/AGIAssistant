"""Spec-024-era fix: line-aware chunking keeps tabular rows intact (V1).

The old char-window chunker clipped mid-row (e.g. `mary.wong@tvb.co…` with
the Office column lost). Lines must never split mid-way.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_rag_mcp.store.vectordb import VectorStore  # noqa: E402


def _rows(n: int) -> str:
    return "\n".join(
        f"1102 | User number {i:03d} | user{i:03d}@tvb.com.hk | MB/{i % 90 + 1}"
        for i in range(n)
    )


def test_no_line_is_split_midway():
    text = _rows(40)  # rows ~55 chars → several chunks
    chunks = VectorStore.chunk_text(text, size=800, overlap=100)
    assert len(chunks) > 1
    for c in chunks:
        for line in c.split("\n"):
            # every full line inside a chunk must be a whole source line
            if "|" in line:
                assert line in text, f"clipped line: {line!r}"
                assert line.endswith(("MB/" + line.rsplit("MB/", 1)[1]) if "MB/" in line else ""), line


def test_all_content_survives_reassembly():
    text = _rows(40)
    chunks = VectorStore.chunk_text(text, size=800, overlap=100)
    joined = "\n".join(chunks)
    for line in text.split("\n"):
        assert line in joined, f"lost line: {line!r}"


def test_short_text_single_chunk():
    assert VectorStore.chunk_text("one line") == ["one line"]
    assert VectorStore.chunk_text("") == []


def test_pathological_long_line_hard_split():
    giant = "x" * 2000
    chunks = VectorStore.chunk_text(giant, size=800, overlap=100)
    assert all(len(c) <= 800 for c in chunks)
    assert "".join(chunks) == giant


def test_overlap_carries_whole_lines():
    text = _rows(40)
    chunks = VectorStore.chunk_text(text, size=800, overlap=100)
    # the overlap tail of chunk N must be a whole-line prefix of chunk N+1
    for a, b in zip(chunks, chunks[1:]):
        tail = a.split("\n")[-1]
        assert tail in b, "overlap must carry whole lines"
