"""Workflow routes — get and validate generated workflows."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.conversation import ConversationModel
from app.schemas.workflow import (
    GeneratedWorkflow,
    StateResponse,
    ValidateWorkflowRequest,
    WorkflowResponse,
    WorkflowState,
)
from app.services.requirement_service import RequirementService
from app.services.validation_service import (
    ValidationService,
)
from app.services.workflow_service import WorkflowService


router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
)

requirement_service = RequirementService()
validation_service = ValidationService()
workflow_service = WorkflowService()


@router.get(
    "/{conversation_id}",
    response_model=WorkflowResponse,
)
async def get_workflow(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """
    Get the generated workflow for a conversation.
    """

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

    if not model:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    if not model.workflow:
        return WorkflowResponse(
            valid=False,
            errors=["Workflow not yet generated."],
        )

    workflow = GeneratedWorkflow(
        **model.workflow
    )

    state = WorkflowState(
        **model.state
    )

    valid, errors = validation_service.validate_workflow(
        workflow,
        state,
    )

    return WorkflowResponse(
        workflow=workflow,
        valid=valid,
        errors=errors,
    )


@router.get(
    "/{conversation_id}/state",
    response_model=StateResponse,
)
async def get_state(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> StateResponse:
    """
    Get the current workflow state and evaluated requirements.
    """

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

    if not model:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    state = WorkflowState(
        **model.state
    )

    requirements = requirement_service.evaluate(
        state
    )

    return StateResponse(
        state=state,
        requirements=requirements,
    )


@router.post(
    "/validate",
    response_model=WorkflowResponse,
)
async def validate_state(
    req: ValidateWorkflowRequest,
) -> WorkflowResponse:
    """
    Validate and generate a workflow from a workflow state
    without persisting it.
    """

    state = req.state

    if not validation_service.is_workflow_complete(
        state
    ):
        return WorkflowResponse(
            valid=False,
            errors=["Workflow is not complete."],
        )

    workflow = workflow_service.generate(
        state
    )

    valid, errors = validation_service.validate_workflow(
        workflow,
        state,
    )

    return WorkflowResponse(
        workflow=workflow,
        valid=valid,
        errors=errors,
    )