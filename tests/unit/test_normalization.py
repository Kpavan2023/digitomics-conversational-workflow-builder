from app.schemas.extraction import ExtractionResult
from app.schemas.workflow import WorkflowState
from app.services.normalization_service import NormalizationService


def test_condition_is_added_to_empty_state():
    service = NormalizationService()
    state = WorkflowState()

    extraction = ExtractionResult(
        condition={
            "field": "invoice.amount",
            "operator": ">",
            "value": 10000,
            "currency": "INR",
        }
    )

    updated_state = service.normalize_and_merge(
        state,
        extraction,
    )

    assert len(updated_state.conditions) == 1

    condition = updated_state.conditions[0]

    assert condition.field == "invoice.amount"
    assert condition.operator == ">"
    assert condition.value == 10000
    assert condition.currency == "INR"


def test_action_does_not_erase_existing_condition():
    service = NormalizationService()
    state = WorkflowState()

    condition_extraction = ExtractionResult(
        condition={
            "field": "invoice.amount",
            "operator": ">",
            "value": 10000,
            "currency": "INR",
        }
    )

    state = service.normalize_and_merge(
        state,
        condition_extraction,
    )

    action_extraction = ExtractionResult(
        action={
            "type": "notification",
            "provider": "gmail",
        }
    )

    updated_state = service.normalize_and_merge(
        state,
        action_extraction,
    )

    assert len(updated_state.conditions) == 1
    assert len(updated_state.actions) == 1

    assert updated_state.conditions[0].value == 10000
    assert updated_state.actions[0].type == "notification"
    assert updated_state.actions[0].provider == "gmail"


def test_existing_condition_is_updated_instead_of_duplicated():
    service = NormalizationService()
    state = WorkflowState()

    first_extraction = ExtractionResult(
        condition={
            "field": "invoice.amount",
            "operator": ">",
            "value": 10000,
            "currency": "INR",
        }
    )

    state = service.normalize_and_merge(
        state,
        first_extraction,
    )

    second_extraction = ExtractionResult(
        condition={
            "field": "invoice.amount",
            "operator": ">",
            "value": 20000,
            "currency": "INR",
        }
    )

    updated_state = service.normalize_and_merge(
        state,
        second_extraction,
    )

    assert len(updated_state.conditions) == 1
    assert updated_state.conditions[0].value == 20000

def test_intent_is_converted_and_preserved():
    from app.schemas.extraction import (
        ExtractedIntent,
        ExtractionResult,
    )
    from app.schemas.workflow import Intent, WorkflowState

    service = NormalizationService()

    current_state = WorkflowState(
        intent=Intent(
            goal="invoice notification",
            confidence=0.9,
        )
    )

    extraction = ExtractionResult(
        intent=ExtractedIntent(
            goal=None,
            confidence=None,
        )
    )

    new_state = service.normalize_and_merge(
        current_state,
        extraction,
    )

    assert new_state.intent.goal == "invoice notification"
    assert new_state.intent.confidence == 0.9