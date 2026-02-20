# Google Docs Collaboration Coordinator

AI-powered CLI tool that analyzes Google Docs collaboration data to generate coordination snapshots.

**Course Project**: CSCE672 (Computer Supported Collaborative Work) - Spring 2026, Texas A&M University  
**Team**: Social Sense (Junhyuk Lee, Jobin Varughese, Kyle Moore)

## Overview

This tool analyzes Google Docs collaboration patterns by examining:
- **Comments**: Threaded discussions, unresolved questions, resolved decisions
- **Activity**: Document revisions and editing patterns over time
- **Metadata**: Document details and contributor information

**Output**: Markdown snapshots with AI-extracted insights:
- 🔴 Open questions requiring team attention
- ✅ Decisions made during collaboration
- ➡️ Suggested next steps for the team

**Why it's useful**: Helps distributed teams track what's been decided, what's still open, and what needs to happen next—especially valuable for asynchronous collaboration on shared documents.

## Features

- 📊 Fetches comments, revisions, and metadata from Google Docs API
- 🤖 AI-powered analysis using OpenAI GPT-4
- ⚡ Smart caching with 5-minute TTL for faster repeated queries
- 🛡️ Partial failure handling—continues with available data if some API calls fail
- 📝 Markdown output with priority badges (🔴 high, 🟡 medium, 🟢 low)
- 🔒 Secure OAuth 2.0 authentication with local token storage

## Prerequisites

- **Python 3.12+**
- **Google Cloud Project** with:
  - Google Docs API enabled
  - Google Drive API enabled
  - OAuth 2.0 credentials (Desktop app)
- **OpenAI API key** with access to GPT-4 models

## Google Cloud Setup

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one

2. **Enable Required APIs**:
   - Navigate to "APIs & Services" > "Library"
   - Search for and enable:
     - **Google Docs API**
     - **Google Drive API**

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Download the credentials JSON file

4. **Save Credentials**:
   ```bash
   mkdir -p credentials
   mv ~/Downloads/client_secret_*.json credentials/credentials.json
   ```

## Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/google-docs-coordinator.git
cd google-docs-coordinator

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### Basic Usage

```bash
python src/main.py <GOOGLE_DOC_ID>
```

### With Options

```bash
# Force refresh (bypass cache)
python src/main.py <DOC_ID> --force-refresh

# Analyze last 72 hours of activity
python src/main.py <DOC_ID> --since-hours 72

# Save to custom directory
python src/main.py <DOC_ID> --output-dir snapshots
```

### Command-Line Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `document_id` | Yes | Google Doc ID (from document URL) | - |
| `--force-refresh` | No | Bypass cache and fetch fresh data | `False` |
| `--since-hours` | No | Hours to look back for activity | `48` |
| `--output-dir` | No | Directory to save snapshot files | `output` |

### Finding the Document ID

Google Doc URLs have this format:
```
https://docs.google.com/document/d/1ABC123XYZ456/edit
                                   ^^^^^^^^^^^^
                                   Document ID
```

Copy the part between `/d/` and `/edit`.

## Output Format

The tool generates Markdown files with the following structure:

```markdown
# Coordination Snapshot: [Document Title]

**Document ID**: 1ABC123XYZ  
**Generated**: 2026-02-20 15:30:00 UTC

## Contributors (3)
- Alice Smith
- Bob Johnson
- Carol Lee

## Open Questions (2)

### 🔴 HIGH: Budget allocation unclear
[AI-extracted question with context from comments]

### 🟡 MEDIUM: Timeline needs clarification
[Question details...]

## Decisions Made (1)

### We will use React for the frontend
[AI-extracted decision with reasoning]

## Next Steps (3)

### 🔴 HIGH: Finalize budget by Friday
[AI-suggested action item]

## Data Completeness
✅ Comments: Available  
✅ Revisions: Available  
✅ Metadata: Available  
⚠️ Errors: 0 warnings
```

Snapshot files are saved as: `output/snapshot_YYYYMMDD_HHMMSS.md`

## Architecture

**Models**:
- `google_models.py` - Google API response schemas (User, Comment, Revision, DocumentMetadata)
- `coordination_models.py` - Output schemas (Question, Decision, NextStep, CoordinationSnapshot)

**Services**:
- `GoogleDocsClient` - Google API wrapper with caching and retry logic
- `AIAnalyzer` - OpenAI integration with structured output parsing
- `Coordinator` - Pipeline orchestration

**Utilities**:
- `utils.py` - OAuth authentication and logging setup
- `prompts.py` - AI prompt templates
- `formatter.py` - Markdown output generation
- `config.py` - Environment configuration (Pydantic Settings)

**Entry Point**:
- `main.py` - CLI interface with argparse

## Troubleshooting

### "credentials.json not found"
**Solution**: Download OAuth credentials from Google Cloud Console and save to `credentials/credentials.json`

### "Invalid credentials" or "Token has been expired or revoked"
**Solution**: Delete `credentials/token.json` and re-run the tool. You'll be prompted to re-authenticate.

### "API has not been used in project before or it is disabled"
**Solution**: Enable Google Docs API and Google Drive API in Google Cloud Console

### "OpenAI API error" or "Invalid API key"
**Solution**: Check that `OPENAI_API_KEY` is correctly set in your `.env` file

### Permission errors when saving snapshots
**Solution**: Ensure the `output` directory exists and you have write permissions

## Security Notes

- **Credentials**: Never commit `credentials/credentials.json` or `credentials/token.json` to version control
- **API Keys**: Keep `.env` file secure and never commit it to git
- **Token Storage**: OAuth tokens are stored locally with `0600` permissions (owner read/write only)
- `.gitignore` is configured to exclude all sensitive files

## License

MIT License - See [LICENSE](LICENSE) file

Copyright (c) 2026 Social Sense Team (Junhyuk Lee, Jobin Varughese, Kyle Moore)

## Acknowledgments

- This project was built with assistance from AI tools (Claude Code by Anthropic)
- Developed as coursework for CSCE672 (Computer Supported Collaborative Work) at Texas A&M University
- This is original work created for academic purposes—NOT copied from existing open source projects
- External dependencies are properly attributed in `requirements.txt`

## Contributing

This is an academic project. For team members:
1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Test your changes locally
4. Submit a pull request for review

## Development

```bash
# Run with verbose logging
python src/main.py <DOC_ID> --force-refresh

# Check for missing dependencies
pip install -r requirements.txt

# Verify credentials setup
ls -la credentials/
```

For questions or issues, contact the team members listed above.
