import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models.coordination_models import CoordinationSnapshot


def format_snapshot(snapshot: "CoordinationSnapshot") -> str:
    """Generate markdown report from snapshot."""
    lines = []

    # Header
    lines.append(f"# Coordination Snapshot: {snapshot.document_title}")
    lines.append(f"**Document ID**: `{snapshot.document_id}`")
    lines.append(
        f"**Generated**: {snapshot.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    lines.append(f"**Analysis Period**: Last {snapshot.since_hours} hours")
    lines.append("")

    # Data completeness
    lines.append("## 📊 Data Status")
    dc = snapshot.data_completeness
    lines.append(
        f"{'✅' if dc.comments_fetched else '❌'} Comments: {snapshot.raw_comment_count} unresolved"
    )
    lines.append(
        f"{'✅' if dc.activity_fetched else '❌'} Activity: {snapshot.raw_revision_count} revisions"
    )
    lines.append(f"{'✅' if dc.metadata_fetched else '❌'} Metadata: Retrieved")
    lines.append(
        f"{'✅' if dc.ai_analysis_completed else '❌'} AI Analysis: {'Completed' if dc.ai_analysis_completed else 'Failed'}"
    )
    if dc.errors:
        lines.append("\n**⚠️ Errors encountered:**")
        for error in dc.errors:
            lines.append(f"- {error}")
    lines.append("")

    # Contributors
    if snapshot.contributors:
        lines.append("## 👥 Contributors")
        for contributor in snapshot.contributors:
            lines.append(f"- {contributor}")
        lines.append("")

    # Questions
    lines.append(f"## 📌 Open Questions ({len(snapshot.questions)})")
    if snapshot.questions:
        for i, q in enumerate(snapshot.questions, 1):
            priority_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}[q.priority]
            lines.append(f"\n### {i}. {q.text} {priority_badge}")
            lines.append(f"**Asked by**: {q.author}")
            if q.context:
                lines.append(f'**Context**: "{q.context}"')
    else:
        lines.append("*No open questions found*")
    lines.append("")

    # Decisions
    lines.append(f"## ✅ Recent Decisions ({len(snapshot.decisions)})")
    if snapshot.decisions:
        for i, d in enumerate(snapshot.decisions, 1):
            lines.append(f"\n### {i}. {d.summary}")
            lines.append(f"**Decided by**: {d.decided_by}")
            if d.date:
                lines.append(f"**When**: {d.date.strftime('%Y-%m-%d')}")
            if d.context:
                lines.append(f"**Context**: {d.context}")
    else:
        lines.append("*No recent decisions found*")
    lines.append("")

    # Next steps
    lines.append(f"## 🔜 Suggested Next Steps ({len(snapshot.next_steps)})")
    if snapshot.next_steps:
        for i, step in enumerate(snapshot.next_steps, 1):
            priority_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}[step.priority]
            assignee = f" → **{step.assignee}**" if step.assignee else " → *Unassigned*"
            lines.append(f"\n### {i}. {step.description} {priority_badge}{assignee}")
            if step.rationale:
                lines.append(f"**Rationale**: {step.rationale}")
    else:
        lines.append("*No next steps generated*")

    return "\n".join(lines)


def save_snapshot(content: str, output_dir: str = "output") -> str:
    """Save snapshot to file with timestamp."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"snapshot_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        f.write(content)

    return filepath


def print_snapshot(content: str) -> None:
    """Print snapshot to terminal with separators."""
    print("\n" + "=" * 80)
    print(content)
    print("=" * 80 + "\n")
