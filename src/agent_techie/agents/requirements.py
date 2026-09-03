from agent_techie.graph.state import Requirements


class RequirementsAgent:
    """Create validated requirements without making external model calls."""

    def run(self, user_request: str) -> Requirements:
        request = user_request.strip()
        if not request:
            raise ValueError("user request must not be empty")

        return Requirements(
            functional_requirements=[request],
            non_functional_requirements=["Preserve existing repository conventions"],
            acceptance_criteria=[f"The repository satisfies: {request}"],
            assumptions=["The requested change targets the supplied repository"],
        )
