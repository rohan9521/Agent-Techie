from typing import Literal, TypedDict

from pydantic import BaseModel, Field

AgentName = Literal["supervisor", "requirements", "architect"]
WorkflowStatus = Literal["pending", "running", "completed", "failed"]


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


class WorkflowState(BaseModel):
    user_request: str
    repository: str
    requirements: Requirements | None = None
    architecture: Architecture | None = None
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
    current_agent: AgentName
    status: WorkflowStatus
    errors: list[str]
    iteration: int
    messages: list[str]
