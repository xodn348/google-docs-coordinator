#!/usr/bin/env python3

import argparse
import sys

from .config import Settings
from .utils import (
    setup_logging,
    get_google_credentials,
)
from .services.google_client import GoogleDocsClient
from .services.ai_analyzer import AIAnalyzer
from .services.coordinator import Coordinator
from .formatter import format_snapshot, save_snapshot, print_snapshot


def main():
    parser = argparse.ArgumentParser(
        description="Google Docs Collaboration Coordinator"
    )
    parser.add_argument("document_id", nargs="?", help="Google Doc ID (from the document URL)")
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
    parser.add_argument(
        "--serve", action="store_true", help="Start the FastAPI server instead of CLI mode"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000, used with --serve)"
    )
    args = parser.parse_args()

    if args.serve:
        import uvicorn
        from .server import app
        print(f"Starting Docs Coordinator API on http://localhost:{args.port}")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
        return

    if not args.document_id:
        parser.error("document_id is required when not using --serve")

    try:
        setup_logging()
        settings = Settings()
        get_google_credentials(settings)
        google_client = GoogleDocsClient(settings, force_refresh=args.force_refresh)
        ai_analyzer = AIAnalyzer(settings)
        coordinator = Coordinator(settings, google_client, ai_analyzer)

        snapshot = coordinator.generate_snapshot(
            args.document_id,
            since_hours=args.since_hours,
            force_refresh=args.force_refresh,
        )

        formatted = format_snapshot(snapshot)
        print_snapshot(formatted)
        save_snapshot(formatted, output_dir=args.output_dir)

        if snapshot.data_completeness.errors:
            print(
                f"\n\u26a0\ufe0f  {len(snapshot.data_completeness.errors)} warning(s) occurred - "
                "see above for details"
            )
            sys.exit(1)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\u274c Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
