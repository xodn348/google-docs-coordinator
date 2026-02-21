"""
FastAPI server for the Google Docs Coordinator.

Usage:
    python -m src --serve [--port PORT]
    uvicorn src.server:app --reload
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import Settings
from .utils import setup_logging, get_google_credentials
from .services.google_client import GoogleDocsClient
from .services.ai_analyzer import AIAnalyzer
from .services.coordinator import Coordinator
from .models.coordination_models import CoordinationSnapshot

logger = logging.getLogger(__name__)


class AnalyzeRequest(BaseModel):
    """POST /api/analyze request body."""

    doc_id: str = Field(description="Google Doc ID extracted from URL")
    since_hours: Optional[int] = Field(
        default=None, description="Hours to look back (default: from config)"
    )
    force_refresh: bool = Field(
        default=False, description="Bypass cache and fetch fresh data"
    )


class HealthResponse(BaseModel):
    status: str = "ok"


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Google Docs Coordinator API",
        description="Analyzes Google Docs collaboration and returns coordination snapshots.",
        version="1.0.0",
    )

    # CORS: allow_origins=["*"] because Chrome Extension origin is chrome-extension://<id>
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Extension origin is chrome-extension://<id>
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings = Settings()
    get_google_credentials(settings)
    google_client = GoogleDocsClient(settings)
    ai_analyzer = AIAnalyzer(settings)
    coordinator = Coordinator(settings, google_client, ai_analyzer)

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse()

    @app.post("/api/analyze", response_model=CoordinationSnapshot)
    async def analyze(req: AnalyzeRequest):
        """Run the full coordination pipeline for a Google Doc."""
        logger.info(
            f"Analyze request: doc_id={req.doc_id}, "
            f"since_hours={req.since_hours}, force_refresh={req.force_refresh}"
        )
        try:
            snapshot = coordinator.generate_snapshot(
                doc_id=req.doc_id,
                since_hours=req.since_hours,
                force_refresh=req.force_refresh,
            )
            return snapshot
        except Exception as e:
            logger.exception("Analysis failed")
            raise HTTPException(status_code=500, detail=str(e))

    return app


app = create_app()
