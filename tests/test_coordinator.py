from unittest.mock import Mock

import pytest

from src.models.coordination_models import Decision, NextStep, Question
from src.services.coordinator import Coordinator


@pytest.fixture
def coordinator_with_mocks(mock_settings):
    google_client = Mock()
    google_client._cache = Mock()
    ai_analyzer = Mock()
    return (
        Coordinator(mock_settings, google_client, ai_analyzer),
        google_client,
        ai_analyzer,
    )


def test_generate_snapshot_uses_default_since_hours(
    coordinator_with_mocks, sample_comment, sample_revision, sample_metadata
):
    coordinator, google_client, ai_analyzer = coordinator_with_mocks
    google_client.fetch_all.return_value = (
        [sample_comment],
        [sample_revision],
        sample_metadata,
        [],
    )
    ai_analyzer.analyze.return_value = ([], [], [], None)

    snapshot = coordinator.generate_snapshot("doc-1")

    google_client.fetch_all.assert_called_once_with("doc-1", 48)
    assert snapshot.since_hours == 48


def test_generate_snapshot_uses_provided_since_hours(
    coordinator_with_mocks, sample_comment, sample_revision, sample_metadata
):
    coordinator, google_client, ai_analyzer = coordinator_with_mocks
    google_client.fetch_all.return_value = (
        [sample_comment],
        [sample_revision],
        sample_metadata,
        [],
    )
    ai_analyzer.analyze.return_value = ([], [], [], None)

    snapshot = coordinator.generate_snapshot("doc-1", since_hours=72)

    google_client.fetch_all.assert_called_once_with("doc-1", 72)
    assert snapshot.since_hours == 72


def test_generate_snapshot_force_refresh_clears_cache(
    coordinator_with_mocks, sample_comment, sample_revision, sample_metadata
):
    coordinator, google_client, ai_analyzer = coordinator_with_mocks
    google_client.fetch_all.return_value = (
        [sample_comment],
        [sample_revision],
        sample_metadata,
        [],
    )
    ai_analyzer.analyze.return_value = ([], [], [], None)

    coordinator.generate_snapshot("doc-1", force_refresh=True)

    google_client._cache.clear.assert_called_once()


def test_generate_snapshot_extracts_sorted_unique_contributors(
    coordinator_with_mocks, sample_comment, sample_revision, sample_metadata
):
    coordinator, google_client, ai_analyzer = coordinator_with_mocks
    google_client.fetch_all.return_value = (
        [sample_comment],
        [sample_revision],
        sample_metadata,
        [],
    )
    ai_analyzer.analyze.return_value = ([], [], [], None)

    snapshot = coordinator.generate_snapshot("doc-1")

    assert snapshot.contributors == ["Alice", "Bob", "Carol"]


def test_generate_snapshot_handles_missing_metadata(
    coordinator_with_mocks, sample_comment, sample_revision
):
    coordinator, google_client, ai_analyzer = coordinator_with_mocks
    google_client.fetch_all.return_value = (
        [sample_comment],
        [sample_revision],
        None,
        [],
    )
    ai_analyzer.analyze.return_value = ([], [], [], None)

    snapshot = coordinator.generate_snapshot("doc-1")

    assert snapshot.document_title == "Unknown Document"
    assert snapshot.data_completeness.metadata_fetched is False


def test_generate_snapshot_merges_fetch_and_ai_errors(
    coordinator_with_mocks, sample_comment, sample_revision, sample_metadata
):
    coordinator, google_client, ai_analyzer = coordinator_with_mocks
    google_client.fetch_all.return_value = (
        [sample_comment],
        [sample_revision],
        sample_metadata,
        ["Failed to fetch comments"],
    )
    ai_analyzer.analyze.return_value = ([], [], [], "AI analysis failed: timeout")

    snapshot = coordinator.generate_snapshot("doc-1")

    assert snapshot.data_completeness.ai_analysis_completed is False
    assert snapshot.data_completeness.errors == [
        "Failed to fetch comments",
        "AI analysis failed: timeout",
    ]


def test_generate_snapshot_passes_data_to_ai_analyzer(
    coordinator_with_mocks, sample_comment, sample_revision, sample_metadata
):
    coordinator, google_client, ai_analyzer = coordinator_with_mocks
    google_client.fetch_all.return_value = (
        [sample_comment],
        [sample_revision],
        sample_metadata,
        [],
    )
    ai_analyzer.analyze.return_value = ([], [], [], None)

    coordinator.generate_snapshot("doc-1")

    ai_analyzer.analyze.assert_called_once_with(
        [sample_comment], [sample_revision], sample_metadata
    )


def test_generate_snapshot_includes_ai_output(
    coordinator_with_mocks, sample_comment, sample_revision, sample_metadata
):
    coordinator, google_client, ai_analyzer = coordinator_with_mocks
    google_client.fetch_all.return_value = (
        [sample_comment],
        [sample_revision],
        sample_metadata,
        [],
    )
    questions = [Question(text="Question?", author="Alice", priority="medium")]
    decisions = [Decision(summary="Ship Friday", decided_by="Team")]
    next_steps = [NextStep(description="Finalize doc")]
    ai_analyzer.analyze.return_value = (questions, decisions, next_steps, None)

    snapshot = coordinator.generate_snapshot("doc-1")

    assert snapshot.questions == questions
    assert snapshot.decisions == decisions
    assert snapshot.next_steps == next_steps


def test_generate_snapshot_tracks_raw_counts(
    coordinator_with_mocks, sample_comment, sample_revision, sample_metadata
):
    coordinator, google_client, ai_analyzer = coordinator_with_mocks
    google_client.fetch_all.return_value = (
        [sample_comment, sample_comment],
        [sample_revision],
        sample_metadata,
        [],
    )
    ai_analyzer.analyze.return_value = ([], [], [], None)

    snapshot = coordinator.generate_snapshot("doc-1")

    assert snapshot.raw_comment_count == 2
    assert snapshot.raw_revision_count == 1
