"""Optional service adapters.

The interfaces are intentionally dependency-free. Applications can pass a
SQLAlchemy/Redis client to these adapters without making those services required
for local runs.
"""

from collections.abc import Mapping
from typing import Any, cast


class PostgresPersistence:
    def __init__(self, client: Any) -> None:
        self.client = client

    def save_project(self, project: Mapping[str, object]) -> dict[str, object]:
        return dict(self.client.save_project(dict(project)))

    def get_project(self, project_id: str) -> dict[str, object] | None:
        return cast(dict[str, object] | None, self.client.get_project(project_id))

    def list_projects(self) -> list[dict[str, object]]:
        return list(self.client.list_projects())

    def save_run(self, run: Mapping[str, object]) -> dict[str, object]:
        return dict(self.client.save_run(dict(run)))

    def get_run(self, run_id: str) -> dict[str, object] | None:
        return cast(dict[str, object] | None, self.client.get_run(run_id))

    def list_runs(self, project_id: str | None = None) -> list[dict[str, object]]:
        return list(self.client.list_runs(project_id))

    def append_event(self, event: Mapping[str, object]) -> dict[str, object]:
        return dict(self.client.append_event(dict(event)))

    def list_events(self, run_id: str) -> list[dict[str, object]]:
        return list(self.client.list_events(run_id))


class RedisPersistence(PostgresPersistence):
    """Redis-compatible persistence boundary; serialization is client-owned."""
