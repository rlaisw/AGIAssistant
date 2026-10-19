# AgenticRAG MCP sidecar for Dify.
# Build from the AgenticRAG repo ROOT (context must include pyproject.toml + src/):
#   docker build -f dify/docker/mcp-server/Dockerfile -t agentic-rag-mcp:latest .
# NOTE: ~6.7 GB — torch (via sentence-transformers) pulls CUDA wheels on both
#       arm64 and x86_64. For a much smaller image force CPU-only torch:
#       pip install --extra-index-url https://download.pytorch.org/whl/cpu .
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . uvicorn

# PPT-Master toolchain deps (spec 009): only the export path the bridge drives
# (project_manager / icon_sync / svg_quality_checker / svg_to_pptx).
# Deliberately excluded: PyMuPDF (AGPL, PDF sources unused) and the source
# converters (mammoth/openpyxl/edge-tts/flask/google-genai) — not on our path.
RUN pip install --no-cache-dir \
    "python-pptx>=0.6.21" \
    "XlsxWriter>=3.0.0" \
    "skia-pathops>=0.9.2" \
    "uharfbuzz>=0.50.0" \
    "PyYAML>=6.0"

# Bake the local embedding model so first-run answers are instant
# (all-MiniLM-L6-v2, ~90 MB; matches config default).
RUN python -c "from sentence_transformers import SentenceTransformer as S; S('all-MiniLM-L6-v2')"

COPY dify/docker/mcp-server/server.py ./server.py

EXPOSE 28080
CMD ["python", "server.py"]
