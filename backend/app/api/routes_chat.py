"""Chat routes — send a message and receive an assistant response."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.llm.provider import get_llm_provider
from app.models.conversation import ConversationModel
from app.orchestrator.conversation_orchestrator import process_message
from app.schemas.conversation import ChatRequest, ChatResponse, Conversation
from app.schemas.message import Message
from app.schemas.workflow import GeneratedWorkflow, WorkflowState, WorkflowStatus

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post(
    "/{conversation_id}/messages",
    response_model=ChatResponse,
)
async def send_message(
    conversation_id: str,
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Process a user message and return the updated workflow state."""

    # -------------------------------------------------------------
    # Validate conversation ID
    # -------------------------------------------------------------

    try:
        conversation_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid conversation ID.",
        )

    # -------------------------------------------------------------
    # Load conversation
    # -------------------------------------------------------------

    model = await db.get(
        ConversationModel,
        conversation_uuid,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # -------------------------------------------------------------
    # Convert persistence model → application model
    # -------------------------------------------------------------

    messages = [
        Message(**message)
        if isinstance(message, dict)
        else message
        for message in (model.messages or [])
    ]

    state = WorkflowState(
        **(model.state or {})
    )

    workflow = None

    if model.workflow:
        workflow = GeneratedWorkflow(
            **model.workflow
        )

    conversation = Conversation(
        id=str(model.id),
        title=model.title,
        messages=messages,
        state=state,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

    # -------------------------------------------------------------
    # Process message through the orchestrator
    # -------------------------------------------------------------

    llm = get_llm_provider()

    (
        updated,
        assistant_message,
        generated_workflow,
        requirements,
    ) = await process_message(
        conversation=conversation,
        user_text=req.message,
        llm=llm,
    )

    # -------------------------------------------------------------
    # Persist updated conversation
    # -------------------------------------------------------------

    model.messages = [
        message.model_dump(mode="json")
        for message in updated.messages
    ]

    model.state = updated.state.model_dump(
        mode="json"
    )

    model.status = updated.state.status.value

    if generated_workflow is not None:
        model.workflow = generated_workflow.model_dump(
            mode="json"
        )

    await db.commit()

    # -------------------------------------------------------------
    # Build API response
    # -------------------------------------------------------------

    return ChatResponse(
        message=assistant_message,
        workflow_ready=(
            updated.state.status == WorkflowStatus.GENERATED
        ),
        state=updated.state,
        workflow=generated_workflow,
        requirements=requirements,
        ambiguities=updated.state.ambiguities,
        conflicts=updated.state.conflicts,
    )