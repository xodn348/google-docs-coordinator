#!/usr/bin/env python3
"""
Google Docs Collaboration Coordinator - CLI Entry Point

This module serves as the main entry point for the Google Docs Coordinator tool.
It orchestrates the full pipeline: fetching document data, analyzing collaboration,
and generating coordination snapshots.

Usage:
    python src/main.py <document_id> [--force-refresh] [--since-hours HOURS] [--output-dir DIR]
"""

import argparse
import sys

from config import Settings
from utils import (
    setup_logging,
    get_google_credentials,
    build_drive_service,
    build_docs_service,
)
from services.google_client import GoogleDocsClient
from services.ai_analyzer import AIAnalyzer
from services.coordinator import Coordinator
from formatter import save_snapshot, print_snapshot


def main():
    """
    Main entry point for the Google Docs Coordinator CLI.

    Parses command-line arguments, initializes services, generates a coordination
    snapshot from a Google Doc, and outputs results to console and file.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Google Docs Collaboration Coordinator - Generate coordination snapshots from Google Docs"
    )
    parser.add_argument("document_id", help="Google Doc ID (from the document URL)")
    parser.add_argument(
        "--force-refresh", action="store_true", help="Bypass cache and fetch fresh data"
    )
    parser.add_argument(
        "--since-hours",
        type=int,
        help="Hours to look back for activity (default: from config)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save snapshots (default: output)",
    )
    args = parser.parse_args()

    try:
        # Step 1: Setup logging for the application
        setup_logging()

        # Step 2: Load configuration settings
        settings = Settings()

        # Step 3: Authenticate with Google APIs
        creds = get_google_credentials()

        # Step 4: Build Google API service clients
        drive_service = build_drive_service(creds)
        docs_service = build_docs_service(creds)

        # Step 5: Initialize service clients
        google_client = GoogleDocsClient(
            drive_service, docs_service, cache_ttl_seconds=settings.cache_ttl_seconds
        )
        ai_analyzer = AIAnalyzer(settings.openai_api_key, model=settings.openai_model)
        coordinator = Coordinator(settings, google_client, ai_analyzer)

        # Step 6: Generate coordination snapshot from the document
        snapshot = coordinator.generate_snapshot(
            args.document_id,
            since_hours=args.since_hours,
            force_refresh=args.force_refresh,
        )

        # Step 7: Print snapshot to console
        print_snapshot(snapshot)

        # Step 8: Save snapshot to output directory
        save_snapshot(snapshot, output_dir=args.output_dir)

        # Step 9: Check for errors and exit with appropriate code
        if snapshot.data_completeness.errors:
            print(
                f"\n⚠️  {len(snapshot.data_completeness.errors)} warning(s) occurred - "
                "see above for details"
            )
            sys.exit(1)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
