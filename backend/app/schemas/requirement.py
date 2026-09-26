from enum import Enum

from pydantic import BaseModel, Field


class RequirementStatus(str, Enum):
    MISSING = "missing"
    SATISFIED = "satisfied"
    AMBIGUOUS = "ambiguous"
    CONFLICTING = "conflicting"


class Requirement(BaseModel):
    """
    Describes one piece of information needed to construct
    or validate a workflow.
    """

    id: str

    description: str

    status: RequirementStatus = RequirementStatus.MISSING

    required: bool = True

    depends_on: list[str] = Field(default_factory=list)

    question: str | None = None

    priority: int = 100