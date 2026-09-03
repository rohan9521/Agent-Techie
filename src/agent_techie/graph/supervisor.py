from typing import Literal

from pydantic import BaseModel

from agent_techie.graph.state import GraphState, WorkflowState

RouteName = Literal["requirements", "architect", "complete", "failed"]


class RoutingDecision(BaseModel):
    next_agent: RouteName
    reason: str


class Supervisor:
    def route(self, state: GraphState | WorkflowState) -> RoutingDecision:
        if isinstance(state, WorkflowState):
            requirements = state.requirements
            architecture = state.architecture
            errors = state.errors
        else:
            requirements = state.get("requirements")
            architecture = state.get("architecture")
            errors = state.get("errors") or []

        if errors:
            return RoutingDecision(next_agent="failed", reason="; ".join(errors))
        if requirements is None:
            return RoutingDecision(
                next_agent="requirements", reason="Requirements are missing"
            )
        if architecture is None:
            return RoutingDecision(
                next_agent="architect", reason="Architecture is missing"
            )
        return RoutingDecision(
            next_agent="complete", reason="Phase 1 analysis is complete"
        )
