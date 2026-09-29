"""Local stdio runtime for the read-only Tracekeep MCP server."""

from __future__ import annotations

from tracekeep.demo import (
    DEMO_ACTOR_ID,
    DEMO_REPOSITORY_ID,
    DEMO_TENANT_ID,
    DEMO_WORKSPACE_ID,
)
from tracekeep.mcp_server import create_mcp_server
from tracekeep.service import ServiceScope
from tracekeep.storage import TracekeepStore


def serve_demo_mcp(database_url: str) -> None:
    store = TracekeepStore(database_url)
    try:
        scope = ServiceScope(
            tenant_id=DEMO_TENANT_ID,
            workspace_id=DEMO_WORKSPACE_ID,
            actor_id=DEMO_ACTOR_ID,
            repository_id=DEMO_REPOSITORY_ID,
        )
        create_mcp_server(store, scope).run("stdio")
    finally:
        store.close()
