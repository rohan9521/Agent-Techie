from unittest.mock import patch

import pytest
from pydantic import ValidationError

from agent_techie.agents.architect import ArchitectAgent
from agent_techie.agents.coder import CoderAgent
from agent_techie.agents.model import (
    AnthropicModel,
    GeminiModel,
    OllamaModel,
    StructuredModel,
)
from agent_techie.agents.requirements import RequirementsAgent
from agent_techie.agents.reviewer import ReviewerAgent
from agent_techie.graph.state import (
    Architecture,
    CodeChange,
    Requirements,
    ReviewReport,
)
from agent_techie.graph.state import (
    TestReport as WorkflowTestReport,
)
from agent_techie.graph.workflow import build_workflow


class FakeStructuredModel:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, system_prompt, user_prompt, schema):
        self.prompts.append(system_prompt)
        assert user_prompt
        if schema is Requirements:
            value = {"functional_requirements": ["Add search"]}
        elif schema is Architecture:
            value = {
                "summary": "Search feature",
                "components": ["API", "Search service"],
                "implementation_plan": ["Implement search"],
                "diagram_edges": [{"source": "API", "target": "Search service"}],
            }
        elif schema is CodeChange:
            value = {
                "file_contents": {"src/search.py": "def search():\n    return []\n"},
                "changes": ["Add search handler"],
            }
        elif schema is ReviewReport:
            value = {"approved": True, "summary": "No blocking findings"}
        else:
            raise AssertionError(f"Unexpected schema: {schema}")
        return schema.model_validate(value)


def test_requirements_agent_returns_structured_requirements(sample_request) -> None:
    result = RequirementsAgent().run(sample_request["task"])

    assert isinstance(result, Requirements)
    assert result.functional_requirements
    assert result.acceptance_criteria
    assert result.ambiguities == []


def test_architect_agent_requires_requirements() -> None:
    with pytest.raises(ValueError, match="requirements"):
        ArchitectAgent().run(None)


def test_architecture_schema_rejects_missing_components() -> None:
    with pytest.raises(ValidationError):
        Architecture.model_validate({"summary": "incomplete"})


def test_requirements_schema_rejects_empty_functional_requirements() -> None:
    with pytest.raises(ValidationError):
        Requirements.model_validate({"functional_requirements": []})


def test_architect_rejects_empty_functional_requirements() -> None:
    with pytest.raises(ValueError, match="functional requirements"):
        ArchitectAgent().run({"functional_requirements": []})


def test_llm_agents_generate_design_code_and_review() -> None:
    model: StructuredModel = FakeStructuredModel()
    requirements = RequirementsAgent(model).run("Add search")
    architecture = ArchitectAgent(model).run(requirements)
    change = CoderAgent(model).run(architecture, "octo/demo", "Add search")
    review = ReviewerAgent(model).run(
        change,
        WorkflowTestReport(passed=True, command="not-run (dry-run)"),
        "Add search",
    )

    assert architecture.diagram_edges[0].source == "API"
    assert change.file_contents["src/search.py"].startswith("def search")
    assert review.approved is True
    assert review.review_mode == "llm"
    assert len(model.prompts) == 4


def test_ollama_model_returns_validated_structured_output() -> None:
    with patch("agent_techie.agents.model.ChatOllama") as chat_ollama:
        (
            chat_ollama.return_value.with_structured_output.return_value.invoke.return_value
        ) = {"functional_requirements": ["Add search"]}
        model = OllamaModel("http://localhost:11434", "llama3.2")

        result = model.generate("system prompt", "user prompt", Requirements)

    assert result.functional_requirements == ["Add search"]
    chat_ollama.assert_called_once_with(
        base_url="http://localhost:11434",
        model="llama3.2",
        temperature=0,
    )


@pytest.mark.parametrize(
    ("model_type", "provider_client", "constructor_args"),
    [
        (
            GeminiModel,
            "ChatGoogleGenerativeAI",
            {"google_api_key": "test-key", "model": "gemini-test", "temperature": 0},
        ),
        (
            AnthropicModel,
            "ChatAnthropic",
            {"api_key": "test-key", "model": "claude-test", "temperature": 0},
        ),
    ],
)
def test_cloud_models_return_validated_structured_output(
    model_type, provider_client: str, constructor_args: dict[str, object]
) -> None:
    with patch(f"agent_techie.agents.model.{provider_client}") as client:
        (
            client.return_value.with_structured_output.return_value.invoke.return_value
        ) = {"functional_requirements": ["Add search"]}
        model = model_type("test-key", str(constructor_args["model"]))

        result = model.generate("system prompt", "user prompt", Requirements)

    assert result.functional_requirements == ["Add search"]
    client.assert_called_once_with(**constructor_args)


def test_llm_workflow_returns_design_code_and_review() -> None:
    result = build_workflow(model=FakeStructuredModel()).invoke(
        {
            "user_request": "Add search",
            "repository": "octo/demo",
            "execute_implementation": True,
        }
    )

    assert result["status"] == "completed"
    assert result["architecture"].diagram_edges
    assert result["code_change"].file_contents["src/search.py"]
    assert result["review_report"].approved


def test_generated_code_paths_cannot_escape_repository() -> None:
    with pytest.raises(ValueError, match="must stay within the project"):
        CodeChange.model_validate(
            {"file_contents": {"../outside.py": "print('unsafe')"}}
        )


def test_llm_reviewer_rejects_high_severity_findings() -> None:
    class HighFindingModel:
        def generate(self, system_prompt, user_prompt, schema):
            assert system_prompt
            assert user_prompt
            return schema.model_validate(
                {
                    "approved": True,
                    "details": [
                        {
                            "severity": "high",
                            "file": "src/search.py",
                            "line": 4,
                            "issue": "The request handler accepts unvalidated input",
                            "recommendation": "Validate the query before use",
                        }
                    ],
                }
            )

    review = ReviewerAgent(HighFindingModel()).run(
        CodeChange(
            files=["src/search.py"],
            file_contents={"src/search.py": "def search(query):\n    return query\n"},
        ),
        WorkflowTestReport(passed=True),
        "Add search",
    )

    assert review.approved is False
    assert review.review_mode == "llm"
