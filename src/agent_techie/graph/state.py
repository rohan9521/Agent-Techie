from pathlib import PurePosixPath
from typing import Literal, TypedDict

from pydantic import BaseModel, Field, field_validator, model_validator

AgentName = Literal[
    "supervisor", "requirements", "architect", "coder", "tester", "reviewer"
]
WorkflowStatus = Literal[
    "pending", "running", "waiting_approval", "completed", "failed"
]


def _validate_generated_path(path: str) -> None:
    parsed = PurePosixPath(path)
    if (
        not path
        or parsed.is_absolute()
        or not parsed.parts
        or ".." in parsed.parts
        or "\\" in path
        or parsed.parts[0].endswith(":")
    ):
        raise ValueError(f"generated file path must stay within the project: {path}")


class Requirements(BaseModel):
    functional_requirements: list[str] = Field(min_length=1)
    non_functional_requirements: list[str] = Field(default_factory=list)
    api_requirements: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


class Architecture(BaseModel):
    summary: str
    components: list[str] = Field(min_length=1)
    implementation_plan: list[str] = Field(min_length=1)
    diagram_edges: list["DiagramEdge"] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class DiagramEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class CodeChange(BaseModel):
    """A proposed implementation; generated files are never applied automatically."""

    files: list[str] = Field(default_factory=list)
    file_contents: dict[str, str] = Field(default_factory=dict)
    changes: list[str] = Field(default_factory=list)
    branch: str | None = None

    @model_validator(mode="after")
    def proposal_size_must_be_bounded(self) -> "CodeChange":
        if len(self.files) > 12:
            raise ValueError("a proposal may contain at most 12 files")
        if sum(map(len, self.file_contents.values())) > 80_000:
            raise ValueError("generated source files exceed the total size limit")
        return self

    @field_validator("files")
    @classmethod
    def file_paths_must_be_relative(cls, value: list[str]) -> list[str]:
        for path in value:
            _validate_generated_path(path)
        return value

    @field_validator("file_contents")
    @classmethod
    def generated_files_must_be_bounded(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 12:
            raise ValueError("a proposal may contain at most 12 files")
        for path, content in value.items():
            _validate_generated_path(path)
            if len(content) > 30_000:
                raise ValueError(f"generated file is too large: {path}")
        return value


class ReviewFinding(BaseModel):
    severity: Literal["critical", "high", "medium", "low", "info"] = "info"
    file: str = ""
    line: int | None = None
    issue: str
    recommendation: str = ""


class TestReport(BaseModel):
    passed: bool = False
    command: str = ""
    output: str = ""
    failures: list[str] = Field(default_factory=list)


class ReviewReport(BaseModel):
    approved: bool = False
    review_mode: Literal["llm", "deterministic"] = "deterministic"
    findings: list[str] = Field(default_factory=list)
    details: list[ReviewFinding] = Field(default_factory=list)
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
    test_report: TestReport | dict[str, object]
    review_report: ReviewReport | dict[str, object]
    requires_approval: bool
    approval: bool | None
    execute_implementation: bool
    current_agent: AgentName
    status: WorkflowStatus
    errors: list[str]
    iteration: int
    messages: list[str]
