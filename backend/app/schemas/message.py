from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    id: str | None = None

    role: MessageRole

    content: str

    created_at: datetime | None = None

    metadata: dict = Field(default_factory=dict)