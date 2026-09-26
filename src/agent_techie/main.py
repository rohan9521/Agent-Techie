from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from agent_techie.api.routes import router
from agent_techie.config import Settings, get_settings
from agent_techie.graph.supervisor import Supervisor
from agent_techie.graph.workflow import build_workflow
from agent_techie.observability.logging import configure_logging
from agent_techie.persistence import InMemoryPersistence

FRONTEND_FILE = Path(__file__).parent / "static" / "index.html"


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or get_settings()
    app = FastAPI(
        title="Agent Techie",
        version="0.1.0",
        description=(
            "Production-oriented modular multi-agent software engineering platform"
        ),
    )
    app.state.settings = configured
    app.state.persistence = InMemoryPersistence()
    app.state.workflow_factory = lambda: build_workflow(
        supervisor=Supervisor(max_iterations=configured.max_workflow_iterations)
    )
    configure_logging(configured.log_level)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "agent-techie"}

    @app.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        return FileResponse(FRONTEND_FILE)

    app.include_router(router, prefix=configured.api_prefix, tags=["tasks"])
    return app


app = create_app()
