# Google Docs Collaboration Coordinator

AI-powered tool that analyzes Google Docs collaboration and surfaces **open questions**, **decisions**, and **next steps** for your team.

Available as both a **CLI tool** and a **Chrome Extension** with a local API server.

**Course**: CSCE672 (CSCW) - Spring 2026, Texas A&M University
**Team**: Social Sense (Junhyuk Lee, Jobin Varughese, Kyle Moore)

## Features

- **Open Questions** - Extracts unresolved questions from comments (priority-ranked)
- **Decisions** - Identifies agreements and resolutions from discussions
- **Next Steps** - Suggests actionable tasks based on activity and open threads
- **Chrome Extension** - Popup sidebar on any Google Docs page, one-click analysis
- **CLI Mode** - Terminal output + Markdown file export
- **Smart Caching** - 5-minute TTL so repeated queries are fast
- **Partial Failure Handling** - Continues with available data if some API calls fail

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| AI | OpenAI GPT-4o-mini (structured output) |
| Backend | FastAPI + Uvicorn |
| Google API | google-api-python-client, OAuth 2.0 |
| Data Validation | Pydantic v2 |
| Frontend | Chrome Extension (Manifest V3), vanilla JS |
| Testing | pytest (55 tests) |

## Prerequisites

- Python 3.12+
- [Google Cloud Project](https://console.cloud.google.com) with **Docs API** + **Drive API** enabled, OAuth 2.0 credentials (Desktop app)
- [OpenAI API key](https://platform.openai.com/api-keys)

## Setup

```bash
git clone https://github.com/xodn348/google-docs-coordinator.git
cd google-docs-coordinator
pip install -r requirements.txt
```

Create `.env`:
```
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Place Google OAuth credentials at `credentials/credentials.json`.
On first run, a browser window opens for Google auth. After that, `credentials/token.json` is cached.

## Quick Start

### Option A: Chrome Extension (Recommended)

**1. Start the local server:**
```bash
python -m src --serve
```
Server runs at `http://localhost:8000`. Keep this terminal open.

**2. Install the extension:**
- Open `chrome://extensions`
- Enable **Developer mode** (top right)
- Click **Load unpacked** → select the `extension/` folder

**3. Use it:**
- Open any Google Doc
- Click the extension icon in Chrome toolbar
- Set look-back hours (default: 48)
- Click **Analyze**

### Option B: CLI

```bash
# Basic
python -m src <DOC_ID>

# Custom look-back period + bypass cache
python -m src <DOC_ID> --since-hours 720 --force-refresh

# Custom output directory
python -m src <DOC_ID> --output-dir snapshots
```

**Finding the Document ID:**
```
https://docs.google.com/document/d/1ABC123XYZ456/edit
                                   ^^^^^^^^^^^^
                                   This part
```

### CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `document_id` | Google Doc ID from URL | required |
| `--serve` | Start API server mode | - |
| `--port` | Server port | `8000` |
| `--since-hours` | Hours to look back | `48` |
| `--force-refresh` | Bypass cache | `false` |
| `--output-dir` | Snapshot save directory | `output` |

## API

When running with `--serve`, one endpoint is available:

```
POST /api/analyze
Content-Type: application/json

{
  "doc_id": "1ABC123XYZ456",
  "since_hours": 48,
  "force_refresh": false
}
```

Returns a `CoordinationSnapshot` JSON with `questions`, `decisions`, `next_steps`, `contributors`, and `data_completeness`.

Health check: `GET /health`

## Architecture

```
src/
  main.py           CLI entry point (argparse + --serve flag)
  server.py         FastAPI server (POST /api/analyze)
  config.py         Pydantic Settings (.env)
  prompts.py        AI system/user prompt templates
  formatter.py      Markdown output generation
  utils.py          OAuth2, logging, Google API service builders
  models/
    google_models.py        Google API schemas (User, Comment, Revision, DocumentMetadata)
    coordination_models.py  Output schemas (Question, Decision, NextStep, CoordinationSnapshot)
  services/
    google_client.py  Google Docs/Drive API client with caching + retry
    ai_analyzer.py    OpenAI structured output (GPT-4o-mini)
    coordinator.py    Pipeline orchestration (fetch → analyze → snapshot)

extension/
  manifest.json   Chrome Extension Manifest V3
  popup.html/js   Popup UI
  content.js      Doc ID extraction from Google Docs URL
  styles.css      Popup styling

tests/            55 unit tests
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `credentials.json not found` | Download OAuth credentials from Google Cloud Console → `credentials/credentials.json` |
| `Token has been expired or revoked` | Delete `credentials/token.json`, re-run to re-authenticate |
| `API has not been used in project` | Enable Google Docs API + Drive API in Cloud Console |
| `OpenAI API error` | Check `OPENAI_API_KEY` in `.env` |
| Extension shows "Cannot reach local server" | Make sure `python -m src --serve` is running |

## License

MIT - Copyright (c) 2026 Social Sense Team (Junhyuk Lee, Jobin Varughese, Kyle Moore)

## Acknowledgments

- Developed for CSCE672 (CSCW) at Texas A&M University
- Original work for academic purposes
