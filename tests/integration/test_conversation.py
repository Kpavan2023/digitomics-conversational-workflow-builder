import pytest

from app.llm.rule_based import RuleBasedProvider
from app.orchestrator.conversation_orchestrator import (
    ConversationOrchestrator,
)
from app.schemas.conversation import Conversation


@pytest.mark.asyncio
async def test_incomplete_workflow_asks_for_clarification():
    """
    An incomplete workflow request should:
    - extract the information already provided
    - preserve it in WorkflowState
    - detect missing requirements
    - ask a clarification question
    - avoid generating a workflow
    """

    conversation = Conversation(
        id="test-conversation",
        title="Invoice notification",
    )

    orchestrator = ConversationOrchestrator(
        llm=RuleBasedProvider()
    )

    updated_conversation, assistant_message, workflow, requirements = (
        await orchestrator.process_message(
            conversation=conversation,
            user_text=(
                "I want to get notified when I receive "
                "an invoice above ₹50,000."
            ),
        )
    )

    # Information supplied by the user must be preserved.
    assert updated_conversation.state.intent.goal is not None

    assert len(
        updated_conversation.state.conditions
    ) == 1

    condition = updated_conversation.state.conditions[0]

    assert condition.field == "invoice.amount"
    assert condition.operator == ">"
    assert condition.value == 50000

    # The workflow is incomplete, so it must not be generated.
    assert workflow is None

    # The assistant must ask for more information.
    assert assistant_message is not None
    assert assistant_message

    # At least one required requirement should remain unresolved.
    unresolved_required = [
        requirement
        for requirement in requirements
        if requirement.required
        and requirement.status.value
        in {"missing", "ambiguous", "conflicting"}
    ]

    assert unresolved_required


@pytest.mark.asyncio
async def test_follow_up_information_is_merged_into_existing_conversation():
    """
    Information provided in a follow-up message should be merged into
    the existing workflow state rather than replacing previously
    collected information.
    """

    conversation = Conversation(
        id="test-conversation",
        title="Invoice notification",
    )

    orchestrator = ConversationOrchestrator(
        llm=RuleBasedProvider()
    )

    # First turn.
    conversation, assistant_message, workflow, requirements = (
        await orchestrator.process_message(
            conversation=conversation,
            user_text=(
                "I want to get notified when I receive "
                "an invoice above ₹50,000."
            ),
        )
    )

    # Workflow must still be incomplete.
    assert workflow is None

    # Previously collected condition must be preserved.
    assert len(conversation.state.conditions) == 1

    condition = conversation.state.conditions[0]

    assert condition.field == "invoice.amount"
    assert condition.operator == ">"
    assert condition.value == 50000

    # Second turn.
    conversation, assistant_message, workflow, requirements = (
        await orchestrator.process_message(
            conversation=conversation,
            user_text="Send a notification to Slack.",
        )
    )

    # Original condition must still exist.
    assert len(conversation.state.conditions) == 1

    condition = conversation.state.conditions[0]

    assert condition.field == "invoice.amount"
    assert condition.operator == ">"
    assert condition.value == 50000

    # Follow-up should have produced an action.
    assert len(conversation.state.actions) >= 1