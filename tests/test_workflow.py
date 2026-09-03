from agent_techie.graph.workflow import build_workflow


def test_workflow_executes_requirements_then_architect(sample_request) -> None:
    result = build_workflow().invoke(
        {
            "user_request": sample_request["task"],
            "repository": sample_request["repository"],
        }
    )

    assert result["status"] == "completed"
    assert result["current_agent"] == "supervisor"
    assert result["requirements"]
    assert result["architecture"]
    assert result["errors"] == []
