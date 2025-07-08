# GivingTuesday AAR Tools

A modular Python package for downloading, converting, and analyzing After Action Review (AAR) documents from Google Drive. This tool helps organizations systematically analyze their post-event reviews to identify patterns, challenges, and successes across multiple operations.

## Features

- **Google Drive Integration**: Download documents from shared Google Drive folders with full authentication support
- **Document Conversion**: Convert Word documents (.docx) to markdown using high-quality mammoth + markdownify pipeline
- **Pattern Analysis**: Identify recurring themes in challenges and successes using configurable regex patterns
- **Relationship Tracking**: Maintain links between original Google Drive URLs, downloaded files, and converted markdown
- **Report Generation**: Create comprehensive markdown reports with direct citations to source documents
- **CLI Interface**: Three command-line tools for streamlined workflows
- **Extensible**: Modular architecture allows for custom analysis patterns and workflows

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Drive API credentials (see [Setup Guide](#google-drive-setup))

### Install from Source

```bash
# Clone and navigate to the refactor directory
cd refactor/

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# For development with testing tools
pip install -e ".[dev]"
```

## Quick Start

### 1. Google Drive Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials file as `credentials.json`

### 2. Basic Usage

```bash
# Download and convert documents
aar-download --folder-url "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" \
             --credentials credentials.json

# Analyze and generate reports
aar-analyze --input-dir markdown --output-dir reports

# Check status
aar-manage status
```

### 3. Python API

```python
from givingtuesday_aar import GoogleDriveDownloader, AARAnalyzer
from givingtuesday_aar.config import GlobalConfig

# Setup configuration
config = GlobalConfig()

# Download documents
downloader = GoogleDriveDownloader(config.downloader)
results = downloader.download_folder("https://drive.google.com/drive/folders/...")

# Analyze content
analyzer = AARAnalyzer(config.analyzer)
challenges = analyzer.analyze_challenges()
successes = analyzer.analyze_successes()
```

## Command Line Tools

### `aar-download` - Download and Convert

Downloads documents from Google Drive and converts them to markdown.

```bash
aar-download [OPTIONS]

Options:
  -u, --folder-url TEXT     Google Drive folder URL (required)
  -o, --output-dir TEXT     Output directory for downloads [default: downloads]
  -m, --markdown-dir TEXT   Output directory for markdown [default: markdown]
  -c, --credentials TEXT    Path to Google API credentials file
  --convert/--no-convert    Convert to markdown [default: convert]
  --track-relationships     Track file relationships [default: True]
  --config-file TEXT        Path to configuration file
  --log-level [DEBUG|INFO|WARNING|ERROR]  [default: INFO]
```

**Example:**
```bash
aar-download -u "https://drive.google.com/drive/folders/1UuS4Q2z1nsFI-eEy5K4TLx6qoJvzHrAK" \
             -c credentials.json \
             -o downloads \
             -m markdown
```

### `aar-analyze` - Generate Analysis Reports

Analyzes markdown documents and generates comprehensive reports.

```bash
aar-analyze [OPTIONS]

Options:
  -i, --input-dir TEXT      Directory with markdown files [default: markdown]
  -o, --output-dir TEXT     Directory for reports [default: reports]
  -t, --report-type [challenges|successes|insights|all]  [default: all]
  --url-mappings TEXT       Path to URL mappings file
  --save-analysis           Save detailed analysis data [default: True]
  --config-file TEXT        Path to configuration file
  --log-level [DEBUG|INFO|WARNING|ERROR]  [default: INFO]
```

**Example:**
```bash
aar-analyze -i markdown \
            -o reports \
            -t all \
            --url-mappings file_relationships.csv
```

### `aar-manage` - Management Utilities

Collection of utilities for managing AAR workflows.

```bash
aar-manage [COMMAND] [OPTIONS]

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
aar-manage init-config

# Check status
aar-manage status --downloads-dir downloads --markdown-dir markdown

# Update report URLs
aar-manage update-urls old_report.md url_mappings.json
```

## Configuration

### Configuration File

Create `aar_config.yaml` to customize behavior:

```yaml
downloader:
  output_dir: downloads
  batch_size: 10
  
analyzer:
  input_dir: markdown
  output_dir: reports
  challenge_patterns:
    resource_constraints: "(?i)(resource|staff|capacity|budget)"
    communication: "(?i)(communication|coordination|messaging)"
  success_patterns:
    leadership: "(?i)(leader|development|empowerment)"
    innovation: "(?i)(innovation|creative|breakthrough)"
    
log_level: INFO
```

### Environment Variables

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google API credentials
- `AAR_CONFIG_FILE`: Path to configuration file
- `AAR_LOG_LEVEL`: Default logging level

## Analysis Patterns

The tool identifies themes using configurable regex patterns:

### Default Challenge Patterns
- **Resource Constraints**: staff, capacity, budget, funding issues
- **Data Collection**: measurement, tracking, reporting difficulties  
- **Communication**: coordination, messaging, coverage gaps
- **Partnership**: collaboration, stakeholder management issues
- **Timing & Scope**: planning, timeline, expectation challenges

### Default Success Patterns
- **Leadership**: development, empowerment, capacity building
- **Content**: creation, engagement, quality storytelling
- **Agility**: innovation, opportunity recognition, adaptability
- **Data Excellence**: measurement, research, insights
- **Partnerships**: collaboration, network building
- **Community**: engagement, mobilization, participation

## Project Structure

```
refactor/
├── src/givingtuesday_aar/          # Main package
│   ├── __init__.py
│   ├── config.py                   # Configuration management
│   ├── downloader/                 # Google Drive downloading
│   │   ├── drive_downloader.py
│   │   ├── file_converter.py
│   │   └── relationship_tracker.py
│   ├── analyzer/                   # Content analysis
│   │   ├── aar_analyzer.py
│   │   ├── pattern_matcher.py
│   │   └── report_generator.py
│   ├── utils/                      # Utility functions
│   │   ├── logging.py
│   │   └── file_utils.py
│   └── cli/                        # Command-line interfaces
│       ├── download.py
│       ├── analyze.py
│       └── manage.py
├── tests/                          # Test suite
├── examples/                       # Usage examples
│   ├── basic_usage.py
│   ├── cli_workflow.sh
│   └── custom_patterns.py
├── pyproject.toml                  # Package configuration
└── README.md                       # This file
```

## Examples

### Example 1: Basic Workflow

See `examples/basic_usage.py` for a complete Python workflow example.

```bash
python examples/basic_usage.py
```

### Example 2: CLI Workflow

See `examples/cli_workflow.sh` for a complete command-line workflow.

```bash
./examples/cli_workflow.sh
```

### Example 3: Custom Analysis Patterns

See `examples/custom_patterns.py` for customizing analysis patterns.

```bash
python examples/custom_patterns.py
```

## Output

### Generated Reports

1. **Challenges Report** (`challenges_report.md`): Systematic analysis of recurring problems with citations
2. **Successes Report** (`successes_report.md`): Organizational strengths and wins with examples  
3. **Insights Report** (`insights_report.md`): Cross-cutting themes and high-level patterns

### Data Files

- `file_relationships.csv`: Mapping between Google Drive URLs, downloads, and markdown files
- `*_analysis.json`: Detailed analysis data for programmatic use

### Citations

All reports include direct citations linking back to original Google Drive documents:

```markdown
*"Resource constraints limited our capacity"* ([Document Name](https://drive.google.com/file/d/FILE_ID/view))
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/givingtuesday_aar --cov-report=html

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

- **Issues**: Report bugs at [GitHub Issues](https://github.com/givingtuesday/aar-tools/issues)
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
- Initial modular architecture
- Complete CLI interface
- Comprehensive test suite
- Pattern-based analysis system
- Google Drive integration
- Markdown report generation