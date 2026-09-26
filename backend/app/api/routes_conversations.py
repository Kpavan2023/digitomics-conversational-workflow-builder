"""Conversation CRUD routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.conversation import ConversationModel
from app.schemas.conversation import Conversation, ConversationCreate
from app.schemas.message import Message, MessageRole
from app.schemas.workflow import WorkflowState, WorkflowStatus

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


def _build_conversation(
    model: ConversationModel,
) -> Conversation:
    """
    Convert the SQLAlchemy persistence model into the
    application-level Conversation schema.
    """

    messages = [
        Message(**message)
        if isinstance(message, dict)
        else message
        for message in (model.messages or [])
    ]

    return Conversation(
        id=str(model.id),
        title=model.title,
        messages=messages,
        state=WorkflowState(
            **(model.state or {})
        ),
        status=WorkflowStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.post(
    "",
    response_model=Conversation,
)
async def create_conversation(
    req: ConversationCreate,
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """Create a new workflow-building conversation."""

    welcome = Message(
        id=str(uuid.uuid4()),
        role=MessageRole.ASSISTANT,
        content=(
            "I can help you build an automation workflow. "
            "Describe what you'd like to automate — for example, "
            "'When I receive an invoice above ₹10,000, notify finance "
            "on Slack.' I'll ask clarifying questions until I have "
            "everything needed."
        ),
    )

    state = WorkflowState()

    model = ConversationModel(
        id=uuid.uuid4(),
        title=req.title or "Untitled workflow",
        messages=[
            welcome.model_dump(mode="json")
        ],
        state=state.model_dump(mode="json"),
        status=WorkflowStatus.COLLECTING.value,
    )

    db.add(model)

    await db.commit()
    await db.refresh(model)

    return _build_conversation(model)


@router.get(
    "/{conversation_id}",
    response_model=Conversation,
)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """Get a conversation by ID."""

    try:
        conversation_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid conversation ID.",
        )

    model = await db.get(
        ConversationModel,
        conversation_uuid,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return _build_conversation(model)


@router.get(
    "",
    response_model=list[Conversation],
)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
) -> list[Conversation]:
    """List the most recent conversations."""

    stmt = (
        select(ConversationModel)
        .order_by(
            ConversationModel.updated_at.desc()
        )
        .limit(20)
    )

    result = await db.execute(stmt)

    rows = result.scalars().all()

    return [
        _build_conversation(row)
        for row in rows
    ]


@router.delete(
    "/{conversation_id}",
)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Delete a conversation."""

    try:
        conversation_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid conversation ID.",
        )

    result = await db.execute(
        delete(ConversationModel).where(
            ConversationModel.id == conversation_uuid
        )
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    await db.commit()

    return {"deleted": True}