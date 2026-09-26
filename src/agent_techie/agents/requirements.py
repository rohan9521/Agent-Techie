from agent_techie.agents.model import StructuredModel
from agent_techie.graph.state import Requirements


class RequirementsAgent:
    """Create validated requirements from a repository task."""

    def __init__(self, model: StructuredModel | None = None) -> None:
        self.model = model

    def run(self, user_request: str) -> Requirements:
        request = user_request.strip()
        if not request:
            raise ValueError("user request must not be empty")

        if self.model is not None:
            return self.model.generate(
                "Turn the task into concise, testable software requirements. "
                "Do not invent repository facts. List ambiguities instead of "
                "assuming details that materially affect the design.",
                request,
                Requirements,
            )

        return Requirements(
            functional_requirements=[request],
            non_functional_requirements=["Preserve existing repository conventions"],
            acceptance_criteria=[f"The repository satisfies: {request}"],
            assumptions=["The requested change targets the supplied repository"],
        )
