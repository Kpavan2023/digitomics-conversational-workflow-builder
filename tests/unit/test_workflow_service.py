from app.schemas.workflow import (
    Action,
    Condition,
    Intent,
    Trigger,
    WorkflowState,
)
from app.services.workflow_service import WorkflowService


def build_state(
    *,
    duplicate_handling: bool | None = True,
    with_condition: bool = False,
) -> WorkflowState:
    conditions = []

    if with_condition:
        conditions.append(
            Condition(
                field="amount",
                operator="gt",
                value=10000,
                currency="INR",
            )
        )

    return WorkflowState(
        intent=Intent(
            goal="Notify me when a new invoice arrives.",
            confidence=1.0,
        ),
        trigger=Trigger(
            type="invoice.created",
            provider="gmail",
            configuration={
                "event": "invoice.created",
                "location": "Invoices",
            },
        ),
        conditions=conditions,
        condition_enabled=with_condition,
        actions=[
            Action(
                type="notification",
                provider="slack",
                configuration={
                    "destination": "#finance",
                    "provider_label": "Slack",
                },
            )
        ],
        duplicate_handling=duplicate_handling,
    )


def test_generates_trigger_action_and_end_nodes():
    service = WorkflowService()

    workflow = service.generate(build_state())

    assert [node.type for node in workflow.nodes] == [
        "trigger",
        "action",
        "end",
    ]


def test_generates_condition_when_condition_exists():
    service = WorkflowService()

    workflow = service.generate(
        build_state(with_condition=True)
    )

    assert [node.type for node in workflow.nodes] == [
        "trigger",
        "condition",
        "action",
        "end",
    ]


def test_preserves_gmail_trigger_configuration():
    service = WorkflowService()

    workflow = service.generate(build_state())

    trigger = workflow.nodes[0]

    assert trigger.type == "trigger"
    assert trigger.configuration["type"] == "invoice.created"
    assert trigger.configuration["provider"] == "gmail"
    assert trigger.configuration["location"] == "Invoices"


def test_preserves_slack_action_configuration():
    service = WorkflowService()

    workflow = service.generate(build_state())

    action = next(
        node for node in workflow.nodes
        if node.type == "action"
    )

    assert action.configuration["provider"] == "slack"
    assert action.configuration["destination"] == "#finance"


def test_duplicate_handling_is_included_in_generated_workflow():
    service = WorkflowService()

    workflow = service.generate(
        build_state(duplicate_handling=True)
    )

    trigger = workflow.nodes[0]

    assert trigger.configuration["duplicate_handling"] == {
        "enabled": True,
        "strategy": "ignore",
    }


def test_duplicate_handling_false_is_preserved():
    service = WorkflowService()

    workflow = service.generate(
        build_state(duplicate_handling=False)
    )

    trigger = workflow.nodes[0]

    assert trigger.configuration["duplicate_handling"] == {
        "enabled": False,
        "strategy": "process",
    }


def test_unanswered_duplicate_handling_is_not_added():
    service = WorkflowService()

    workflow = service.generate(
        build_state(duplicate_handling=None)
    )

    trigger = workflow.nodes[0]

    assert "duplicate_handling" not in trigger.configuration