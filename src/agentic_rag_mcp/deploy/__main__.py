"""CLI: python -m agentic_rag_mcp.deploy {redeploy|chatflow|verify|all} [--dry-run] (spec 011)."""

from __future__ import annotations

import argparse
import sys

import yaml

from . import docker_ops, tool_sync
from .battery import run_battery
from .config import ConfigError, DeployConfig, redact, resolve
from .report import RunReport


def echo_config(dcfg: DeployConfig) -> None:
    safe = (f"console_url={dcfg.console_url} "
            f"console_email={dcfg.console_email or '<unset>'} "
            f"console_password={'***' if dcfg.console_password else '<unset>'} "
            f"api_key={'***' if dcfg.api_key else '<unset>'} "
            f"image={dcfg.sidecar_image} container={dcfg.container}")
    print(f"config: {safe}", flush=True)


def cmd_redeploy(dcfg: DeployConfig, dry: bool) -> int:
    report = RunReport()
    report.configure(dcfg)
    plan = ["build image", "recreate container", "wait health",
            "ensure MCP registration", "re-sync tool cache"]
    if dry:
        print("dry-run plan (redeploy):")
        for p in plan:
            print(f"  - {p}")
        return 0
    try:
        docker_ops.build_image(dcfg.sidecar_image, report)
        docker_ops.recreate_container(dcfg.container, dcfg.sidecar_image, report)
        if not docker_ops.wait_health():
            report.add("health-wait", "failed",
                       evidence="sidecar did not become healthy in 120s")
            print(report.summary(dcfg))
            return 1
        report.add("health-wait", evidence="ok")
        tool_sync.sync_provider(dcfg, report)
    except Exception as exc:  # noqa: BLE001 — honest failure boundary
        report.add("redeploy", "failed", evidence=str(exc))
        print(report.summary(dcfg))
        return 1
    print(report.summary(dcfg))
    return report.exit_code()


def cmd_chatflow(dcfg: DeployConfig, dry: bool) -> int:
    from .dify_console import ConsoleError, DifyConsole

    report = RunReport()
    report.configure(dcfg)
    if dry:
        print("dry-run plan (chatflow):")
        print(f"  - login to {dcfg.console_url}")
        print(f"  - find or import app '{dcfg.app_name}' from {dcfg.dsl_path}")
        print("  - update workflow draft (in place) when the app exists")
        print("  - publish")
        return 0
    try:
        dcfg.require_console()
        with open(dcfg.dsl_path, encoding="utf-8") as f:
            dsl = yaml.safe_load(f)
        console = DifyConsole(dcfg)
        console.login()
        report.add("console-login", evidence="ok")
        app = console.find_app(dcfg.app_name)
        if app:
            console.update_workflow_draft(app["id"], dsl.get("workflow", {}))
            report.add("chatflow-update", evidence=f"draft updated in place (app {app['id'][:8]})")
            app_id = app["id"]
        else:
            app_id = console.import_app(
                open(dcfg.dsl_path, encoding="utf-8").read()
            )
            report.add("chatflow-import", evidence=f"imported as app {app_id[:8]}")
        console.publish(app_id)
        report.add("chatflow-publish", evidence="published")
    except (ConfigError, ConsoleError, FileNotFoundError, OSError) as exc:
        report.add("chatflow", "failed", evidence=str(exc))
        print(report.summary(dcfg))
        return 2 if isinstance(exc, ConfigError) else 1
    print(report.summary(dcfg))
    return report.exit_code()


def cmd_verify(dcfg: DeployConfig, dry: bool, skip_chat: bool = False) -> int:
    if dry:
        print("dry-run plan (verify): run the battery scenarios headlessly,")
        print("  unique verify_<ts> projects, teardown sweep, exit = failure count")
        return 0
    results, cleanup = run_battery(dcfg, skip_chat=skip_chat)
    failed = [name for name, ok, _ in results if not ok]
    for note in cleanup:
        print(f"[i] {note}")
    print(f"summary: {len(results) - len(failed)}/{len(results)} passed"
          + (f", failed: {', '.join(failed)}" if failed else ""))
    return len(failed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentic-rag-deploy")
    parser.add_argument("command", choices=["redeploy", "chatflow", "verify", "all"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-chat", action="store_true")
    args = parser.parse_args(argv)

    from ..config import load_config

    dcfg = resolve(load_config())
    echo_config(dcfg)

    if args.command == "redeploy":
        return cmd_redeploy(dcfg, args.dry_run)
    if args.command == "chatflow":
        return cmd_chatflow(dcfg, args.dry_run)
    if args.command == "verify":
        return cmd_verify(dcfg, args.dry_run, args.skip_chat)
    # all: redeploy → chatflow → verify
    if args.dry_run:
        print("dry-run plan (all): redeploy → chatflow → verify")
        return 0
    for step in (cmd_redeploy, cmd_chatflow):
        code = step(dcfg, False)
        if code != 0:
            print(f"aborting 'all' before verify (exit {code})")
            return code
    return cmd_verify(dcfg, False, args.skip_chat)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ConfigError as exc:
        print(f"configuration error: {exc}")
        sys.exit(2)
