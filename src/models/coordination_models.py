"""Pydantic models for coordination analysis output."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class Question(BaseModel):
    """Extracted open question."""

    text: str = Field(description="The question text")
    author: str = Field(description="Who asked the question")
    context: Optional[str] = Field(
        default=None, description="Surrounding context from document"
    )
    priority: Literal["high", "medium", "low"] = Field(
        default="medium", description="Question priority"
    )
    comment_id: Optional[str] = Field(
        default=None, description="Source comment ID if available"
    )


class Decision(BaseModel):
    """Identified decision from discussion."""

    summary: str = Field(description="What was decided")
    decided_by: str = Field(description="Who made or agreed to the decision")
    date: Optional[datetime] = Field(default=None, description="When decision was made")
    context: Optional[str] = Field(default=None, description="Supporting context")


class NextStep(BaseModel):
    """Suggested action item."""

    description: str = Field(description="What needs to be done")
    assignee: Optional[str] = Field(default=None, description="Who should do it")
    priority: Literal["high", "medium", "low"] = Field(
        default="medium", description="Task priority"
    )
    rationale: Optional[str] = Field(default=None, description="Why this is important")
    source: Optional[str] = Field(
        default=None, description="What triggered this suggestion"
    )


class DataCompleteness(BaseModel):
    """Tracks what data was successfully fetched."""

    comments_fetched: bool = False
    activity_fetched: bool = False
    metadata_fetched: bool = False
    ai_analysis_completed: bool = False
    errors: list[str] = Field(default_factory=list)


class CoordinationSnapshot(BaseModel):
    """Complete coordination analysis output."""

    # Document info
    document_title: str
    document_id: str
    generated_at: datetime
    since_hours: int

    # Contributors
    contributors: list[str] = Field(default_factory=list)

    # Analysis results
    questions: list[Question] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)

    # Metadata
    data_completeness: DataCompleteness
    raw_comment_count: int = 0
    raw_revision_count: int = 0
