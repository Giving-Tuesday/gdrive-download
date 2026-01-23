# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains two linked Python packages:

1. **`gdrive-download`** - Core Google Drive document downloading and conversion tool
2. **`document-analyzer`** - Generic document analysis framework with template-based architecture

The system is designed with clear separation of concerns: `gdrive-download` focuses purely on downloading and converting documents from Google Drive to markdown, while `document-analyzer` provides extensible analysis capabilities for structured documents. AAR (After Action Review) analysis is provided as the primary template, but the framework supports any document type.

## Known Limitations

### Footnote Handling

**Download (DOCX → Markdown):** ✅ **Fully Supported**
- Word document footnotes are converted to Pandoc-style markdown footnotes
- Format: `[^1]` for references, `[^1]: content` for definitions
- Preserves footnote content and sequential numbering

**Upload (Markdown → Google Docs):** ⚠️ **Not Supported**
- Pandoc-style footnotes in markdown files are uploaded as plain text (e.g., `[^1]`)
- Google Docs API footnote creation requires a complex two-pass batchUpdate process
- Implementing this would require significant architectural changes with marginal benefit
- **Workaround:** Manually insert footnotes in Google Docs after upload using Insert → Footnote

**Why Not Supported:**
- Google Docs API `createFootnote` returns a `footnoteId` in the response
- Adding content requires a second batchUpdate with `insertText` using that `footnoteId` as `segmentId`
- This necessitates: (1) parsing batchUpdate responses, (2) mapping footnote IDs, (3) generating second request set
- HTML import path (currently used) does not preserve footnotes either

**Bottom Line:** Footnotes work great for download/conversion but remain as text markers when uploading to Google Docs. 

## Core Commands

**IMPORTANT: Always use the `.venv` environment and `uv` for all Python commands.**

### Development Commands
```bash
# Activate the virtual environment (if needed)
source .venv/bin/activate

# Install package in development mode using uv
uv pip install -e .
uv pip install -e ".[dev]"  # With dev dependencies

# Run tests
uv run pytest
uv run pytest --cov=src/gdrive_download --cov-report=html

# Code quality checks
uv run black src/ tests/           # Format code
uv run isort src/ tests/           # Sort imports  
uv run mypy src/                   # Type checking
uv run flake8 src/ tests/          # Linting
uv run pre-commit run --all-files  # Run all pre-commit hooks
```

### CLI Tools

#### gdrive-download Package
```bash
# Download and convert documents from Google Drive
gdrive-download -u "https://drive.google.com/drive/folders/FOLDER_ID" -c credentials.json

# Search for files by pattern across Google Drive
gdrive-search -p "AAR*"                    # Search all drives
gdrive-search -p "*2024*" -s personal      # Search personal drive only
gdrive-search -p "^AAR.*\.docx$"           # Regex pattern search

# Create shortcuts to search results in a Google Drive folder
gdrive-search -p "AAR*" --no-download --create-shortcuts FOLDER_ID
gdrive-search -p "Project Brief*" --create-shortcuts FOLDER_ID  # Search, download, and create shortcuts

# Search for recently modified files
gdrive-search -p "AAR*" --since 7d         # Files modified in last 7 days
gdrive-search -p "Report*" --since 2024-01-01  # Files modified since specific date
gdrive-search -p "Project*" --since 2w     # Last 2 weeks (also supports: 1h, 1m)

# Management utilities
gdrive-manage status
gdrive-manage init-config
```

#### document-analyzer Package (Future CLI)
```bash
# Analyze documents using templates
doc-analyze --template aar --input markdown_docs/ --output reports/

# List available templates
doc-analyze --list-templates

# Generate analysis reports
doc-report --template aar --format markdown --input analysis_results.json
```

## Architecture

### gdrive-download Package

**Core Components:**

1. **Downloader Module** (`src/gdrive_download/downloader/`)
   - `GoogleDriveDownloader`: Handles OAuth authentication and downloads files from Google Drive
   - `GoogleDriveSearcher`: Search for files by pattern across personal and shared drives
   - `FileConverter`: Converts Word documents to markdown using mammoth + markdownify
   - `FileRelationshipTracker`: Tracks relationships between Google Drive URLs, downloaded files, and converted markdown

