from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from agent_techie.agents.model import OpenAIModel, StructuredModel
from agent_techie.api.routes import router
from agent_techie.config import Settings, get_settings
from agent_techie.graph.supervisor import Supervisor
from agent_techie.graph.workflow import build_workflow
from agent_techie.observability.logging import configure_logging
from agent_techie.persistence import InMemoryPersistence

FRONTEND_FILE = Path(__file__).parent / "static" / "index.html"


def _configured_model(settings: Settings) -> StructuredModel | None:
    provider = (settings.llm_provider or "").strip().lower()
    if not provider:
        return None
    if provider != "openai":
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
    if settings.openai_api_key is None:
        raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
    return OpenAIModel(
        api_key=settings.openai_api_key.get_secret_value(),
        model_name=settings.model_name,
    )


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
    model = _configured_model(configured)
    app.state.llm_enabled = model is not None
    app.state.workflow_factory = lambda: build_workflow(
        supervisor=Supervisor(max_iterations=configured.max_workflow_iterations),
        model=model,
    )
    configure_logging(configured.log_level)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "agent-techie"}

    @app.get(f"{configured.api_prefix}/status", tags=["system"])
    def status() -> dict[str, str | bool]:
        return {
            "llm_enabled": model is not None,
            "llm_provider": configured.llm_provider or "disabled",
            "model_name": configured.model_name if model is not None else "",
        }

    @app.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        return FileResponse(FRONTEND_FILE)

    app.include_router(router, prefix=configured.api_prefix, tags=["tasks"])
    return app


app = create_app()
