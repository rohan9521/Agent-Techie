from pydantic import BaseModel, Field, field_validator


class TaskRequest(BaseModel):
    repository: str = Field(pattern=r"^[^/\s]+/[^/\s]+$")
    task: str = Field(min_length=1)

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