2. **CLI Module** (`src/gdrive_download/cli/`)
   - Multiple CLI commands with Click framework
   - Rich console output for better user experience

3. **Configuration** (`src/gdrive_download/config.py`)
   - Pydantic models for type-safe configuration
   - YAML configuration file support

### document-analyzer Package

**Core Components:**

1. **Templates Module** (`src/document_analyzer/templates/`)
   - `DocumentTemplate`: Abstract base class for all analysis templates
   - `AarTemplate`: Concrete implementation for After Action Review documents
   - Template loading and discovery utilities

2. **Core Analysis Framework** (`src/document_analyzer/core/`)
   - `DocumentAnalyzer`: Main analysis orchestrator that coordinates the analysis process
   - `PatternMatcher`: Advanced pattern matching with regex, context extraction, and deduplication
   - Template-based analysis framework for extensible document analysis

3. **Template System Architecture:**
   - Templates define document structure, analysis patterns, and processing logic
   - Extensible design allows easy addition of new document types
   - AAR template provides patterns for challenges, successes, lessons, and recommendations

### Data Flow

#### gdrive-download Workflow
1. **Download**: Google Drive folder URL → downloaded .docx files in `downloads/`
2. **Convert**: .docx files → markdown files in `markdown/`
3. **Track**: Relationships stored in `file_relationships.csv`

#### document-analyzer Workflow
1. **Load Template**: Choose analysis template (e.g., AAR)
2. **Preprocess**: Normalize document structure and headers
3. **Extract Sections**: Identify document sections based on template
4. **Pattern Matching**: Apply regex patterns to find relevant content
5. **Theme Extraction**: Analyze pattern frequencies and extract key themes
6. **Report Generation**: Create comprehensive analysis reports

### Key Configuration

#### gdrive-download
- Google Drive authentication uses OAuth2 with `credentials.json` and `token.pickle`
- File conversion settings configurable via YAML

#### document-analyzer
- Templates define analysis patterns, section headers, and report structure
- AAR template patterns categorize challenges (resource constraints, communication, etc.) and successes (leadership, partnerships, etc.)
- Pattern matching uses case-insensitive regex with context extraction
- Report formats include Markdown, HTML, and JSON

### Testing

- Comprehensive test suite in `tests/` directory
- Uses pytest with coverage reporting
- **gdrive-download tests**: CLI, downloader, converter, and configuration components
- **document-analyzer tests**: Template system, core analysis framework, pattern matching, and report generation
- **Integration tests**: End-to-end document analysis workflows

## Important Files

### gdrive-download Package
- `pyproject.toml`: Package configuration, dependencies, and tool settings
- `credentials.json`: Google Drive API credentials (not in repo)
- `token.pickle`: OAuth token storage (not in repo)
- `file_relationships.csv`: Mapping between Google Drive URLs and local files

### document-analyzer Package
- Templates in `src/document_analyzer/templates/` define analysis behavior
- Core framework in `src/document_analyzer/core/` provides analysis engine
- Comprehensive test suite in `tests/document_analyzer/`

## Working with the Codebase

### Development Practices
- Both packages use modern Python practices with type hints and Pydantic models
- Configuration is centralized and type-safe
- All file paths use `pathlib.Path` objects
- Rich console library provides enhanced CLI output

### Package Architecture
- **gdrive-download**: Focused on Google Drive integration and document conversion
- **document-analyzer**: Generic framework with template-based extensibility
- Clear separation of concerns enables independent development and testing

### Extending the System
- **New document types**: Create new templates by extending `DocumentTemplate`
- **New analysis patterns**: Add regex patterns to existing templates
- **New export formats**: Extend pattern matcher with additional export formats
- **Integration**: Use both packages together or independently as needed

## File Relationship and Naming Conventions

- **File Relationship CSVs Guidelines**:
  * File relationship mapping CSVs should:
    1. Be consistently named
    2. Have consistently named fields
  * Verify that `drive_downloader.py` and `drive_searcher.py` use the same field names for identical pieces of information
  * Check that URL fields are particularly consistent across different modules
  * For API endpoints with distinct information:
    - Acceptable to include unique fields in the final CSV
    - Core fields (tracking Google file IDs, file names, markdown file paths, and URLs) must be present in all cases# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

