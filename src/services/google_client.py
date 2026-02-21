import os
import time
import logging
from typing import Optional, Any
from datetime import datetime, timedelta, timezone

from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from ..models.google_models import Comment, Revision, DocumentMetadata
from ..config import Settings
from ..utils import get_google_credentials, build_drive_service, build_docs_service


class InMemoryCache:
    """Simple TTL-based cache."""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl_seconds
        self._logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            timestamp, value = self._cache[key]
            if time.time() - timestamp < self._ttl:
                self._logger.debug(f"Cache hit: {key}")
                return value
            else:
                del self._cache[key]
                self._logger.debug(f"Cache expired: {key}")
        return None

    def set(self, key: str, value: Any):
        """Set cached value with current timestamp."""
        self._cache[key] = (time.time(), value)
        self._logger.debug(f"Cache set: {key}")

    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._logger.info("Cache cleared")


def should_retry_http_error(exception):
    """Only retry transient HTTP errors."""
    if isinstance(exception, HttpError):
        status = exception.resp.status
        # Retry: 429 (rate limit) and 5xx (server errors)
        return status == 429 or (500 <= status < 600)
    return False


class GoogleDocsClient:
    """Google Docs/Drive API client with caching and retry."""

    def __init__(self, settings: Settings, force_refresh: bool = False):
        self._settings = settings
        self._force_refresh = force_refresh
        self._cache = InMemoryCache(settings.cache_ttl_seconds)
        self._logger = logging.getLogger(__name__)

        # Initialize API services
        creds = get_google_credentials(settings)
        self._drive = build_drive_service(creds)
        self._docs = build_docs_service(creds)

    @retry(
        retry=retry_if_exception(should_retry_http_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    def _fetch_comments_api(self, doc_id: str) -> list[dict]:
        """Fetch comments via Drive API with retry."""
        response = (
            self._drive.comments()
            .list(
                fileId=doc_id,
                fields="comments(id,content,author,createdTime,modifiedTime,resolved,quotedFileContent,replies)",
                includeDeleted=False,
            )
            .execute()
        )
        return response.get("comments", [])

    def fetch_comments(
        self, doc_id: str, include_resolved: bool = False
    ) -> tuple[list[Comment], Optional[str]]:
        """Fetch comments with caching."""
        cache_key = f"{doc_id}:comments"

        # Check cache
        if not self._force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached, None

        try:
            self._logger.info(f"Fetching comments for {doc_id}")
            raw_comments = self._fetch_comments_api(doc_id)

            # Filter by resolved status
            if not include_resolved:
                raw_comments = [c for c in raw_comments if not c.get("resolved", False)]

            # Parse into models
            comments = [Comment.from_api_response(c) for c in raw_comments]

            # Cache result
            self._cache.set(cache_key, comments)
            self._logger.info(f"Fetched {len(comments)} comments")

            return comments, None

        except Exception as e:
            error_msg = f"Failed to fetch comments: {str(e)}"
            self._logger.error(error_msg)
            return [], error_msg

    @retry(
        retry=retry_if_exception(should_retry_http_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    def _fetch_revisions_api(self, doc_id: str) -> list[dict]:
        """Fetch revisions via Drive API with retry."""
        response = (
            self._drive.revisions()
            .list(
                fileId=doc_id,
                fields="revisions(id,modifiedTime,lastModifyingUser)",
                pageSize=100,
            )
            .execute()
        )
        return response.get("revisions", [])

    def fetch_revisions(
        self, doc_id: str, since_hours: int = 48
    ) -> tuple[list[Revision], Optional[str]]:
        """Fetch recent revisions with caching."""
        cache_key = f"{doc_id}:revisions:{since_hours}"

        # Check cache
        if not self._force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached, None

        try:
            self._logger.info(f"Fetching revisions for {doc_id}")
            raw_revisions = self._fetch_revisions_api(doc_id)

            # Filter by time
            cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
            recent = []
            for r in raw_revisions:
                mod_time = datetime.fromisoformat(
                    r["modifiedTime"].replace("Z", "+00:00")
                )
                if mod_time > cutoff:
                    recent.append(r)

            # Parse into models
            revisions = [Revision.from_api_response(r) for r in recent]

            # Cache result
            self._cache.set(cache_key, revisions)
            self._logger.info(f"Fetched {len(revisions)} revisions")

            return revisions, None

        except Exception as e:
            error_msg = f"Failed to fetch revisions: {str(e)}"
            self._logger.error(error_msg)
            return [], error_msg

    @retry(
        retry=retry_if_exception(should_retry_http_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    def _fetch_metadata_api(self, doc_id: str) -> dict:
        """Fetch metadata via Docs API with retry."""
        return self._docs.documents().get(documentId=doc_id).execute()

    def fetch_metadata(
        self, doc_id: str
    ) -> tuple[Optional[DocumentMetadata], Optional[str]]:
        """Fetch document metadata with caching."""
        cache_key = f"{doc_id}:metadata"

        # Check cache
        if not self._force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached, None

        try:
            self._logger.info(f"Fetching metadata for {doc_id}")
            raw_doc = self._fetch_metadata_api(doc_id)

            # Parse into model
            metadata = DocumentMetadata.from_api_response(raw_doc)

            # Cache result
            self._cache.set(cache_key, metadata)
            self._logger.info(f"Fetched metadata: {metadata.title}")

            return metadata, None

        except Exception as e:
            error_msg = f"Failed to fetch metadata: {str(e)}"
            self._logger.error(error_msg)
            return None, error_msg

    def fetch_all(
        self, doc_id: str, since_hours: int = 48
    ) -> tuple[list[Comment], list[Revision], Optional[DocumentMetadata], list[str]]:
        """
        Fetch all data with partial failure handling.
        Returns (comments, revisions, metadata, errors).
        """
        errors = []

        # Fetch each independently
        comments, err = self.fetch_comments(doc_id)
        if err:
            errors.append(err)

        revisions, err = self.fetch_revisions(doc_id, since_hours)
        if err:
            errors.append(err)

        metadata, err = self.fetch_metadata(doc_id)
        if err:
            errors.append(err)

        return comments, revisions, metadata, errors
