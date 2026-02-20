"""OpenAI-powered coordination analysis with structured output."""

import logging
from typing import Optional
from pydantic import BaseModel, Field

from openai import OpenAI

from ..models.google_models import Comment, Revision, DocumentMetadata
from ..models.coordination_models import Question, Decision, NextStep
from ..config import Settings
from ..prompts import COORDINATION_SYSTEM_PROMPT, build_user_prompt


class CoordinationAnalysis(BaseModel):
    """Structured output from AI analysis."""

    questions: list[Question] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)


class AIAnalyzer:
    """OpenAI-powered coordination analysis."""

    def __init__(self, settings: Settings):
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._logger = logging.getLogger(__name__)

    def analyze(
        self,
        comments: list[Comment],
        revisions: list[Revision],
        metadata: Optional[DocumentMetadata],
    ) -> tuple[list[Question], list[Decision], list[NextStep], Optional[str]]:
        """
        Analyze all data in single OpenAI call.

        Returns:
            (questions, decisions, next_steps, error_message)
        """
        # Handle empty metadata gracefully
        if metadata is None:
            metadata = DocumentMetadata(
                document_id="unknown", title="Unknown Document", revision_id=None
            )

        try:
            self._logger.info(f"Analyzing document: {metadata.title}")

            # Build context prompt
            user_prompt = build_user_prompt(comments, revisions, metadata)

            # Call OpenAI with structured output
            response = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": COORDINATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=CoordinationAnalysis,
                temperature=0,  # Deterministic for analysis
            )

            # Extract parsed data
            analysis = response.choices[0].message.parsed

            if analysis is None:
                raise ValueError("OpenAI returned null parsed response")

            self._logger.info(
                f"Analysis complete: {len(analysis.questions)} questions, "
                f"{len(analysis.decisions)} decisions, {len(analysis.next_steps)} next steps"
            )

            return (analysis.questions, analysis.decisions, analysis.next_steps, None)

        except Exception as e:
            error_msg = f"AI analysis failed: {str(e)}"
            self._logger.error(error_msg)

            # Return empty results on failure
            return [], [], [], error_msg
