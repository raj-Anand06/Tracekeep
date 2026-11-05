"""Application service coordinating ingestion and cited handoff compilation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from tracekeep.compiler import CompiledHandoff, compile_handoff
from tracekeep.ingest import IngestionResult, ingest_local_repository
from tracekeep.storage import TracekeepStore


@dataclass(frozen=True)
class ServiceScope:
    tenant_id: UUID
    workspace_id: UUID
    actor_id: UUID
    repository_id: UUID


class TracekeepService:
    def __init__(self, store: TracekeepStore) -> None:
        self.store = store

    def ingest(
        self,
        *,
        repository_path: Path,
        scope: ServiceScope,
        code_cache_path: Path | None = None,
        replace_current_snapshot: bool = False,
        progress: Callable[[str], None] | None = None,
    ) -> IngestionResult:
        return ingest_local_repository(
            self.store,
            path=repository_path,
            tenant_id=scope.tenant_id,
            workspace_id=scope.workspace_id,
            actor_id=scope.actor_id,
            repository_id=scope.repository_id,
            code_cache_path=code_cache_path,
            replace_current_snapshot=replace_current_snapshot,
            progress=progress,
        )

    def compile_task_handoff(
        self,
        *,
        scope: ServiceScope,
        task_id: UUID,
        query: str,
        token_budget: int = 2048,
    ) -> CompiledHandoff:
        return compile_handoff(
            self.store,
            tenant_id=scope.tenant_id,
            workspace_id=scope.workspace_id,
            task_id=task_id,
            actor_id=scope.actor_id,
            query=query,
            token_budget=token_budget,
        )

    def latest_handoff(self, *, scope: ServiceScope, task_id: UUID) -> dict[str, object]:
        content = self.store.load_latest_handoff(
            tenant_id=scope.tenant_id,
            workspace_id=scope.workspace_id,
            task_id=task_id,
        )
        return {str(key): value for key, value in content.items()}
