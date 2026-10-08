from pydantic import BaseModel, Field, field_validator


class TaskRequest(BaseModel):
    repository: str = Field(pattern=r"^[^/\s]+/[^/\s]+$")
    task: str = Field(min_length=1)
    project_id: str | None = None
    execute_implementation: bool = True
    requires_approval: bool = False

    @field_validator("task")
    @classmethod
    def task_must_contain_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("task must contain text")
        return normalized


class TaskResponse(BaseModel):
    run_id: str
    status: str


class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    repository: str = Field(pattern=r"^[^/\s]+/[^/\s]+$")


class ProjectResponse(ProjectRequest):
    project_id: str


class ApprovalRequest(BaseModel):
    approved: bool


class RunResponse(BaseModel):
    run_id: str
    status: str
    project_id: str | None = None
    request: dict[str, object] | None = None
    result: dict[str, object] | None = None
    error: str | None = None


class EventResponse(BaseModel):
    run_id: str
    event: str
    data: dict[str, object] = Field(default_factory=dict)
    timestamp: str | None = None
