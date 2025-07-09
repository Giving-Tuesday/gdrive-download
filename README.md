# Google Drive Downloading and Analysis Package

This project contains two Python packages, one for bulk downloading & conversion of google docs, and a second with preliminary analysis tools for the same.  

## Google Drive Download Tools

A focused Python package for downloading and converting documents from Google Drive to markdown format. This package handles Google Drive integration, document downloading, and conversion to markdown. For document analysis capabilities, see the companion `document-analyzer` package.

### Features

- **Google Drive Integration**: Download documents from shared Google Drive folders with full authentication support
- **Document Conversion**: Convert Word documents (.docx) to markdown using high-quality mammoth + markdownify pipeline
- **Search Capabilities**: Search for files by pattern across personal and shared drives
- **Relationship Tracking**: Maintain links between original Google Drive URLs, downloaded files, and converted markdown
- **CLI Interface**: Three command-line tools for streamlined workflows
- **Standardized Structure**: Creates consistent project directory structure for easy organization
- **Incremental Updates**: Smart downloading to avoid re-processing existing files

### Installation

#### Prerequisites

- Python 3.8 or higher
- Google Drive API credentials (see [Setup Guide](#google-drive-setup))

#### Install from Source

```bash
## Clone and navigate to the refactor directory
cd refactor/

## Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# For development with testing tools
pip install -e ".[dev]"
```

### Quick Start

#### 1. Google Drive Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials file as `credentials.json`

#### 2. Basic Usage

```bash
# Download and convert documents from a folder
gdrive-download --folder-url "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" \
             --credentials credentials.json

# Search for documents by pattern
gdrive-search --pattern "AAR*" --credentials credentials.json

# Check status
gdrive-manage status
```

#### 3. Python API

```python
from gdrive_download import GoogleDriveDownloader, GoogleDriveSearcher, FileConverter
from gdrive_download.config import GlobalConfig

# Setup configuration
config = GlobalConfig()

# Download documents from folder
downloader = GoogleDriveDownloader(config.downloader)
results = downloader.download_folder("https://drive.google.com/drive/folders/...")

# Search for documents
searcher = GoogleDriveSearcher(config.downloader)
search_results = searcher.search_files(pattern="AAR*", drive_scope="all")

# Convert documents to markdown
converter = FileConverter(input_dir="documents", output_dir="markdown")
converted_files = converter.convert_all_files()
```

### Main Components

#### Downloader Module
The downloader module handles all interactions with Google Drive, including authentication, file discovery, downloading, and format conversion. Key features:
- OAuth2 authentication with token persistence
- Batch downloading from Google Drive folders
- File search across personal and shared drives
- Document conversion to markdown format
- Relationship tracking between Drive URLs and local files

#### Standard Directory Structure
All operations create a consistent directory structure:
```
project_name/
├── documents/              # Downloaded files
├── markdown/               # Converted markdown files
├── file_relationships.csv  # URL to file mappings
└── README.md               # Project overview
```

#### Integration with Document Analysis
For document analysis, use the companion `document-analyzer` package:
```python
from document_analyzer import DocumentAnalyzer

analyzer = DocumentAnalyzer(template="aar")
results = analyzer.analyze_directory("project_name/markdown")
```

### Command Line Tools

#### `gdrive-download` - Download and Convert

Downloads documents from Google Drive and converts them to markdown using the standard directory structure.

```bash
gdrive-download [OPTIONS]

Options:
  -u, --folder-url TEXT     Google Drive folder URL (required)
  -o, --output-dir TEXT     Base output directory (auto-generated from folder name if not specified)
  --documents-subdir TEXT   Subdirectory for downloaded files [default: documents]
  --markdown-subdir TEXT    Subdirectory for markdown files [default: markdown]
  -c, --credentials TEXT    Path to Google API credentials file [default: credentials.json]
  --convert/--no-convert    Convert to markdown [default: convert]
  --track-relationships     Track file relationships [default: True]
  --config-file TEXT        Path to configuration file
  --log-level [DEBUG|INFO|WARNING|ERROR]  [default: INFO]
```

**Example:**
```bash
gdrive-download -u "https://drive.google.com/drive/folders/1UuS4Q2z1nsFI-eEy5K4TLx6qoJvzHrAK" \
             -c credentials.json \
             -o my_project
```

Creates structure:
```
my_project/
├── documents/              # Downloaded files
├── markdown/               # Converted markdown files
└── file_relationships.csv  # URL mappings
```


#### `gdrive-search` - Search Google Drive

Search for files by pattern across Google Drive and optionally download them using the standard directory structure.

```bash
gdrive-search [OPTIONS]

Options:
  -p, --pattern TEXT        File name pattern (required, supports wildcards)
  -s, --scope [personal|all|shared]  Drive scope [default: all]
  --shared-drive-id TEXT    Specific shared drive ID when scope is "shared"
  -t, --file-types TEXT     File types to search [default: document]
  -o, --output-dir TEXT     Base output directory [default: search_<pattern>]
  -c, --credentials TEXT    Google API credentials file [default: credentials.json]
  --download/--no-download  Download found files [default: download]
  --convert/--no-convert    Convert to markdown [default: convert]
  --max-results INT         Maximum results [default: 100]
  --create-shortcuts TEXT   Create shortcuts in specified folder ID
  --since TEXT              Filter files modified since date (e.g., 7d, 2024-01-01)
```

**Examples:**
```bash
# Search for AAR documents
gdrive-search -p "AAR*"

# Search and create shortcuts without downloading
gdrive-search -p "Project Brief*" --no-download --create-shortcuts FOLDER_ID

# Search for recent files (last 7 days)
gdrive-search -p "Report*" --since 7d -o recent_reports
```

Creates structure:
```
search_AAR/  (or specified output directory)
├── documents/              # Downloaded files
├── markdown/               # Converted markdown files
├── search_results.csv      # Search metadata
└── search_summary.md       # Search summary
```

#### `gdrive-manage` - Management Utilities

Collection of utilities for managing document workflows.

```bash
gdrive-manage [COMMAND] [OPTIONS]

Commands:
  init-config              Initialize configuration file
  status                   Show file status and relationships
  update-urls             Update URLs in existing reports
  cleanup                 Clean up temporary files
  version                 Show version information
```

**Examples:**
```bash
# Initialize configuration
gdrive-manage init-config

# Check status
gdrive-manage status --downloads-dir downloads --markdown-dir markdown

# Update report URLs
gdrive-manage update-urls old_report.md url_mappings.json
```

### Configuration

#### Configuration File

Create `gdrive_config.yaml` to customize behavior:

```yaml
downloader:
  output_dir: documents
  batch_size: 10
  credentials_file: credentials.json
  token_file: token.pickle
  
working_dir: .
log_level: INFO
```

#### Environment Variables

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google API credentials

## Document Analysis

For analyzing the downloaded documents, use the companion `document-analyzer` package:

```bash
pip install -e ../document-analyzer
```

```python
from document_analyzer import DocumentAnalyzer

# Analyze documents using built-in templates
analyzer = DocumentAnalyzer(template="aar")
results = analyzer.analyze_directory("my_project/markdown")

# Get analysis results
summary = analyzer.get_summary(results)
```

The document-analyzer package provides:
- **Template-based analysis**: AAR, project review, and custom templates
- **Pattern matching**: Configurable regex patterns for theme identification
- **Pattern extraction**: Identify themes and patterns in documents
- **Multiple formats**: JSON, CSV, and markdown output options

## Project Structure

```
gdrive-download/
├── src/gdrive_download/          # Main package
│   ├── __init__.py
│   ├── config.py                   # Configuration management
│   ├── downloader/                 # Google Drive downloading
│   │   ├── drive_downloader.py       # Core downloading functionality
│   │   ├── drive_searcher.py         # Search functionality
│   │   ├── file_converter.py         # Document conversion
│   │   └── relationship_tracker.py   # File relationship tracking
│   ├── utils/                      # Utility functions
│   │   ├── logging.py
│   │   └── file_utils.py
│   └── cli/                        # Command-line interfaces
│       ├── download.py               # Download command
│       ├── search.py                 # Search command
│       └── manage.py                 # Management utilities
├── src/document_analyzer/          # Companion analysis package
│   ├── core/                       # Analysis framework
│   ├── templates/                  # Document templates (AAR, etc.)
│   └── cli/                        # Analysis CLI tools
├── tests/                          # Test suite
├── examples/                       # Usage examples
│   ├── getting_started.py           # Basic usage
│   ├── complete_workflow.py         # Full workflow
│   └── incremental_download.py      # Smart updates
├── pyproject.toml                  # Package configuration
└── README.md                       # This file
```

## Examples

The `examples/` directory contains three focused example scripts:

### Example 1: Getting Started

Simple download and conversion for first-time users:

```bash
python examples/getting_started.py "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" my_project
```

### Example 2: Complete Workflow

Full workflow with analysis preparation, supports both folder and search modes:

```bash
# Download from folder
python examples/complete_workflow.py folder "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" my_project

# Search and download
python examples/complete_workflow.py search "AAR*" aar_analysis
```

### Example 3: Incremental Download

Smart updates for existing projects, only downloads new/changed files:

```bash
python examples/incremental_download.py "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" my_project
```

All examples create the same standardized directory structure for consistency and tool compatibility.

## Output

### Standard Directory Structure

All tools create this consistent structure:

```
project_name/
├── documents/              # Original downloaded files
├── markdown/               # Converted markdown files
├── file_relationships.csv  # URL to file mappings
└── README.md               # Project overview
```

### Additional Files (Search Command)

When using `gdrive-search`, additional files are created:

- `search_results.csv`: Search metadata and file information
- `search_summary.md`: Summary of search results and statistics

### File Relationships

The `file_relationships.csv` file maintains traceability:

```csv
original_name,google_drive_url,downloaded_file,markdown_file,has_download,has_markdown
Document.docx,https://drive.google.com/file/d/...,documents/Document.docx,markdown/Document.md,True,True
```

### Integration Ready

The output structure is designed for seamless integration with the `document-analyzer` package for further analysis.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/gdrive_download --cov-report=html

# Run specific test file
pytest tests/test_config.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Troubleshooting

### Common Issues

1. **Google API Authentication Errors**
   - Ensure credentials.json is valid and accessible
   - Check that Google Drive API is enabled in your project
   - Verify the folder URL is correct and accessible

2. **File Conversion Errors**
   - Install system dependencies for document conversion
   - Check file permissions in download directories
   - Verify input files are valid .docx format

3. **Memory Issues with Large Datasets**
   - Reduce batch_size in configuration
   - Process files in smaller chunks
   - Monitor disk space for temporary files

### Getting Help

- **Issues**: Report bugs at [GitHub Issues](https://github.com/givingtuesday/gdrive-download/issues)
- **Documentation**: Full documentation at [docs.example.com](https://docs.example.com)
- **Support**: Contact the development team

## License

MIT License - see LICENSE file for details.

## Contributing

We welcome contributions! Please see CONTRIBUTING.md for guidelines.

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Changelog

### v1.0.0 (Current)
- Focused Google Drive downloading and conversion
- Three command-line tools (download, search, manage)
- Standardized directory structure
- Comprehensive test suite
- Separated analysis functionality into document-analyzer package
- Improved search capabilities with pattern matching
