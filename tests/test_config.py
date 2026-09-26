from agent_techie.config import Settings


def test_settings_have_safe_defaults() -> None:
    settings = Settings()

    assert settings.environment == "development"
    assert settings.api_prefix == "/api"
    assert settings.langsmith_tracing is False
    assert settings.llm_provider is None
    assert settings.model_name == "gpt-4o-mini"


def test_settings_read_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("API_PREFIX", "/v1")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")

    settings = Settings()

    assert settings.environment == "test"
    assert settings.api_prefix == "/v1"
    assert settings.langsmith_tracing is True


def test_settings_read_openai_configuration(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("MODEL_NAME", "gpt-test")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    settings = Settings()

    assert settings.llm_provider == "openai"
    assert settings.model_name == "gpt-test"
    assert settings.openai_api_key is not None
    assert settings.openai_api_key.get_secret_value() == "test-key"
