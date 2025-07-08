# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python package called `givingtuesday-aar-tools` that downloads After Action Review (AAR) documents from Google Drive, converts them to markdown, and analyzes them for patterns and insights. The system is modular with separate components for downloading, conversion, analysis, and reporting.

## Core Commands

### Development Commands
```bash
# Install package in development mode
pip install -e .
pip install -e ".[dev]"  # With dev dependencies

# Run tests
pytest
pytest --cov=src/givingtuesday_aar --cov-report=html

# Code quality checks
black src/ tests/           # Format code
isort src/ tests/           # Sort imports  
mypy src/                   # Type checking
flake8 src/ tests/          # Linting
pre-commit run --all-files  # Run all pre-commit hooks
```

### CLI Tools
The package provides 4 command-line tools:
```bash
# Download and convert documents from Google Drive
aar-download -u "https://drive.google.com/drive/folders/FOLDER_ID" -c credentials.json

# Analyze markdown documents and generate reports
aar-analyze -i markdown -o reports

# Extract specific data from documents
aar-extract-data

# Management utilities
aar-manage status
aar-manage init-config
```

## Architecture

### Core Components

1. **Downloader Module** (`src/givingtuesday_aar/downloader/`)
   - `GoogleDriveDownloader`: Handles OAuth authentication and downloads files from Google Drive
   - `FileConverter`: Converts Word documents to markdown using mammoth + markdownify
   - `FileRelationshipTracker`: Tracks relationships between Google Drive URLs, downloaded files, and converted markdown

2. **Analyzer Module** (`src/givingtuesday_aar/analyzer/`)
   - `AARAnalyzer`: Main analysis engine that identifies patterns in challenges and successes
   - `PatternMatcher`: Uses regex patterns to categorize content
   - `ReportGenerator`: Creates markdown reports with citations back to source documents

3. **CLI Module** (`src/givingtuesday_aar/cli/`)
   - Four separate CLI commands with Click framework
   - Rich console output for better user experience

4. **Configuration** (`src/givingtuesday_aar/config.py`)
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