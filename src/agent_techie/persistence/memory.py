from collections.abc import Mapping
from copy import deepcopy
from threading import RLock


class InMemoryPersistence:
    """Thread-safe default persistence suitable for local development and tests."""

    def __init__(self) -> None:
        self._projects: dict[str, dict[str, object]] = {}
        self._runs: dict[str, dict[str, object]] = {}
        self._events: dict[str, list[dict[str, object]]] = {}
        self._lock = RLock()

    def save_project(self, project: Mapping[str, object]) -> dict[str, object]:
        value = deepcopy(dict(project))
        project_id = str(value["project_id"])
        with self._lock:
            self._projects[project_id] = value
        return deepcopy(value)

    def get_project(self, project_id: str) -> dict[str, object] | None:
        with self._lock:
            value = self._projects.get(project_id)
            return deepcopy(value) if value else None

    def list_projects(self) -> list[dict[str, object]]:
        with self._lock:
            return deepcopy(list(self._projects.values()))

    def save_run(self, run: Mapping[str, object]) -> dict[str, object]:
        value = deepcopy(dict(run))
        run_id = str(value["run_id"])
        with self._lock:
            self._runs[run_id] = value
        return deepcopy(value)

    def get_run(self, run_id: str) -> dict[str, object] | None:
        with self._lock:
            value = self._runs.get(run_id)
            return deepcopy(value) if value else None

    def list_runs(self, project_id: str | None = None) -> list[dict[str, object]]:
        with self._lock:
            values = list(self._runs.values())
            if project_id is not None:
                values = [v for v in values if v.get("project_id") == project_id]
            return deepcopy(values)

    def append_event(self, event: Mapping[str, object]) -> dict[str, object]:
        value = deepcopy(dict(event))
        run_id = str(value["run_id"])
        with self._lock:
            self._events.setdefault(run_id, []).append(value)
        return deepcopy(value)

    def list_events(self, run_id: str) -> list[dict[str, object]]:
        with self._lock:
            return deepcopy(self._events.get(run_id, []))
