from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models.google_models import Comment, Revision, DocumentMetadata


COORDINATION_SYSTEM_PROMPT = """You are a coordination assistant analyzing Google Docs collaboration data.

Your task is to extract actionable coordination information to help teams work together effectively.

Extract THREE types of information:

1. **OPEN QUESTIONS** - Unresolved questions from comments
   - Must be explicit questions (ending with "?" or clearly interrogative)
   - NOT rhetorical or already answered
   - Include who asked and any quoted context
   - Assign priority based on impact on project progress

2. **DECISIONS** - Clear agreements or resolutions from discussions
   - Look for phrases like "agreed", "decided", "let's go with", "resolved"
   - Only include if there's clear resolution, not ongoing debate
   - Note who made/agreed to the decision

3. **NEXT STEPS** - Actionable tasks the team should do next
   - ALWAYS generate at least 1-2 next steps based on available data
   - Suggest steps to resolve any open questions
   - Suggest follow-ups if activity is low or one-sided
   - If comments mention tasks, deadlines, or responsibilities, extract them
   - Assign to specific people when mentioned
   - Prioritize by urgency and blocking nature
   - Provide brief rationale for each step

RULES:
- For QUESTIONS and DECISIONS: only extract items explicitly visible in the data
- For NEXT STEPS: infer reasonable action items from the context (open questions, activity patterns, stalled discussions)
- Be concise and actionable
- When uncertain about priority, default to "medium"
"""


def build_user_prompt(
    comments: list["Comment"], revisions: list["Revision"], metadata: "DocumentMetadata"
) -> str:
    """Build user prompt with document context."""
    parts = []

    # Document header
    parts.append(f"## Document: {metadata.title}")
    parts.append(f"Document ID: {metadata.document_id}\n")

    # Comments section
    if comments:
        parts.append("## UNRESOLVED COMMENTS\n")
        for i, comment in enumerate(comments, 1):
            parts.append(f"### Comment {i}")
            parts.append(f"**Author**: {comment.author.display_name}")
            parts.append(
                f"**Posted**: {comment.created_time.strftime('%Y-%m-%d %H:%M')}"
            )
            if comment.quoted_content:
                parts.append(f'**Quoted text**: "{comment.quoted_content}"')
            parts.append(f"**Content**: {comment.content}")
            if comment.replies:
                parts.append(f"**Replies** ({len(comment.replies)}):")
                for reply in comment.replies:
                    parts.append(f"  - {reply.author.display_name}: {reply.content}")
            parts.append("")
    else:
        parts.append("## COMMENTS: None found\n")

    # Activity section
    if revisions:
        parts.append(f"## RECENT ACTIVITY ({len(revisions)} revisions)\n")
        # Group by user
        user_edits = {}
        for rev in revisions:
            if rev.last_modifying_user:
                name = rev.last_modifying_user.display_name
                if name not in user_edits:
                    user_edits[name] = {"count": 0, "last_edit": rev.modified_time}
                user_edits[name]["count"] += 1
                if rev.modified_time > user_edits[name]["last_edit"]:
                    user_edits[name]["last_edit"] = rev.modified_time

        for user, data in sorted(
            user_edits.items(), key=lambda x: x[1]["count"], reverse=True
        ):
            parts.append(
                f"- **{user}**: {data['count']} edits, last at {data['last_edit'].strftime('%Y-%m-%d %H:%M')}"
            )
        parts.append("")
    else:
        parts.append("## ACTIVITY: No recent revisions\n")

    parts.append(
        "---\nBased on the above, extract questions, decisions, and next steps."
    )

    return "\n".join(parts)
