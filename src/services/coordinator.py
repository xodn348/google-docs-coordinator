"""Orchestrates the entire coordination analysis pipeline."""

import logging
from typing import Optional
from datetime import datetime, timezone

from ..models.coordination_models import CoordinationSnapshot, DataCompleteness
from ..config import Settings
from .google_client import GoogleDocsClient
from .ai_analyzer import AIAnalyzer


class Coordinator:
    """Orchestrates GoogleDocsClient + AIAnalyzer to produce CoordinationSnapshot."""

    def __init__(
        self,
        settings: Settings,
        google_client: GoogleDocsClient,
        ai_analyzer: AIAnalyzer,
    ):
        """Initialize coordinator with dependencies.

        Args:
            settings: Application configuration
            google_client: Google Docs API client
            ai_analyzer: AI-powered analysis engine
        """
        self.settings = settings
        self.google_client = google_client
        self.ai_analyzer = ai_analyzer
        self.logger = logging.getLogger(__name__)

    def generate_snapshot(
        self,
        doc_id: str,
        since_hours: Optional[int] = None,
        force_refresh: bool = False,
    ) -> CoordinationSnapshot:
        """Generate coordination snapshot for a Google Doc.

        Orchestrates data fetching and AI analysis to produce a complete
        coordination snapshot with questions, decisions, and next steps.

        Args:
            doc_id: Google Doc ID
            since_hours: Hours to look back for activity (default: from settings)
            force_refresh: Bypass cache if True

        Returns:
            CoordinationSnapshot with questions, decisions, next steps
        """
        # Resolve since_hours
        since_hours = since_hours or self.settings.default_since_hours
        self.logger.info(
            f"Generating snapshot for doc_id={doc_id}, since_hours={since_hours}"
        )

        # Clear cache if force_refresh
        if force_refresh:
            self.logger.info("Force refresh enabled, clearing cache")
            self.google_client._cache.clear()

        # Fetch all data from Google Docs
        self.logger.info("Fetching data from Google Docs API")
        comments, revisions, metadata, errors = self.google_client.fetch_all(
            doc_id, since_hours
        )
        self.logger.info(
            f"Fetched: {len(comments)} comments, {len(revisions)} revisions, "
            f"metadata={'present' if metadata else 'missing'}"
        )

        # Extract unique contributors
        self.logger.info("Extracting contributors")
        contributors = set()

        # From comments
        for comment in comments:
            contributors.add(comment.author.display_name)
            for reply in comment.replies:
                contributors.add(reply.author.display_name)

        # From revisions
        for revision in revisions:
            if revision.last_modifying_user:
                contributors.add(revision.last_modifying_user.display_name)

        self.logger.info(f"Found {len(contributors)} unique contributors")

        # Analyze with AI
        self.logger.info("Running AI analysis")
        questions, decisions, next_steps, ai_error = self.ai_analyzer.analyze(
            comments, revisions, metadata
        )
        self.logger.info(
            f"AI analysis complete: {len(questions)} questions, "
            f"{len(decisions)} decisions, {len(next_steps)} next steps"
        )

        # Build data completeness
        all_errors = errors + ([ai_error] if ai_error else [])
        data_completeness = DataCompleteness(
            comments_fetched=len(comments) > 0,
            activity_fetched=len(revisions) > 0,
            metadata_fetched=metadata is not None,
            ai_analysis_completed=ai_error is None,
            errors=all_errors,
        )

        # Build and return snapshot
        snapshot = CoordinationSnapshot(
            document_id=doc_id,
            document_title=metadata.title if metadata else "Unknown Document",
            generated_at=datetime.now(timezone.utc),
            since_hours=since_hours,
            contributors=sorted(contributors),
            questions=questions,
            decisions=decisions,
            next_steps=next_steps,
            data_completeness=data_completeness,
            raw_comment_count=len(comments),
            raw_revision_count=len(revisions),
        )

        self.logger.info(
            f"Snapshot generated successfully for '{snapshot.document_title}' "
            f"with {len(contributors)} contributors"
        )

        return snapshot
