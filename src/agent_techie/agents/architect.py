from collections.abc import Mapping

from agent_techie.graph.state import Architecture, Requirements


class ArchitectAgent:
    """Produce a structured architecture proposal from validated requirements."""

    def run(
        self, requirements: Requirements | Mapping[str, object] | None
    ) -> Architecture:
        if requirements is None:
            raise ValueError("requirements are required before architecture")
        validated = Requirements.model_validate(requirements)
        if not validated.functional_requirements:
            raise ValueError("functional requirements are required")
        first_requirement = validated.functional_requirements[0]
        return Architecture(
            summary=f"Implement the requested capability: {first_requirement}",
            components=["Existing repository components", "Target feature boundary"],
            implementation_plan=[
                "Inspect the existing repository and identify the owning modules",
                "Implement the smallest change that satisfies the acceptance criteria",
                "Add or update focused tests and quality checks",
            ],
            risks=["Repository conventions may constrain the implementation approach"],
        )
