from app.schemas.requirement import RequirementStatus
from app.schemas.workflow import (
    Action,
    Condition,
    Intent,
    Trigger,
    WorkflowState,
)
from app.services.requirement_service import RequirementService


def test_empty_state_requires_intent_trigger_and_action():
    service = RequirementService()
    state = WorkflowState()

    requirements = service.evaluate(state)

    requirement_ids = {
        requirement.id
        for requirement in requirements
        if requirement.status == RequirementStatus.MISSING
    }

    assert "workflow.intent" in requirement_ids
    assert "trigger.type" in requirement_ids
    assert "action" in requirement_ids


def test_existing_condition_is_not_marked_missing():
    service = RequirementService()

    state = WorkflowState(
        intent=Intent(
            goal="invoice_notification"
        ),
        trigger=Trigger(
            type="invoice_received"
        ),
        conditions=[
            Condition(
                field="invoice.amount",
                operator=">",
                value=10000,
                currency="INR",
            )
        ],
        actions=[
            Action(
                type="notification",
                provider="gmail",
            )
        ],
        duplicate_handling=True,
    )

    requirements = service.evaluate(state)

    condition_requirements = [
        requirement
        for requirement in requirements
        if requirement.id == "condition"
    ]

    assert condition_requirements == []


def test_action_without_provider_requires_provider():
    service = RequirementService()

    state = WorkflowState(
        intent=Intent(
            goal="invoice_notification"
        ),
        trigger=Trigger(
            type="invoice_received"
        ),
        conditions=[
            Condition(
                field="invoice.amount",
                operator=">",
                value=10000,
                currency="INR",
            )
        ],
        actions=[
            Action(
                type="notification"
            )
        ],
    )

    requirements = service.evaluate(state)

    provider_requirements = [
        requirement
        for requirement in requirements
        if requirement.id == "action.0.provider"
    ]

    assert len(provider_requirements) == 1
    assert (
        provider_requirements[0].status
        == RequirementStatus.MISSING
    )


def test_duplicate_handling_is_required_when_missing():
    service = RequirementService()

    state = WorkflowState(
        intent=Intent(
            goal="invoice_notification"
        ),
        trigger=Trigger(
            type="invoice_received"
        ),
        conditions=[
            Condition(
                field="invoice.amount",
                operator=">",
                value=10000,
                currency="INR",
            )
        ],
        actions=[
            Action(
                type="notification",
                provider="gmail",
            )
        ],
    )

    requirements = service.evaluate(state)

    duplicate_requirement = next(
        requirement
        for requirement in requirements
        if requirement.id == "duplicate_handling"
    )

    assert duplicate_requirement.status == RequirementStatus.MISSING
    assert duplicate_requirement.required is True
    assert (
        duplicate_requirement.question
        == "Should duplicate invoices be ignored?"
    )


def test_duplicate_handling_true_is_satisfied():
    service = RequirementService()

    state = WorkflowState(
        intent=Intent(
            goal="invoice_notification"
        ),
        trigger=Trigger(
            type="invoice_received"
        ),
        conditions=[
            Condition(
                field="invoice.amount",
                operator=">",
                value=10000,
                currency="INR",
            )
        ],
        actions=[
            Action(
                type="notification",
                provider="gmail",
            )
        ],
        duplicate_handling=True,
    )

    requirements = service.evaluate(state)

    duplicate_requirement = next(
        requirement
        for requirement in requirements
        if requirement.id == "duplicate_handling"
    )

    assert (
        duplicate_requirement.status
        == RequirementStatus.SATISFIED
    )


def test_duplicate_handling_false_is_satisfied():
    service = RequirementService()

    state = WorkflowState(
        intent=Intent(
            goal="invoice_notification"
        ),
        trigger=Trigger(
            type="invoice_received"
        ),
        conditions=[
            Condition(
                field="invoice.amount",
                operator=">",
                value=10000,
                currency="INR",
            )
        ],
        actions=[
            Action(
                type="notification",
                provider="gmail",
            )
        ],
        duplicate_handling=False,
    )

    requirements = service.evaluate(state)

    duplicate_requirement = next(
        requirement
        for requirement in requirements
        if requirement.id == "duplicate_handling"
    )

    assert (
        duplicate_requirement.status
        == RequirementStatus.SATISFIED
    )


def test_complete_basic_workflow_has_no_missing_required_fields():
    service = RequirementService()

    state = WorkflowState(
        intent=Intent(
            goal="invoice_notification"
        ),
        trigger=Trigger(
            type="invoice_received"
        ),
        conditions=[
            Condition(
                field="invoice.amount",
                operator=">",
                value=10000,
                currency="INR",
            )
        ],
        actions=[
            Action(
                type="notification",
                provider="gmail",
            )
        ],
        duplicate_handling=True,
    )

    requirements = service.evaluate(state)

    missing_required = [
        requirement
        for requirement in requirements
        if requirement.required
        and requirement.status == RequirementStatus.MISSING
    ]

    assert missing_required == []