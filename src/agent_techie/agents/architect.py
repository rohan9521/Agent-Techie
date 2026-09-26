from collections.abc import Mapping

from agent_techie.agents.model import StructuredModel
from agent_techie.graph.state import Architecture, Requirements


class ArchitectAgent:
    """Produce a structured architecture proposal from validated requirements."""

    def __init__(self, model: StructuredModel | None = None) -> None:
        self.model = model

    def run(
        self, requirements: Requirements | Mapping[str, object] | None
    ) -> Architecture:
        if requirements is None:
            raise ValueError("requirements are required before architecture")
        validated = Requirements.model_validate(requirements)
        if not validated.functional_requirements:
            raise ValueError("functional requirements are required")
        if self.model is not None:
            return self.model.generate(
                "Design a practical software architecture that satisfies the "
                "requirements. Return components and directed diagram edges whose "
                "source and target exactly match component names. Include a concise "
                "implementation plan, dependencies, and concrete risks. Do not "
                "claim to have inspected repository files.",
                validated.model_dump_json(),
                Architecture,
            )
        first_requirement = validated.functional_requirements[0]
        return Architecture(
            summary=f"Implement the requested capability: {first_requirement}",
            components=["Existing repository components", "Target feature boundary"],
            implementation_plan=[
                "Inspect the existing repository and identify the owning modules",
                "Implement the smallest change that satisfies the acceptance criteria",
                "Add or update focused tests and quality checks",
            ],
            diagram_edges=[
                {
                    "source": "Existing repository components",
                    "target": "Target feature boundary",
                    "label": "integrates with",
                }
            ],
            risks=["Repository conventions may constrain the implementation approach"],
        )
