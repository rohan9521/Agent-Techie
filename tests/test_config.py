import pytest

from agent_techie.config import Settings


def test_settings_have_safe_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.api_prefix == "/api"
    assert settings.langsmith_tracing is False
    assert settings.llm_provider == "ollama"
    assert settings.model_name == "qwen2.5-coder"
    assert settings.ollama_base_url == "http://localhost:11434"


def test_settings_read_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("API_PREFIX", "/v1")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")

    settings = Settings(_env_file=None)

    assert settings.environment == "test"
    assert settings.api_prefix == "/v1"
    assert settings.langsmith_tracing is True


def test_settings_read_openai_configuration(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("MODEL_NAME", "gpt-test")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    settings = Settings(_env_file=None)

    assert settings.llm_provider == "openai"
    assert settings.model_name == "gpt-test"
    assert settings.openai_api_key is not None
    assert settings.openai_api_key.get_secret_value() == "test-key"


def test_settings_read_ollama_configuration(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("MODEL_NAME", "llama3.2")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.local:11434")

    settings = Settings(_env_file=None)

    assert settings.llm_provider == "ollama"
    assert settings.model_name == "llama3.2"
    assert settings.ollama_base_url == "http://ollama.local:11434"


@pytest.mark.parametrize(
    ("environment_name", "setting_name"),
    [
        ("OPENAI_API_KEY", "openai_api_key"),
        ("GEMINI_API_KEY", "gemini_api_key"),
        ("ANTHROPIC_API_KEY", "anthropic_api_key"),
    ],
)
def test_settings_read_cloud_provider_api_keys(
    monkeypatch, environment_name: str, setting_name: str
) -> None:
    monkeypatch.setenv(environment_name, "test-key")

    settings = Settings(_env_file=None)

    api_key = getattr(settings, setting_name)
    assert api_key is not None
    assert api_key.get_secret_value() == "test-key"
