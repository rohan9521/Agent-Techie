from agent_techie.graph.state import WorkflowState
from agent_techie.graph.supervisor import Supervisor


def test_supervisor_routes_new_request_to_requirements() -> None:
    state = WorkflowState(user_request="Add search", repository="octo/demo")

    assert Supervisor().route(state).next_agent == "requirements"


def test_supervisor_routes_requirements_to_architect() -> None:
    state = WorkflowState(
        user_request="Add search",
        repository="octo/demo",
        requirements={
            "functional_requirements": ["Search"],
            "acceptance_criteria": ["Find"],
        },
    )

    assert Supervisor().route(state).next_agent == "architect"


def test_supervisor_stops_after_architecture() -> None:
    state = WorkflowState(
        user_request="Add search",
        repository="octo/demo",
        requirements={
            "functional_requirements": ["Search"],
            "acceptance_criteria": ["Find"],
        },
        architecture={
            "summary": "Search service",
            "components": ["API"],
            "implementation_plan": ["Add endpoint"],
        },
    )

    assert Supervisor().route(state).next_agent == "complete"


def test_supervisor_fails_when_iteration_limit_is_reached() -> None:
    state = WorkflowState(
        user_request="Add search",
        repository="octo/demo",
        iteration=2,
    )

    decision = Supervisor(max_iterations=2).route(state)

    assert decision.next_agent == "failed"
    assert "Maximum workflow iterations" in decision.reason
