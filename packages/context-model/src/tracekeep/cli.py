"""Command-line entry point for Tracekeep's local vertical slice."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

import uvicorn

from tracekeep.api import create_app
from tracekeep.demo import default_demo_repository, prepare_demo_repository, run_demo
from tracekeep.manifest import initialize_manifest
from tracekeep.mcp_runtime import serve_demo_mcp, serve_workspace_mcp
from tracekeep.migrations import upgrade_database
from tracekeep.workspace import sync_local_workspace

DEFAULT_DATABASE_URL = "postgresql+psycopg://tracekeep:tracekeep_local@localhost:55432/tracekeep"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tracekeep")
    subparsers = parser.add_subparsers(dest="command", required=True)

    migrate = subparsers.add_parser("migrate", help="apply explicit schema migrations")
    migrate.add_argument("--database-url")

    init = subparsers.add_parser(
        "init", help="create a repository-owned Tracekeep manifest"
    )
    init.add_argument("repository", nargs="?", type=Path, default=Path.cwd())
    init.add_argument("--objective", required=True)
    init.add_argument("--next-action", required=True)

    sync = subparsers.add_parser(
        "sync", help="ingest and compile the exact committed repository state"
    )
    sync.add_argument("repository", nargs="?", type=Path, default=Path.cwd())
    sync.add_argument("--database-url")
    sync.add_argument("--query")

    prepare = subparsers.add_parser(
        "prepare-demo", help="create the synthetic Git continuation repository"
    )
    prepare.add_argument("--repository", type=Path, default=default_demo_repository())

    demo = subparsers.add_parser(
        "demo", help="ingest, verify, retrieve, and compile a cited handoff"
    )
    demo.add_argument("--database-url")
    demo.add_argument("--repository", type=Path, default=default_demo_repository())

    mcp = subparsers.add_parser("mcp", help="serve one exact local workspace over stdio")
    mcp.add_argument("--database-url")
    mcp.add_argument("--repository", type=Path)
    mcp.add_argument("--demo", action="store_true")

    api = subparsers.add_parser("api", help="serve the read-only synthetic demo API")
    api.add_argument("--database-url")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8000)
    return parser


def _database_url(explicit: str | None) -> str:
    if explicit is not None:
        return explicit
    return os.getenv("TRACEKEEP_DATABASE_URL") or DEFAULT_DATABASE_URL


def main(arguments: Sequence[str] | None = None) -> None:
    parsed = _parser().parse_args(arguments)
    if parsed.command == "migrate":
        upgrade_database(_database_url(parsed.database_url))
        print("Tracekeep schema is current.")
        return
    if parsed.command == "init":
        path, manifest = initialize_manifest(
            parsed.repository,
            objective=parsed.objective,
            next_action=parsed.next_action,
        )
        print(
            json.dumps(
                {
                    "manifest": str(path),
                    "repository_id": str(manifest.repository_id),
                    "task_id": str(manifest.task.id),
                    "next": (
                        "Review tracekeep.json, then commit it before running "
                        "tracekeep sync."
                    ),
                },
                indent=2,
            )
        )
        return
    if parsed.command == "sync":
        synced = sync_local_workspace(
            parsed.repository,
            database_url=parsed.database_url,
            query=parsed.query,
        )
        print(
            json.dumps(
                {
                    "repository": str(synced.workspace.repository_path),
                    "task_id": str(synced.workspace.manifest.task.id),
                    "branch": synced.handoff.context_pack.repository_version.branch,
                    "commit": synced.handoff.context_pack.repository_version.commit_sha,
                    "context_version_id": str(synced.handoff.context_version.id),
                    "status": (
                        "partial"
                        if synced.handoff.content["unknowns"]
                        or synced.handoff.content["contradictions"]
                        else "ok"
                    ),
                },
                indent=2,
            )
        )
        return
    if parsed.command == "prepare-demo":
        path = prepare_demo_repository(parsed.repository)
        print(path)
        return
    if parsed.command == "mcp":
        if parsed.demo:
            serve_demo_mcp(_database_url(parsed.database_url))
            return
        serve_workspace_mcp(parsed.repository or Path.cwd(), parsed.database_url)
        return
    if parsed.command == "api":
        uvicorn.run(
            create_app(_database_url(parsed.database_url)),
            host=parsed.host,
            port=parsed.port,
        )
        return
    result = run_demo(_database_url(parsed.database_url), parsed.repository)
    print(
        json.dumps(
            {
                "repository": str(result.repository_path),
                "handoff_id": str(result.handoff.handoff.id),
                "context_version_id": str(result.handoff.context_version.id),
                **result.handoff.content,
            },
            indent=2,
            default=str,
        )
    )
