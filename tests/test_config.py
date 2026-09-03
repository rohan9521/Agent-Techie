from agent_techie.config import Settings


def test_settings_have_safe_defaults() -> None:
    settings = Settings()

    assert settings.environment == "development"
    assert settings.api_prefix == "/api"
    assert settings.langsmith_tracing is False


def test_settings_read_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("API_PREFIX", "/v1")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")

    settings = Settings()

    assert settings.environment == "test"
    assert settings.api_prefix == "/v1"
    assert settings.langsmith_tracing is True
