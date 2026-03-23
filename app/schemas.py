from pydantic import BaseModel, Field


class RunTaskRequest(BaseModel):
    task: str = Field(..., min_length=1, description="The user task for the agent graph.")
    thread_id: str | None = Field(default=None, description="Optional thread identifier for persistence.")


class RunTaskResponse(BaseModel):
    thread_id: str
    task: str
    mode: str
    plan: str
    research_notes: str
    execution_notes: str
    final_response: str
