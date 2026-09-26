from app.schemas.workflow import (
    Action,
    Condition,
    Intent,
    Trigger,
    WorkflowState,
)
from app.services.ambiguity_service import AmbiguityService


def test_complete_workflow_has_no_ambiguity_or_conflict():
    service = AmbiguityService()

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

    ambiguities, conflicts = service.evaluate(state)

    assert ambiguities == []
    assert conflicts == []


def test_schedule_without_configuration_is_ambiguous():
    service = AmbiguityService()

    state = WorkflowState(
        intent=Intent(
            goal="scheduled_notification"
        ),
        trigger=Trigger(
            type="schedule"
        ),
        actions=[
            Action(
                type="notification",
                provider="gmail",
            )
        ],
    )

    ambiguities, conflicts = service.evaluate(state)

    assert (
        "The schedule trigger does not contain scheduling details."
        in ambiguities
    )
    assert conflicts == []


def test_notification_without_provider_is_ambiguous():
    service = AmbiguityService()

    state = WorkflowState(
        intent=Intent(
            goal="invoice_notification"
        ),
        trigger=Trigger(
            type="invoice_received"
        ),
        actions=[
            Action(
                type="notification"
            )
        ],
    )

    ambiguities, conflicts = service.evaluate(state)

    assert (
        "Notification action 1 does not specify a provider."
        in ambiguities
    )
    assert conflicts == []


def test_contradictory_conditions_are_detected():
    service = AmbiguityService()

    state = WorkflowState(
        intent=Intent(
            goal="invoice_workflow"
        ),
        trigger=Trigger(
            type="invoice_received"
        ),
        conditions=[
            Condition(
                field="invoice.amount",
                operator=">",
                value=10000,
            ),
            Condition(
                field="invoice.amount",
                operator="<",
                value=5000,
            ),
        ],
        actions=[
            Action(
                type="notification",
                provider="gmail",
            )
        ],
    )

    ambiguities, conflicts = service.evaluate(state)

    assert ambiguities == []
    assert len(conflicts) == 1
    assert "Conflicting conditions" in conflicts[0]


def test_conditions_on_different_fields_do_not_conflict():
    service = AmbiguityService()

    state = WorkflowState(
        intent=Intent(
            goal="conditional_workflow"
        ),
        trigger=Trigger(
            type="invoice_received"
        ),
        conditions=[
            Condition(
                field="invoice.amount",
                operator=">",
                value=10000,
            ),
            Condition(
                field="invoice.currency",
                operator="=",
                value="INR",
            ),
        ],
        actions=[
            Action(
                type="notification",
                provider="gmail",
            )
        ],
    )

    ambiguities, conflicts = service.evaluate(state)

    assert ambiguities == []
    assert conflicts == []