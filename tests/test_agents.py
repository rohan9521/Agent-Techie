import pytest
from pydantic import ValidationError

from agent_techie.agents.architect import ArchitectAgent
from agent_techie.agents.requirements import RequirementsAgent
from agent_techie.graph.state import Architecture, Requirements


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


def test_architect_rejects_empty_functional_requirements() -> None:
    with pytest.raises(ValueError, match="functional requirements"):
        ArchitectAgent().run({"functional_requirements": []})
