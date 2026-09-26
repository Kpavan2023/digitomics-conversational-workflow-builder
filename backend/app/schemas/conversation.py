from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.message import Message
from app.schemas.requirement import Requirement
from app.schemas.workflow import GeneratedWorkflow, WorkflowState


class ConversationCreate(BaseModel):
    title: str | None = None


class Conversation(BaseModel):
    id: str
    title: str | None = None
    messages: list[Message] = Field(default_factory=list)
    state: WorkflowState = Field(default_factory=WorkflowState)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ChatRequest(BaseModel):
    """
    User message sent to the conversation orchestrator.
    """

    message: str


class ChatResponse(BaseModel):
    """
    Stable response returned by the conversation orchestrator.
    """

    message: str

    workflow_ready: bool = False

    state: WorkflowState

    workflow: GeneratedWorkflow | None = None

    requirements: list[Requirement] = Field(
        default_factory=list
    )

    ambiguities: list[str] = Field(
        default_factory=list
    )

    conflicts: list[str] = Field(
        default_factory=list
    )