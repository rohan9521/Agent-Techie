from collections.abc import Mapping

from agent_techie.graph.state import Architecture, CodeChange


class CoderAgent:
    """Produce a safe implementation proposal without modifying a repository."""

    def run(
        self,
        architecture: Architecture | Mapping[str, object],
        repository: str = "",
    ) -> CodeChange:
        validated = Architecture.model_validate(architecture)
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
