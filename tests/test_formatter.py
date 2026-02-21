from src.formatter import format_snapshot, print_snapshot, save_snapshot
from src.models.coordination_models import DataCompleteness


def test_format_snapshot_includes_main_sections(sample_snapshot):
    output = format_snapshot(sample_snapshot)

    assert "# Coordination Snapshot: Test Document" in output
    assert "## 📊 Data Status" in output
    assert "## 👥 Contributors" in output
    assert "## 📌 Open Questions (1)" in output
    assert "## ✅ Recent Decisions (1)" in output
    assert "## 🔜 Suggested Next Steps (1)" in output


def test_format_snapshot_shows_priority_badges(sample_snapshot):
    output = format_snapshot(sample_snapshot)

    assert "🔴" in output
    assert "### 1. Finalize budget by Friday 🔴 → **Carol**" in output


def test_format_snapshot_handles_empty_analysis_lists(sample_snapshot):
    empty_snapshot = sample_snapshot.model_copy(
        update={"questions": [], "decisions": [], "next_steps": []}
    )

    output = format_snapshot(empty_snapshot)

    assert "*No open questions found*" in output
    assert "*No recent decisions found*" in output
    assert "*No next steps generated*" in output


def test_format_snapshot_includes_errors_when_present(sample_snapshot):
    with_errors = sample_snapshot.model_copy(
        update={
            "data_completeness": DataCompleteness(
                comments_fetched=True,
                activity_fetched=False,
                metadata_fetched=True,
                ai_analysis_completed=False,
                errors=["Failed to fetch revisions"],
            )
        }
    )

    output = format_snapshot(with_errors)

    assert "⚠️ Errors encountered" in output
    assert "- Failed to fetch revisions" in output


def test_save_snapshot_writes_markdown_file(tmp_path):
    content = "# hello"

    filepath = save_snapshot(content, output_dir=str(tmp_path))

    saved_path = tmp_path / filepath.split("/")[-1]
    assert saved_path.exists()
    assert saved_path.read_text() == "# hello"


def test_print_snapshot_writes_to_stdout(capsys):
    print_snapshot("snapshot-body")

    captured = capsys.readouterr().out
    assert "snapshot-body" in captured
    assert "=" * 80 in captured
