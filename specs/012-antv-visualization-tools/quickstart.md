# Quickstart — AntV Visualization Tools Validation Guide

Runnable end-to-end validation for spec 012. Prereq: the stack from DEPLOY.md deployed and verified (battery green).

## 1. Deploy

```bash
cd /kilocode/AGIAssistant
docker build -f dify/docker/mcp-server/Dockerfile -t agentic-rag-mcp:latest .
# recreate the container (the documented run with the ppt-master mount), then:
VENV=/home/administrator/.local/share/pipx/venvs/agentic-rag-mcp/bin/python
$VENV -m agentic_rag_mcp.deploy redeploy   # rebuild → recreate → health → tools re-sync (21 → 23)
$VENV -m agentic_rag_mcp.deploy chatflow    # republish chatflow with antv_* tools on both agent nodes
```

## 2. Automated battery

```bash
$VENV -m pytest tests/unit/test_antv_tools.py tests/integration/test_antv_pipeline.py \
  tests/contract/test_antv_contract.py -v
$VENV -m pytest            # full suite (existing + antv) green
$VENV -m agentic_rag_mcp.deploy verify   # battery incl. antv-chart, antv-infographic, chart-in-deck
```

Note: the live chart call requires outbound internet; on an air-gapped host the chart scenarios report honest failures (the service is external — see the data posture below).

## 3. End-to-end scenarios

| # | Do | Expect (maps to) |
|---|----|------------------|
| S1 | In the Chat UI: "show me monthly ticket volume for Q3 as a bar chart: Jan 120, Feb 150, Mar 90" | The answer contains a rendered chart image inline (Story 1 / SC-001/002) |
| S2 | "create a one-page deck about our Q3 volume with a chart" | The exported `.pptx` shows the chart on the slide; the file is self-contained (opens with no network) (Story 2 / SC-003) |
| S3 | "create an infographic of a 4-step onboarding process" | The answer links `…/infographics/<id>/` which opens the rendered infographic in the browser (Story 3) |
| S4 | "draw a district map of Guangdong" | Honest refusal naming the supported types (Story 4 / FR-003) |
| S5 | Stop outbound internet, then ask for a chart | The agent states the rendering service is unreachable — no fabricated image (FR-006) |
| S6 | Dify webapp: same chart prompt | Image renders in the webapp answer too (same markdown surface) |

## 4. Data posture (FR-009)

By default chart data travels to the AntV public rendering service (`https://antv-studio.alipay.com/api/gpt-vis`) and the returned image URL is hosted on its CDN — outbound internet required, chart data leaves the network. To render privately, deploy [GPT-Vis-SSR](https://github.com/antvis/GPT-Vis/tree/main/bindings/gpt-vis-ssr) and set `[antv] chart_service_url` in config.toml (geography types are not supported privately; they are excluded here regardless). Infographic syntax stays local — only the rendering engine script loads from CDN in the browser.
