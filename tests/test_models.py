from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models.coordination_models import (
    CoordinationSnapshot,
    DataCompleteness,
    Decision,
    NextStep,
    Question,
)
from src.models.google_models import Comment, DocumentMetadata, Reply, Revision, User


def test_user_from_api_response_maps_fields(sample_user_data):
    user = User.from_api_response(sample_user_data)

    assert user.display_name == "Alice Smith"
    assert user.email == "alice@example.com"
    assert user.photo_link == "https://photo.example.com/alice"


def test_user_from_api_response_defaults_display_name_when_missing():
    user = User.from_api_response({})

    assert user.display_name == "Unknown"
    assert user.email is None
    assert user.photo_link is None


def test_reply_from_api_response_parses_timestamps(sample_comment_data):
    reply = Reply.from_api_response(sample_comment_data["replies"][0])

    assert reply.id == "reply-1"
    assert reply.created_time.tzinfo is not None
    assert reply.modified_time == datetime(2026, 2, 20, 11, 0, tzinfo=timezone.utc)


def test_reply_from_api_response_sets_modified_time_none_when_missing():
    reply = Reply.from_api_response(
        {
            "id": "r2",
            "content": "Looks good",
            "author": {"displayName": "Bob"},
            "createdTime": "2026-02-20T11:00:00Z",
        }
    )

    assert reply.modified_time is None


def test_comment_from_api_response_parses_nested_replies(sample_comment_data):
    comment = Comment.from_api_response(sample_comment_data)

    assert comment.id == "comment-1"
    assert comment.quoted_content == "Frontend framework selection"
    assert len(comment.replies) == 1
    assert comment.replies[0].author.display_name == "Bob Johnson"


def test_comment_from_api_response_defaults_empty_content_and_replies():
    comment = Comment.from_api_response(
        {
            "id": "comment-empty",
            "author": {"displayName": "Alice"},
            "createdTime": "2026-02-20T10:00:00Z",
        }
    )

    assert comment.content == ""
    assert comment.replies == []
    assert comment.resolved is False
    assert comment.quoted_content is None


def test_revision_from_api_response_parses_optional_user_and_size(sample_revision_data):
    revision = Revision.from_api_response({**sample_revision_data, "size": 512})

    assert revision.id == "rev-1"
    assert revision.last_modifying_user is not None
    assert revision.last_modifying_user.display_name == "Carol Lee"
    assert revision.size == 512


def test_revision_from_api_response_handles_missing_user(sample_revision_data):
    revision = Revision.from_api_response(
        {
            "id": sample_revision_data["id"],
            "modifiedTime": sample_revision_data["modifiedTime"],
        }
    )

    assert revision.last_modifying_user is None


def test_document_metadata_from_api_response_defaults_title_when_missing():
    metadata = DocumentMetadata.from_api_response({"documentId": "doc-1"})

    assert metadata.document_id == "doc-1"
    assert metadata.title == "Untitled"
    assert metadata.revision_id is None


def test_document_metadata_from_api_response_accepts_none_revision(
    sample_doc_api_response,
):
    metadata = DocumentMetadata.from_api_response(
        {**sample_doc_api_response, "revisionId": None}
    )

    assert metadata.revision_id is None


def test_question_rejects_invalid_priority():
    with pytest.raises(ValidationError):
        Question.model_validate({"text": "Q?", "author": "Alice", "priority": "urgent"})


def test_next_step_defaults_priority_and_optional_fields():
    step = NextStep(description="Do thing")

    assert step.priority == "medium"
    assert step.assignee is None
    assert step.rationale is None
    assert step.source is None


def test_data_completeness_defaults_empty_error_list():
    completeness = DataCompleteness()

    assert completeness.errors == []
    assert completeness.comments_fetched is False


def test_coordination_snapshot_allows_empty_analysis_lists(sample_metadata):
    snapshot = CoordinationSnapshot(
        document_title=sample_metadata.title,
        document_id=sample_metadata.document_id,
        generated_at=datetime(2026, 2, 21, tzinfo=timezone.utc),
        since_hours=48,
        data_completeness=DataCompleteness(),
    )

    assert snapshot.questions == []
    assert snapshot.decisions == []
    assert snapshot.next_steps == []
    assert snapshot.contributors == []


def test_coordination_snapshot_tracks_raw_counts(sample_snapshot):
    assert sample_snapshot.raw_comment_count == 5
    assert sample_snapshot.raw_revision_count == 12
    assert isinstance(sample_snapshot.decisions[0], Decision)
