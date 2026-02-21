from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from src.services.google_client import (
    GoogleDocsClient,
    InMemoryCache,
    should_retry_http_error,
)


@pytest.fixture
def client(mock_settings, mocker):
    mocker.patch(
        "src.services.google_client.get_google_credentials", return_value=Mock()
    )
    drive = Mock()
    docs = Mock()
    mocker.patch("src.services.google_client.build_drive_service", return_value=drive)
    mocker.patch("src.services.google_client.build_docs_service", return_value=docs)
    return GoogleDocsClient(mock_settings), drive, docs


def test_cache_returns_value_before_ttl_expiry(mocker):
    cache = InMemoryCache(ttl_seconds=10)
    mocker.patch("src.services.google_client.time.time", side_effect=[100.0, 105.0])

    cache.set("k", "v")

    assert cache.get("k") == "v"


def test_cache_expires_value_after_ttl(mocker):
    cache = InMemoryCache(ttl_seconds=5)
    mocker.patch("src.services.google_client.time.time", side_effect=[100.0, 106.0])

    cache.set("k", "v")

    assert cache.get("k") is None


def test_cache_clear_removes_all_values():
    cache = InMemoryCache(ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)

    cache.clear()

    assert cache.get("a") is None
    assert cache.get("b") is None


def test_should_retry_http_error_retries_for_429():
    from googleapiclient.errors import HttpError

    response = type("Resp", (), {"status": 429, "reason": "rate limit"})()

    assert should_retry_http_error(HttpError(response, b"{}")) is True


def test_should_retry_http_error_does_not_retry_for_400():
    from googleapiclient.errors import HttpError

    response = type("Resp", (), {"status": 400, "reason": "bad request"})()

    assert should_retry_http_error(HttpError(response, b"{}")) is False


def test_fetch_comments_filters_resolved_comments(
    client, sample_comment_data, sample_resolved_comment_data
):
    instance, drive, _ = client
    drive.comments.return_value.list.return_value.execute.return_value = {
        "comments": [sample_comment_data, sample_resolved_comment_data]
    }

    comments, error = instance.fetch_comments("doc-1")

    assert error is None
    assert len(comments) == 1
    assert comments[0].id == "comment-1"


def test_fetch_comments_include_resolved_true_returns_all(
    client, sample_comment_data, sample_resolved_comment_data
):
    instance, drive, _ = client
    drive.comments.return_value.list.return_value.execute.return_value = {
        "comments": [sample_comment_data, sample_resolved_comment_data]
    }

    comments, error = instance.fetch_comments("doc-1", include_resolved=True)

    assert error is None
    assert {c.id for c in comments} == {"comment-1", "comment-2"}


def test_fetch_comments_uses_cache_on_second_call(client, sample_comment_data):
    instance, drive, _ = client
    drive.comments.return_value.list.return_value.execute.return_value = {
        "comments": [sample_comment_data]
    }

    first, _ = instance.fetch_comments("doc-cache")
    second, _ = instance.fetch_comments("doc-cache")

    assert len(first) == 1
    assert len(second) == 1
    assert drive.comments.return_value.list.call_count == 1


def test_fetch_comments_returns_error_on_api_failure(client):
    instance, drive, _ = client
    drive.comments.return_value.list.return_value.execute.side_effect = RuntimeError(
        "boom"
    )

    comments, error = instance.fetch_comments("doc-err")

    assert comments == []
    assert error is not None
    assert "Failed to fetch comments" in error


def test_fetch_revisions_filters_by_since_hours(client):
    instance, drive, _ = client
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old = (now - timedelta(hours=120)).strftime("%Y-%m-%dT%H:%M:%SZ")
    drive.revisions.return_value.list.return_value.execute.return_value = {
        "revisions": [
            {
                "id": "recent",
                "modifiedTime": recent,
                "lastModifyingUser": {"displayName": "Recent User"},
            },
            {
                "id": "old",
                "modifiedTime": old,
                "lastModifyingUser": {"displayName": "Old User"},
            },
        ]
    }

    revisions, error = instance.fetch_revisions("doc-rev", since_hours=24)

    assert error is None
    assert len(revisions) == 1
    assert revisions[0].id == "recent"


def test_fetch_metadata_returns_model(client, sample_doc_api_response):
    instance, _, docs = client
    docs.documents.return_value.get.return_value.execute.return_value = (
        sample_doc_api_response
    )

    metadata, error = instance.fetch_metadata("doc-meta")

    assert error is None
    assert metadata is not None
    assert metadata.title == "Team Project Proposal"


def test_fetch_metadata_returns_error_on_failure(client):
    instance, _, docs = client
    docs.documents.return_value.get.return_value.execute.side_effect = RuntimeError(
        "down"
    )

    metadata, error = instance.fetch_metadata("doc-meta")

    assert metadata is None
    assert error is not None
    assert "Failed to fetch metadata" in error


def test_fetch_all_collects_partial_failure_errors(
    client, sample_comment, sample_revision, sample_metadata, mocker
):
    instance, _, _ = client
    mocker.patch.object(
        instance, "fetch_comments", return_value=([sample_comment], None)
    )
    mocker.patch.object(
        instance,
        "fetch_revisions",
        return_value=([], "Failed to fetch revisions: timeout"),
    )
    mocker.patch.object(
        instance, "fetch_metadata", return_value=(sample_metadata, None)
    )

    comments, revisions, metadata, errors = instance.fetch_all("doc", since_hours=48)

    assert len(comments) == 1
    assert revisions == []
    assert metadata == sample_metadata
    assert errors == ["Failed to fetch revisions: timeout"]
