"""Ollama model-provider setup in Dify (spec 025, "AI LLM" dropdown).

Installs the marketplace Ollama plugin when absent, saves the provider
credential (docker-bridge base URL), and registers the local no-think model
as a custom LLM so the chatflow's local branch nodes can use it. Idempotent:
safe to rerun on every deploy.
"""

from __future__ import annotations

import time

# Resolved from marketplace.dify.ai at implementation time (spec 025, T006).
OLLAMA_PLUGIN_IDENTIFIER = (
    "langgenius/ollama:1.0.3@1086758302d98263d5b7881de8ba95fc219351fdf97831d18a7807378674d203"
)
OLLAMA_PLUGIN_ID = "langgenius/ollama"
OLLAMA_PROVIDER = "langgenius/ollama/ollama"
OPENROUTER_PROVIDER = "langgenius/openrouter/openrouter"
# spec 025 grouped-menu: additional cloud models selectable in the Chat UI.
# moonshotai/kimi-k3 is preset in the provider catalog; these two are not.
# (model_id, context_size, max_tokens_to_sample)
OPENROUTER_CUSTOM_MODELS = (
    ("z-ai/glm-5.3-flash", "1048576", "943717"),
    ("qwen/qwen3.8-flash", "1000000", "131072"),
)


def _find_task_id(body: dict) -> str | None:
    for source in (body, body.get("data") or {}):
        for key in ("task_id", "taskId"):
            value = source.get(key) if isinstance(source, dict) else None
            if isinstance(value, str) and value:
                return value
    return None


def _wait_task(console, task_id: str, timeout_s: int = 300) -> str:
    deadline = time.monotonic() + timeout_s
    last = "unknown"
    while time.monotonic() < deadline:
        body = console.plugin_task(task_id)
        status = str(body.get("status", body.get("state", ""))).lower()
        last = status or last
        if status in {"succeeded", "success", "done", "finished"}:
            return status
        if status in {"failed", "error"}:
            raise RuntimeError(f"plugin install task {task_id} failed: {str(body)[:200]}")
        time.sleep(2)
    raise RuntimeError(f"plugin install task {task_id} timed out (last status: {last})")


def setup_models(dcfg, report) -> None:
    from .dify_console import DifyConsole

    console = DifyConsole(dcfg)
    console.login()
    report.add("console-login", evidence="ok")

    plugins = console.list_plugins()
    if any(p.get("plugin_id") == OLLAMA_PLUGIN_ID for p in plugins):
        report.add("ollama-plugin", evidence="already installed")
    else:
        task = console.install_marketplace_plugins([OLLAMA_PLUGIN_IDENTIFIER])
        plugins = console.list_plugins()
        if any(p.get("plugin_id") == OLLAMA_PLUGIN_ID for p in plugins):
            report.add("ollama-plugin", evidence="installed")
        else:
            task_id = _find_task_id(task)
            if not task_id:
                raise RuntimeError(
                    f"install returned no task and plugin absent: {str(task)[:200]}"
                )
            status = _wait_task(console, task_id)
            report.add("ollama-plugin",
                       evidence=f"installed via task {task_id} ({status})")

    # ollama 1.0.3 is a custom-model-only provider: no provider credential
    # schema — each model is registered with its own base_url credential.
    try:
        console.save_model_credentials(
            OLLAMA_PROVIDER,
            dcfg.ollama_model,
            "llm",
            {"base_url": dcfg.ollama_base_url, "model_name": dcfg.ollama_model,
             "mode": "chat", "context_size": "40960", "max_tokens": "40960",
             # without this Dify never offers the model tools (spec 026 follow-up)
             "function_call_support": "true"},
        )
        report.add("ollama-model", evidence=f"registered llm {dcfg.ollama_model}")
    except Exception as exc:  # noqa: BLE001 — idempotency boundary
        models = console.list_provider_models(OLLAMA_PROVIDER)
        names = sorted(str(m.get("model")) for m in models)
        if dcfg.ollama_model in names:
            report.add("ollama-model",
                       evidence=f"already registered ({str(exc)[:120]})")
        else:
            raise

    models = console.list_provider_models(OLLAMA_PROVIDER)
    names = sorted(str(m.get("model")) for m in models)
    report.add("ollama-models-list",
               evidence=f"{len(names)}: {', '.join(names[:12])}")

    # OpenRouter custom models for the grouped menu (spec 025 follow-up)
    from .config import ConfigError

    or_models = console.list_provider_models(OPENROUTER_PROVIDER)
    or_names = {str(m.get("model")) for m in or_models}
    for model_id, ctx, mt in OPENROUTER_CUSTOM_MODELS:
        if model_id in or_names:
            report.add(f"cloud-model:{model_id}", evidence="already registered")
            continue
        if not dcfg.openrouter_api_key:
            raise ConfigError(
                "openrouter_api_key required to register extra cloud models "
                "(env DIFY_OPENROUTER_API_KEY or [dify] openrouter_api_key)"
            )
        console.save_model_credentials(
            OPENROUTER_PROVIDER, model_id, "llm",
            {"model_name": model_id, "api_key": dcfg.openrouter_api_key,
             "context_size": ctx, "max_tokens_to_sample": mt,
             # without this the model free-forms tool calls as text (2026-10-27 bug)
             "function_calling_type": "tool_call"},
        )
        report.add(f"cloud-model:{model_id}", evidence="registered")
