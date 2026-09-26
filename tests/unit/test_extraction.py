import pytest

from app.llm.rule_based import RuleBasedProvider
from app.schemas.extraction import (
    ExtractedAction,
    ExtractedCondition,
    ExtractedTrigger,
)
from app.schemas.workflow import Trigger, WorkflowState


@pytest.fixture
def provider():
    return RuleBasedProvider()


# ================================================================
# Initial extraction
# ================================================================


@pytest.mark.asyncio
async def test_initial_invoice_message_extracts_condition(provider):
    """
    Regression test for the original repeated-question bug.

    The user's first message already contains the invoice threshold.
    The extractor must capture it immediately.
    """

    message = (
        "Can you create a workflow that automatically sends "
        "a notification whenever I receive an invoice above ₹10,000?"
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.condition is not None

    assert result.condition.field == "invoice.amount"
    assert result.condition.operator == ">"
    assert result.condition.value == 10000
    assert result.condition.currency == "INR"


@pytest.mark.asyncio
async def test_initial_invoice_message_extracts_trigger(provider):
    """
    The initial message explicitly says the workflow starts
    when an invoice is received.
    """

    message = (
        "Send a notification whenever I receive "
        "an invoice above ₹10,000."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.trigger is not None
    assert result.trigger.type == "email"


@pytest.mark.asyncio
async def test_gmail_is_extracted_as_trigger_provider(provider):
    """
    Gmail should be extracted only when explicitly mentioned.
    """

    message = (
        "Whenever I receive an invoice in Gmail, "
        "send a notification."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.trigger is not None
    assert result.trigger.type == "email"
    assert result.trigger.provider == "gmail"


@pytest.mark.asyncio
async def test_slack_is_extracted_as_notification_provider(provider):
    """
    Slack should become the notification action provider
    when the user explicitly mentions Slack.
    """

    message = (
        "Whenever I receive an invoice above ₹10,000, "
        "send a notification to Slack."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.action is not None
    assert result.action.type == "notification"
    assert result.action.provider == "slack"


# ================================================================
# Condition extraction
# ================================================================


@pytest.mark.asyncio
async def test_numeric_amount_is_extracted(provider):
    """
    Numeric amounts should be parsed correctly.
    """

    message = (
        "Notify me when the invoice amount is above 25000."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.condition is not None
    assert result.condition.operator == ">"
    assert result.condition.value == 25000


@pytest.mark.asyncio
async def test_number_word_amount_is_extracted(provider):
    """
    Number words should be parsed without raising an exception.
    """

    message = (
        "Notify me when the invoice amount is above ten thousand rupees."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.condition is not None
    assert result.condition.operator == ">"
    assert result.condition.value == 10000
    assert result.condition.currency == "INR"


@pytest.mark.asyncio
async def test_missing_provider_is_not_invented(provider):
    """
    If the user does not specify Gmail, Outlook, etc.,
    the extractor must not invent one.
    """

    message = (
        "Send a notification whenever I receive "
        "an invoice above ₹10,000."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.trigger is not None
    assert result.trigger.type == "email"
    assert result.trigger.provider is None


@pytest.mark.asyncio
async def test_missing_condition_is_not_invented(provider):
    """
    If the user only describes an invoice notification,
    the extractor must not invent an amount condition.
    """

    message = (
        "Send me a notification whenever I receive an invoice."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.condition is None


@pytest.mark.asyncio
async def test_missing_action_provider_is_not_invented(provider):
    """
    A notification action may be identified without assuming
    which platform should receive it.
    """

    message = (
        "Whenever I receive an invoice above ₹10,000, "
        "send me a notification."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.action is not None
    assert result.action.type == "notification"
    assert result.action.provider is None


@pytest.mark.asyncio
async def test_initial_message_extracts_multiple_facts(provider):
    """
    A single user message may contain multiple workflow facts.
    The extractor must capture all explicitly provided facts.
    """

    message = (
        "Whenever I receive an invoice in Gmail above ₹10,000, "
        "send a notification to Slack."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    # Trigger
    assert result.trigger is not None
    assert result.trigger.type == "email"
    assert result.trigger.provider == "gmail"

    # Condition
    assert result.condition is not None
    assert result.condition.field == "invoice.amount"
    assert result.condition.operator == ">"
    assert result.condition.value == 10000
    assert result.condition.currency == "INR"

    # Action
    assert result.action is not None
    assert result.action.type == "notification"
    assert result.action.provider == "slack"


@pytest.mark.asyncio
async def test_condition_update_can_be_extracted(provider):
    """
    A later message containing a new threshold should produce
    a new extraction that normalization can use to update the
    canonical condition.
    """

    message = "Actually, make the threshold above ₹20,000."

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.condition is not None
    assert result.condition.field == "invoice.amount"
    assert result.condition.operator == ">"
    assert result.condition.value == 20000
    assert result.condition.currency == "INR"


@pytest.mark.asyncio
async def test_vague_condition_is_not_treated_as_numeric(provider):
    """
    Terms such as 'high-value' are ambiguous and should not
    become an invented numeric threshold.
    """

    message = (
        "Send a notification whenever I receive a high-value invoice."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.condition is None
    assert result.raw_facts.get("ambiguous_condition") == "high-value"


# ================================================================
# Destination extraction
# ================================================================


@pytest.mark.asyncio
async def test_destination_is_preserved_in_action_configuration(provider):
    """
    An explicitly specified destination should be extracted
    rather than invented.
    """

    message = (
        "Whenever I receive an invoice above ₹10,000, "
        "send a notification to #finance-alerts."
    )

    result = await provider.extract_information(
        message,
        WorkflowState(),
    )

    assert result.action is not None
    assert result.action.type == "notification"
    assert (
        result.action.configuration["destination"]
        == "#finance-alerts"
    )


# ================================================================
# Duplicate handling
# ================================================================


@pytest.mark.asyncio
async def test_duplicate_handling_yes_is_extracted(provider):
    """
    When duplicate handling is the active requirement,
    a standalone 'Yes' means duplicate invoices should be ignored.
    """

    state = WorkflowState(
        active_requirement_id="duplicate_handling"
    )

    result = await provider.extract_information(
        "Yes",
        state,
    )

    assert result.duplicate_handling is True


@pytest.mark.asyncio
async def test_duplicate_handling_no_is_extracted(provider):
    """
    When duplicate handling is the active requirement,
    a standalone 'No' means duplicate invoices should not
    be ignored.
    """

    state = WorkflowState(
        active_requirement_id="duplicate_handling"
    )

    result = await provider.extract_information(
        "No",
        state,
    )

    assert result.duplicate_handling is False


@pytest.mark.asyncio
async def test_duplicate_handling_ignore_is_extracted(provider):
    """
    Explicit instructions to ignore duplicate invoices
    should produce True.
    """

    state = WorkflowState(
        active_requirement_id="duplicate_handling"
    )

    result = await provider.extract_information(
        "Ignore duplicate invoices",
        state,
    )

    assert result.duplicate_handling is True


@pytest.mark.asyncio
async def test_duplicate_handling_allow_is_extracted(provider):
    """
    Explicit instructions to allow duplicate invoices
    should produce False.
    """

    state = WorkflowState(
        active_requirement_id="duplicate_handling"
    )

    result = await provider.extract_information(
        "Allow duplicate invoices",
        state,
    )

    assert result.duplicate_handling is False


@pytest.mark.asyncio
async def test_yes_does_not_become_duplicate_handling_without_active_requirement(
    provider,
):
    """
    A standalone 'Yes' must not be interpreted as duplicate
    handling unless the duplicate_handling requirement is active.

    This protects other clarification questions from accidentally
    modifying duplicate-handling state.
    """

    state = WorkflowState(
        active_requirement_id="condition"
    )

    result = await provider.extract_information(
        "Yes",
        state,
    )

    assert result.duplicate_handling is None


# ================================================================
# Gmail monitor location
# ================================================================


@pytest.mark.asyncio
async def test_gmail_monitor_location_is_extracted(provider):
    """
    When the Gmail monitor-location requirement is active,
    the user's label/folder answer should be extracted.
    """

    state = WorkflowState(
        active_requirement_id="trigger.location",
        trigger=Trigger(
            type="invoice.created",
            provider="gmail",
        ),
    )

    result = await provider.extract_information(
        "Invoices",
        state,
    )

    assert result.trigger is not None
    assert result.trigger.type == "invoice.created"
    assert result.trigger.provider == "gmail"
    assert (
        result.trigger.configuration["location"]
        == "Invoices"
    )


@pytest.mark.asyncio
async def test_gmail_monitor_location_preserves_existing_trigger(
    provider,
):
    """
    Adding the Gmail monitor location must not erase existing
    trigger information or configuration.
    """

    state = WorkflowState(
        active_requirement_id="trigger.location",
        trigger=Trigger(
            type="invoice.created",
            provider="gmail",
            configuration={
                "event": "invoice.created",
            },
        ),
    )

    result = await provider.extract_information(
        "Invoices",
        state,
    )

    assert result.trigger is not None
    assert result.trigger.type == "invoice.created"
    assert result.trigger.provider == "gmail"

    assert (
        result.trigger.configuration["event"]
        == "invoice.created"
    )

    assert (
        result.trigger.configuration["location"]
        == "Invoices"
    )


@pytest.mark.asyncio
async def test_monitor_location_is_not_extracted_without_active_requirement(
    provider,
):
    """
    A word such as 'Invoices' must not automatically become a
    Gmail monitor location unless the backend has explicitly asked
    for trigger.location.

    This prevents accidental extraction from unrelated messages.
    """

    state = WorkflowState(
        trigger=Trigger(
            type="invoice.created",
            provider="gmail",
        ),
    )

    result = await provider.extract_information(
        "Invoices",
        state,
    )

    assert (
        result.trigger is None
        or "location" not in result.trigger.configuration
    )


@pytest.mark.asyncio
async def test_explicit_gmail_label_is_extracted(provider):
    """
    Explicit phrases such as 'Gmail label Vendor Invoices'
    should also produce the monitor location.
    """

    state = WorkflowState(
        active_requirement_id="trigger.location",
        trigger=Trigger(
            type="invoice.created",
            provider="gmail",
        ),
    )

    result = await provider.extract_information(
        "Gmail label Vendor Invoices",
        state,
    )

    assert result.trigger is not None
    assert (
        result.trigger.configuration["location"]
        == "Vendor Invoices"
    )