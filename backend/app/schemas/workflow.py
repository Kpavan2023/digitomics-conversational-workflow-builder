from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.requirement import Requirement


class WorkflowStatus(str, Enum):
    COLLECTING = "collecting"
    READY = "ready"
    GENERATED = "generated"


class Intent(BaseModel):
    """
    Represents the user's overall automation goal.

    The goal is extracted from the conversation, while the
    application remains responsible for deciding whether the
    workflow is complete.
    """

    goal: str | None = None
    confidence: float | None = None


class Trigger(BaseModel):
    """
    Defines the event or schedule that starts the workflow.
    """

    type: str | None = None
    provider: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)


class Condition(BaseModel):
    """
    Defines a rule that determines whether an action should execute.
    """

    field: str
    operator: str
    value: Any
    currency: str | None = None


class Action(BaseModel):
    """
    Defines an operation performed by the workflow.
    """

    type: str
    provider: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)


class WorkflowState(BaseModel):
    """
    Canonical application-owned representation of the workflow
    being constructed during a conversation.

    The LLM may propose information, but the application remains
    responsible for deciding:

    - what information is known
    - what information is missing
    - what clarification should be asked next
    - when the workflow is complete

    condition_enabled represents whether the workflow should use
    a condition:

    - None  -> the user has not answered the condition question yet
    - True  -> a condition is required and should be collected
    - False -> the user explicitly chose not to use a condition

    duplicate_handling represents whether duplicate invoices should
    be ignored:

    - None  -> the user has not answered the duplicate question yet
    - True  -> duplicate invoices should be ignored
    - False -> duplicate invoices should not be ignored

    active_requirement_id represents the single requirement
    currently being collected from the user.
    """

    intent: Intent = Field(default_factory=Intent)

    trigger: Trigger = Field(default_factory=Trigger)

    conditions: list[Condition] = Field(default_factory=list)

    condition_enabled: bool | None = None

    actions: list[Action] = Field(default_factory=list)

    duplicate_handling: bool | None = None

    active_requirement_id: str | None = None

    missing_requirements: list[str] = Field(default_factory=list)

    ambiguities: list[str] = Field(default_factory=list)

    conflicts: list[str] = Field(default_factory=list)

    status: WorkflowStatus = WorkflowStatus.COLLECTING

    version: int = 1


class WorkflowNode(BaseModel):
    id: str
    type: str
    label: str
    configuration: dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    from_node: str
    to_node: str


class WorkflowMetadata(BaseModel):
    name: str | None = None
    description: str | None = None


class GeneratedWorkflow(BaseModel):
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    metadata: WorkflowMetadata = Field(default_factory=WorkflowMetadata)


class ValidateWorkflowRequest(BaseModel):
    state: WorkflowState


class WorkflowResponse(BaseModel):
    workflow: GeneratedWorkflow | None = None
    valid: bool = False
    errors: list[str] = Field(default_factory=list)


class StateResponse(BaseModel):
    state: WorkflowState
    requirements: list[Requirement] = Field(default_factory=list)