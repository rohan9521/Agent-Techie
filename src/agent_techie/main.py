from fastapi import FastAPI

from agent_techie.api.routes import router
from agent_techie.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or get_settings()
    app = FastAPI(
        title="Agent Techie",
        version="0.1.0",
        description="Phase 1 multi-agent software engineering platform",
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "agent-techie"}

    app.include_router(router, prefix=configured.api_prefix, tags=["tasks"])
    return app


app = create_app()
