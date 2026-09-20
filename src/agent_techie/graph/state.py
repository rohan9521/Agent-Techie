from typing import Literal, TypedDict

from pydantic import BaseModel, Field

AgentName = Literal[
    "supervisor", "requirements", "architect", "coder", "tester", "reviewer"
]
WorkflowStatus = Literal[
    "pending", "running", "waiting_approval", "completed", "failed"
]


class Requirements(BaseModel):
    functional_requirements: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    api_requirements: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


class Architecture(BaseModel):
    summary: str
    components: list[str] = Field(min_length=1)
    implementation_plan: list[str] = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class CodeChange(BaseModel):
    """A deterministic, reviewable description of a proposed implementation."""

    files: list[str] = Field(default_factory=list)
    changes: list[str] = Field(default_factory=list)
    branch: str | None = None


class TestReport(BaseModel):
    passed: bool = False
    command: str = ""
    output: str = ""
    failures: list[str] = Field(default_factory=list)


class ReviewReport(BaseModel):
    approved: bool = False
    findings: list[str] = Field(default_factory=list)
    summary: str = ""


class WorkflowState(BaseModel):
    user_request: str
    repository: str
    requirements: Requirements | None = None
    architecture: Architecture | None = None
    implementation_plan: list[str] = Field(default_factory=list)
    code_change: CodeChange | None = None
    test_report: TestReport | None = None
    review_report: ReviewReport | None = None
    requires_approval: bool = False
    approval: bool | None = None
    execute_implementation: bool = False
    current_agent: AgentName = "supervisor"
    status: WorkflowStatus = "pending"
    errors: list[str] = Field(default_factory=list)
    iteration: int = 0
    messages: list[str] = Field(default_factory=list)


class GraphState(TypedDict, total=False):
    user_request: str
    repository: str
    requirements: Requirements
    architecture: Architecture
    implementation_plan: list[str]
    code_change: CodeChange
    test_report: TestReport
    review_report: ReviewReport
    requires_approval: bool
    approval: bool | None
    execute_implementation: bool
    current_agent: AgentName
    status: WorkflowStatus
    errors: list[str]
    iteration: int
    messages: list[str]
