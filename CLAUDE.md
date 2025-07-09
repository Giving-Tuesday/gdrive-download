# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python package called `gdrive-download` that downloads and converts documents from Google Drive to markdown format. The core function is Google Drive document downloading and conversion, with additional analysis capabilities for After Action Review (AAR) documents. The system is modular with separate components for downloading, conversion, analysis, and reporting.

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
The package provides 5 command-line tools:
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

# Analyze markdown documents and generate reports
gdrive-analyze -i markdown -o reports

# Extract specific data from documents
gdrive-extract-data

# Management utilities
gdrive-manage status
gdrive-manage init-config
```

## Architecture

### Core Components

1. **Downloader Module** (`src/gdrive_download/downloader/`)
   - `GoogleDriveDownloader`: Handles OAuth authentication and downloads files from Google Drive
   - `GoogleDriveSearcher`: Search for files by pattern across personal and shared drives
   - `FileConverter`: Converts Word documents to markdown using mammoth + markdownify
   - `FileRelationshipTracker`: Tracks relationships between Google Drive URLs, downloaded files, and converted markdown

2. **Analyzer Module** (`src/gdrive_download/analyzer/`)
   - `AARAnalyzer`: Main analysis engine that identifies patterns in challenges and successes
   - `PatternMatcher`: Uses regex patterns to categorize content
   - `ReportGenerator`: Creates markdown reports with citations back to source documents

3. **CLI Module** (`src/gdrive_download/cli/`)
   - Four separate CLI commands with Click framework
   - Rich console output for better user experience

4. **Configuration** (`src/gdrive_download/config.py`)
   - Pydantic models for type-safe configuration
   - YAML configuration file support (`aar_config.yaml`)
   - Configurable regex patterns for analysis

### Data Flow

1. **Download**: Google Drive folder URL → downloaded .docx files in `downloads/`
2. **Convert**: .docx files → markdown files in `markdown/`
3. **Track**: Relationships stored in `file_relationships.csv`
4. **Analyze**: Markdown files → pattern analysis using configurable regex
5. **Report**: Analysis results → markdown reports in `reports/`

### Key Configuration

- Analysis patterns are fully configurable in `aar_config.yaml`
- Default patterns categorize challenges (resource constraints, data collection, communication, etc.) and successes (leadership, content, agility, etc.)
- Google Drive authentication uses OAuth2 with `credentials.json` and `token.pickle`

### Testing

- Test suite in `tests/` directory
- Uses pytest with coverage reporting
- Tests cover all major components including CLI, downloader, analyzer, and configuration

## Important Files

- `pyproject.toml`: Package configuration, dependencies, and tool settings
- `aar_config.yaml`: Runtime configuration for analysis patterns and directories
- `credentials.json`: Google Drive API credentials (not in repo)
- `token.pickle`: OAuth token storage (not in repo)
- `file_relationships.csv`: Mapping between Google Drive URLs and local files

## Working with the Codebase

- The package uses modern Python practices with type hints and Pydantic models
- Configuration is centralized and type-safe
- All file paths use `pathlib.Path` objects
- Rich console library provides enhanced CLI output
- Pattern matching uses regex for flexibility while maintaining readability through configuration