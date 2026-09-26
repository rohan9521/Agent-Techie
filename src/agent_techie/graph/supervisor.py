from typing import Literal

from pydantic import BaseModel

from agent_techie.graph.state import (
    GraphState,
    ReviewReport,
    TestReport,
    WorkflowState,
)

RouteName = Literal[
    "requirements",
    "architect",
    "coder",
    "tester",
    "reviewer",
    "approval",
    "complete",
    "failed",
]


class RoutingDecision(BaseModel):
    next_agent: RouteName
    reason: str


def _tests_passed(report: TestReport | dict[str, object] | None) -> bool:
    if isinstance(report, TestReport):
        return report.passed
    return bool(report and report.get("passed", False))


def _review_approved(report: ReviewReport | dict[str, object] | None) -> bool:
    if isinstance(report, ReviewReport):
        return report.approved
    return bool(report and report.get("approved", False))


class Supervisor:
    def __init__(self, max_iterations: int = 10) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        self.max_iterations = max_iterations

    def route(self, state: GraphState | WorkflowState) -> RoutingDecision:
        test_report: TestReport | dict[str, object] | None
        review_report: ReviewReport | dict[str, object] | None
        if isinstance(state, WorkflowState):
            requirements = state.requirements
            architecture = state.architecture
            code_change = state.code_change
            test_report = state.test_report
            review_report = state.review_report
            approval = state.approval
            requires_approval = state.requires_approval
            execute_implementation = state.execute_implementation or requires_approval
            errors = state.errors
            iteration = state.iteration
        else:
            requirements = state.get("requirements")
            architecture = state.get("architecture")
            code_change = state.get("code_change")
            test_report = state.get("test_report")
            review_report = state.get("review_report")
            approval = state.get("approval")
            requires_approval = state.get("requires_approval", False)
            execute_implementation = (
                state.get("execute_implementation", False) or requires_approval
            )
            errors = state.get("errors") or []
            iteration = state.get("iteration") or 0

        if errors:
            return RoutingDecision(next_agent="failed", reason="; ".join(errors))
        if iteration >= self.max_iterations:
            return RoutingDecision(
                next_agent="failed",
                reason=f"Maximum workflow iterations ({self.max_iterations}) reached",
            )
        if requirements is None:
            return RoutingDecision(
                next_agent="requirements", reason="Requirements are missing"
            )
        if architecture is None:
            return RoutingDecision(
                next_agent="architect", reason="Architecture is missing"
            )
        if execute_implementation:
            if code_change is None:
                return RoutingDecision(
                    next_agent="coder", reason="Implementation is missing"
                )
            if test_report is None:
                return RoutingDecision(next_agent="tester", reason="Tests are missing")
            if review_report is None:
                return RoutingDecision(
                    next_agent="reviewer", reason="Review is missing"
                )
            if not _tests_passed(test_report):
                return RoutingDecision(next_agent="failed", reason="Tests did not pass")
            if not _review_approved(review_report):
                return RoutingDecision(
                    next_agent="failed", reason="Review did not approve the change"
                )
            if requires_approval and approval is None:
                return RoutingDecision(
                    next_agent="approval", reason="Human approval is required"
                )
            if requires_approval and approval is False:
                return RoutingDecision(
                    next_agent="failed", reason="Human approval was denied"
                )
        return RoutingDecision(
            next_agent="complete",
            reason="Workflow completed"
            if execute_implementation
            else "Phase 1 analysis is complete",
        )
