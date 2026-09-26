from typing import Any

from langgraph.graph import END, START, StateGraph

from agent_techie.agents.architect import ArchitectAgent
from agent_techie.agents.coder import CoderAgent
from agent_techie.agents.requirements import RequirementsAgent
from agent_techie.agents.reviewer import ReviewerAgent
from agent_techie.agents.tester import TesterAgent
from agent_techie.graph.state import GraphState
from agent_techie.graph.supervisor import Supervisor


def build_workflow(
    requirements_agent: RequirementsAgent | None = None,
    architect_agent: ArchitectAgent | None = None,
    coder_agent: CoderAgent | None = None,
    tester_agent: TesterAgent | None = None,
    reviewer_agent: ReviewerAgent | None = None,
    supervisor: Supervisor | None = None,
) -> Any:
    requirements = requirements_agent or RequirementsAgent()
    architect = architect_agent or ArchitectAgent()
    coder = coder_agent or CoderAgent()
    tester = tester_agent or TesterAgent()
    reviewer = reviewer_agent or ReviewerAgent()
    routing = supervisor or Supervisor()

    def supervise(state: GraphState) -> dict[str, object]:
        decision = routing.route(state)
        iteration = (state.get("iteration") or 0) + 1
        status = (
            "completed"
            if decision.next_agent == "complete"
            else state.get("status", "running")
        )
        if decision.next_agent == "failed":
            status = "failed"
        return {
            "current_agent": "supervisor",
            "status": status,
            "errors": state.get("errors") or [],
            "iteration": iteration,
            "messages": [decision.reason],
        }

    def route(state: GraphState) -> str:
        return routing.route(state).next_agent

    def collect_requirements(state: GraphState) -> dict[str, object]:
        result = requirements.run(state["user_request"])
        return {
            "requirements": result,
            "current_agent": "requirements",
            "status": "running",
        }

    def design_architecture(state: GraphState) -> dict[str, object]:
        result = architect.run(state["requirements"])
        return {
            "architecture": result,
            "implementation_plan": result.implementation_plan,
            "current_agent": "architect",
            "status": "running",
        }

    def write_code(state: GraphState) -> dict[str, object]:
        result = coder.run(state["architecture"], state.get("repository", ""))
        return {"code_change": result, "current_agent": "coder", "status": "running"}

    def run_tests(state: GraphState) -> dict[str, object]:
        result = tester.run(state["code_change"])
        return {"test_report": result, "current_agent": "tester", "status": "running"}

    def review_code(state: GraphState) -> dict[str, object]:
        result = reviewer.run(state["code_change"], state["test_report"])
        return {
            "review_report": result,
            "current_agent": "reviewer",
            "status": "running",
        }

    def request_approval(state: GraphState) -> dict[str, object]:
        return {
            "current_agent": "supervisor",
            "status": "waiting_approval",
            "messages": ["Human approval is required before completion"],
        }

    builder = StateGraph(GraphState)
    builder.add_node("supervisor_agent", supervise)
    builder.add_node("requirements_agent", collect_requirements)
    builder.add_node("architect_agent", design_architecture)
    builder.add_node("coder_agent", write_code)
    builder.add_node("tester_agent", run_tests)
    builder.add_node("reviewer_agent", review_code)
    builder.add_node("approval_gate", request_approval)
    builder.add_edge(START, "supervisor_agent")
    builder.add_conditional_edges(
        "supervisor_agent",
        route,
        {
            "requirements": "requirements_agent",
            "architect": "architect_agent",
            "coder": "coder_agent",
            "tester": "tester_agent",
            "reviewer": "reviewer_agent",
            "approval": "approval_gate",
            "complete": END,
            "failed": END,
        },
    )
    builder.add_edge("requirements_agent", "supervisor_agent")
    builder.add_edge("architect_agent", "supervisor_agent")
    builder.add_edge("coder_agent", "supervisor_agent")
    builder.add_edge("tester_agent", "supervisor_agent")
    builder.add_edge("reviewer_agent", "supervisor_agent")
    builder.add_edge("approval_gate", END)
    return builder.compile()
