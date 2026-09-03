from typing import Any

from langgraph.graph import END, START, StateGraph

from agent_techie.agents.architect import ArchitectAgent
from agent_techie.agents.requirements import RequirementsAgent
from agent_techie.graph.state import GraphState
from agent_techie.graph.supervisor import Supervisor


def build_workflow(
    requirements_agent: RequirementsAgent | None = None,
    architect_agent: ArchitectAgent | None = None,
    supervisor: Supervisor | None = None,
) -> Any:
    requirements = requirements_agent or RequirementsAgent()
    architect = architect_agent or ArchitectAgent()
    routing = supervisor or Supervisor()

    def supervise(state: GraphState) -> dict[str, object]:
        decision = routing.route(state)
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
            "iteration": state.get("iteration") or 0,
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
            "current_agent": "architect",
            "status": "running",
        }

    builder = StateGraph(GraphState)
    builder.add_node("supervisor_agent", supervise)
    builder.add_node("requirements_agent", collect_requirements)
    builder.add_node("architect_agent", design_architecture)
    builder.add_edge(START, "supervisor_agent")
    builder.add_conditional_edges(
        "supervisor_agent",
        route,
        {
            "requirements": "requirements_agent",
            "architect": "architect_agent",
            "complete": END,
            "failed": END,
        },
    )
    builder.add_edge("requirements_agent", "supervisor_agent")
    builder.add_edge("architect_agent", "supervisor_agent")
    return builder.compile()
