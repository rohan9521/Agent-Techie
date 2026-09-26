from collections.abc import Mapping

from agent_techie.agents.model import StructuredModel
from agent_techie.graph.state import Architecture, CodeChange


class CoderAgent:
    """Produce a reviewable code proposal without modifying a repository."""

    def __init__(self, model: StructuredModel | None = None) -> None:
        self.model = model

    def run(
        self,
        architecture: Architecture | Mapping[str, object],
        repository: str = "",
        user_request: str = "",
    ) -> CodeChange:
        validated = Architecture.model_validate(architecture)
        if self.model is not None:
            proposed = self.model.generate(
                "Implement the requested feature as a small, coherent code proposal. "
                "Return complete file contents for every proposed file, relative "
                "paths only, and a concise list of changes. Never claim to edit or "
                "test a repository. Do not include secrets or unrelated files.",
                (
                    f"Repository identifier: {repository}\n"
                    f"Task: {user_request}\n"
                    f"Architecture:\n{validated.model_dump_json()}"
                ),
                CodeChange,
            )
            if not proposed.files and proposed.file_contents:
                proposed.files = list(proposed.file_contents)
            return proposed

        return CodeChange(
            files=[],
            changes=[
                f"Implement the architecture step: {step}"
                for step in validated.implementation_plan
            ],
            branch=f"agent-techie/{repository.replace('/', '-')}"
            if repository
            else None,
        )
