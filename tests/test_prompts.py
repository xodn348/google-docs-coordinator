from src.prompts import build_user_prompt
from src.models.google_models import Revision


def test_build_user_prompt_includes_document_header(
    sample_comment, sample_revision, sample_metadata
):
    prompt = build_user_prompt([sample_comment], [sample_revision], sample_metadata)

    assert "## Document: Test Document" in prompt
    assert "Document ID: doc-123" in prompt


def test_build_user_prompt_includes_comment_author_and_replies(
    sample_comment, sample_revision, sample_metadata
):
    prompt = build_user_prompt([sample_comment], [sample_revision], sample_metadata)

    assert "## UNRESOLVED COMMENTS" in prompt
    assert "**Author**: Alice" in prompt
    assert "**Replies** (1):" in prompt
    assert "- Bob: Friday works" in prompt


def test_build_user_prompt_handles_no_comments(sample_revision, sample_metadata):
    prompt = build_user_prompt([], [sample_revision], sample_metadata)

    assert "## COMMENTS: None found" in prompt


def test_build_user_prompt_groups_activity_by_user(sample_comment, sample_metadata):
    revisions = [
        Revision.from_api_response(
            {
                "id": "r1",
                "modifiedTime": "2026-02-21T08:00:00Z",
                "lastModifyingUser": {"displayName": "Carol"},
            }
        ),
        Revision.from_api_response(
            {
                "id": "r2",
                "modifiedTime": "2026-02-21T09:00:00Z",
                "lastModifyingUser": {"displayName": "Carol"},
            }
        ),
        Revision.from_api_response(
            {
                "id": "r3",
                "modifiedTime": "2026-02-21T07:00:00Z",
                "lastModifyingUser": {"displayName": "Alice"},
            }
        ),
    ]

    prompt = build_user_prompt([], revisions, sample_metadata)

    assert "## RECENT ACTIVITY (3 revisions)" in prompt
    assert "**Carol**: 2 edits" in prompt
    assert "**Alice**: 1 edits" in prompt


def test_build_user_prompt_handles_no_revisions(sample_comment, sample_metadata):
    prompt = build_user_prompt([sample_comment], [], sample_metadata)

    assert "## ACTIVITY: No recent revisions" in prompt


def test_build_user_prompt_always_ends_with_instruction(
    sample_comment, sample_revision, sample_metadata
):
    prompt = build_user_prompt([sample_comment], [sample_revision], sample_metadata)

    assert "extract questions, decisions, and next steps" in prompt
