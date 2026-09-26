from app.schemas.requirement import (
    Requirement,
    RequirementStatus,
)
from app.schemas.workflow import WorkflowState
from app.services.question_service import QuestionService


def test_returns_highest_priority_missing_question():
    service = QuestionService()
    state = WorkflowState()

    requirements = [
        Requirement(
            id="action.provider",
            description="Notification provider",
            status=RequirementStatus.MISSING,
            required=True,
            question="Which notification platform should be used?",
            priority=50,
        ),
        Requirement(
            id="trigger.type",
            description="Trigger event",
            status=RequirementStatus.MISSING,
            required=True,
            question="What event should trigger the workflow?",
            priority=20,
        ),
    ]

    question = service.get_next_question(
        state,
        requirements,
    )

    assert question == "What event should trigger the workflow?"


def test_does_not_return_satisfied_requirement():
    service = QuestionService()
    state = WorkflowState()

    requirements = [
        Requirement(
            id="action.provider",
            description="Notification provider",
            status=RequirementStatus.SATISFIED,
            required=True,
            question="Which notification platform should be used?",
            priority=50,
        ),
    ]

    question = service.get_next_question(
        state,
        requirements,
    )

    assert question is None


def test_returns_none_when_all_required_information_exists():
    service = QuestionService()
    state = WorkflowState()

    requirements = [
        Requirement(
            id="workflow.intent",
            description="Workflow intent",
            status=RequirementStatus.SATISFIED,
            required=True,
            question="What should this workflow automate?",
            priority=10,
        ),
        Requirement(
            id="action.provider",
            description="Notification provider",
            status=RequirementStatus.SATISFIED,
            required=True,
            question="Which notification platform should be used?",
            priority=50,
        ),
    ]

    question = service.get_next_question(
        state,
        requirements,
    )

    assert question is None


def test_ambiguous_required_requirement_can_trigger_question():
    service = QuestionService()
    state = WorkflowState()

    requirements = [
        Requirement(
            id="trigger.type",
            description="Trigger event",
            status=RequirementStatus.AMBIGUOUS,
            required=True,
            question="Could you clarify what event should trigger the workflow?",
            priority=20,
        ),
    ]

    question = service.get_next_question(
        state,
        requirements,
    )

    assert question == (
        "Could you clarify what event should trigger the workflow?"
    )


def test_conflicting_required_requirement_can_trigger_question():
    service = QuestionService()
    state = WorkflowState()

    requirements = [
        Requirement(
            id="condition",
            description="Workflow condition",
            status=RequirementStatus.CONFLICTING,
            required=True,
            question="Which condition should the workflow use?",
            priority=30,
        ),
    ]

    question = service.get_next_question(
        state,
        requirements,
    )

    assert question == "Which condition should the workflow use?"