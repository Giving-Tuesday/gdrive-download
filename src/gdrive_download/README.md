# Google Drive Download Package

Core Python package for downloading, converting, and analyzing documents from Google Drive.

## Package Structure

```
gdrive_download/
├── __init__.py          # Package initialization and exports
├── config.py            # Configuration management with Pydantic
├── downloader/          # Google Drive operations
├── analyzer/            # Document analysis and reporting
├── cli/                 # Command-line interfaces
└── utils/               # Utility functions
```

## Key Classes

### config.py
- **GlobalConfig**: Main configuration container
- **DownloaderConfig**: Settings for Google Drive operations
- **AnalyzerConfig**: Analysis patterns and settings
- **AnalysisPattern**: Pattern definition for theme detection

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from gdrive_download import GoogleDriveDownloader, DocumentAnalyzer
from gdrive_download.config import GlobalConfig

# Load configuration
config = GlobalConfig.from_yaml("gdrive_config.yaml")

# Download documents
downloader = GoogleDriveDownloader(config.downloader)
files = downloader.download_folder(folder_url)

# Analyze content
analyzer = DocumentAnalyzer(config.analyzer)
analyzer.analyze_all()
analyzer.generate_reports()
```

## Environment Variables

- `GDRIVE_CONFIG_FILE`: Default configuration file path
- `GDRIVE_LOG_LEVEL`: Default logging level
- `GOOGLE_APPLICATION_CREDENTIALS`: Google API credentials path

## See Also

- [Downloader Module](./downloader/README.md)
- [Analyzer Module](./analyzer/README.md)
- [CLI Module](./cli/README.md)
- [Utils Module](./utils/README.md)