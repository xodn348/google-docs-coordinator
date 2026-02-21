import pytest
from datetime import datetime, timezone

from src.models.google_models import User, Comment, Reply, Revision, DocumentMetadata
from src.models.coordination_models import (
    Question,
    Decision,
    NextStep,
    DataCompleteness,
    CoordinationSnapshot,
)
from src.config import Settings


@pytest.fixture
def sample_user_data():
    return {
        "displayName": "Alice Smith",
        "emailAddress": "alice@example.com",
        "photoLink": "https://photo.example.com/alice",
    }


@pytest.fixture
def sample_comment_data():
    return {
        "id": "comment-1",
        "content": "Should we use React or Vue for this?",
        "author": {"displayName": "Alice Smith", "emailAddress": "alice@example.com"},
        "createdTime": "2026-02-20T10:00:00Z",
        "modifiedTime": "2026-02-20T10:30:00Z",
        "resolved": False,
        "quotedFileContent": {"value": "Frontend framework selection"},
        "replies": [
            {
                "id": "reply-1",
                "content": "I think React would be better for our use case",
                "author": {"displayName": "Bob Johnson"},
                "createdTime": "2026-02-20T11:00:00Z",
                "modifiedTime": "2026-02-20T11:00:00Z",
            }
        ],
    }


@pytest.fixture
def sample_resolved_comment_data():
    return {
        "id": "comment-2",
        "content": "Let's go with React",
        "author": {"displayName": "Alice Smith"},
        "createdTime": "2026-02-20T12:00:00Z",
        "modifiedTime": "2026-02-20T12:30:00Z",
        "resolved": True,
        "replies": [],
    }


@pytest.fixture
def sample_revision_data():
    return {
        "id": "rev-1",
        "modifiedTime": "2026-02-21T08:00:00Z",
        "lastModifyingUser": {
            "displayName": "Carol Lee",
            "emailAddress": "carol@example.com",
        },
    }


@pytest.fixture
def sample_doc_api_response():
    return {
        "documentId": "doc-abc-123",
        "title": "Team Project Proposal",
        "revisionId": "rev-latest",
    }


@pytest.fixture
def sample_comment():
    return Comment.from_api_response(
        {
            "id": "c1",
            "content": "What about the deadline?",
            "author": {"displayName": "Alice"},
            "createdTime": "2026-02-20T10:00:00Z",
            "resolved": False,
            "replies": [
                {
                    "id": "r1",
                    "content": "Friday works",
                    "author": {"displayName": "Bob"},
                    "createdTime": "2026-02-20T11:00:00Z",
                }
            ],
        }
    )


@pytest.fixture
def sample_revision():
    return Revision.from_api_response(
        {
            "id": "rev1",
            "modifiedTime": "2026-02-21T08:00:00Z",
            "lastModifyingUser": {"displayName": "Carol"},
        }
    )


@pytest.fixture
def sample_metadata():
    return DocumentMetadata(
        document_id="doc-123", title="Test Document", revision_id="rev-1"
    )


@pytest.fixture
def sample_snapshot(sample_metadata):
    return CoordinationSnapshot(
        document_id="doc-123",
        document_title="Test Document",
        generated_at=datetime(2026, 2, 21, 12, 0, 0, tzinfo=timezone.utc),
        since_hours=48,
        contributors=["Alice", "Bob", "Carol"],
        questions=[
            Question(
                text="What about the deadline?",
                author="Alice",
                context="Project timeline section",
                priority="high",
            )
        ],
        decisions=[
            Decision(
                summary="Use React for frontend",
                decided_by="Alice, Bob",
                date=datetime(2026, 2, 20, tzinfo=timezone.utc),
                context="From comment thread",
            )
        ],
        next_steps=[
            NextStep(
                description="Finalize budget by Friday",
                assignee="Carol",
                priority="high",
                rationale="Blocking other work",
            )
        ],
        data_completeness=DataCompleteness(
            comments_fetched=True,
            activity_fetched=True,
            metadata_fetched=True,
            ai_analysis_completed=True,
            errors=[],
        ),
        raw_comment_count=5,
        raw_revision_count=12,
    )


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    return Settings()
