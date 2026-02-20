import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from .config import Settings


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def get_google_credentials(settings: Settings) -> Credentials:
    """
    Get Google OAuth2 credentials with token refresh.
    Enforces 0600 permissions on token file for security.
    """
    creds = None
    token_path = settings.google_token_path

    # Load existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(
            token_path, settings.google_scopes
        )

    # Refresh or initiate OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(settings.google_credentials_path):
                raise FileNotFoundError(
                    f"Google credentials not found at {settings.google_credentials_path}\n"
                    "Download from Google Cloud Console: "
                    "https://console.cloud.google.com/apis/credentials"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                settings.google_credentials_path, settings.google_scopes
            )
            creds = flow.run_local_server(port=0)

        # Save credentials with strict permissions
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        os.chmod(token_path, 0o600)  # Owner read/write only

    return creds


def build_drive_service(creds: Credentials):
    """Build Google Drive API service."""
    return build("drive", "v3", credentials=creds)


def build_docs_service(creds: Credentials):
    """Build Google Docs API service."""
    return build("docs", "v1", credentials=creds)
