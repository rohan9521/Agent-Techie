from typing import Protocol, TypeVar

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredModel(Protocol):
    def generate(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T: ...


class OpenAIModel:
    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key.strip():
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if not model_name.strip():
            raise ValueError("MODEL_NAME must not be empty")
        self._model = ChatOpenAI(
            api_key=api_key,
            model=model_name,
            temperature=0,
            timeout=60,
            max_retries=2,
        )

    def generate(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        response: object = self._model.with_structured_output(schema).invoke(
            [("system", system_prompt), ("human", user_prompt)]
        )
        return schema.model_validate(response)


class OllamaModel:
    def __init__(self, base_url: str, model_name: str) -> None:
        if not base_url.strip():
            raise ValueError("OLLAMA_BASE_URL must not be empty")
        if not model_name.strip():
            raise ValueError("MODEL_NAME must not be empty")
        self._model = ChatOllama(
            base_url=base_url,
            model=model_name,
            temperature=0,
        )

    def generate(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        response: object = self._model.with_structured_output(schema).invoke(
            [("system", system_prompt), ("human", user_prompt)]
        )
        return schema.model_validate(response)


class GeminiModel:
    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        if not model_name.strip():
            raise ValueError("MODEL_NAME must not be empty")
        self._model = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=model_name,
            temperature=0,
        )

    def generate(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        response: object = self._model.with_structured_output(schema).invoke(
            [("system", system_prompt), ("human", user_prompt)]
        )
        return schema.model_validate(response)


class AnthropicModel:
    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key.strip():
            raise ValueError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
            )
        if not model_name.strip():
            raise ValueError("MODEL_NAME must not be empty")
        self._model = ChatAnthropic(
            api_key=api_key,
            model=model_name,
            temperature=0,
        )

    def generate(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        response: object = self._model.with_structured_output(schema).invoke(
            [("system", system_prompt), ("human", user_prompt)]
        )
        return schema.model_validate(response)
