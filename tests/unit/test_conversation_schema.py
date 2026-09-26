from app.schemas.conversation import ChatRequest, ChatResponse
from app.schemas.workflow import WorkflowState


def test_chat_request_accepts_user_message():
    request = ChatRequest(
        message="Send me a notification when an invoice exceeds 10000."
    )

    assert request.message.startswith("Send me a notification")


def test_chat_response_defaults_to_not_ready():
    response = ChatResponse(
        message="What event should trigger the workflow?",
        state=WorkflowState(),
    )

    assert response.workflow_ready is False
    assert response.requirements == []
    assert response.ambiguities == []
    assert response.conflicts == []


def test_chat_response_can_represent_ready_workflow():
    response = ChatResponse(
        message="Your workflow is ready.",
        workflow_ready=True,
        state=WorkflowState(),
    )

    assert response.workflow_ready is True
    assert response.message == "Your workflow is ready."