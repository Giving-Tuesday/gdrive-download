# GivingTuesday AAR Package

Core Python package for downloading, converting, and analyzing After Action Review documents.

## Package Structure

```
givingtuesday_aar/
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
from givingtuesday_aar import GoogleDriveDownloader, AARAnalyzer
from givingtuesday_aar.config import GlobalConfig

# Load configuration
config = GlobalConfig.from_yaml("aar_config.yaml")

# Download documents
downloader = GoogleDriveDownloader(config.downloader)
files = downloader.download_folder(folder_url)

# Analyze content
analyzer = AARAnalyzer(config.analyzer)
analyzer.analyze_all()
analyzer.generate_reports()
```

## Environment Variables

- `AAR_CONFIG_FILE`: Default configuration file path
- `AAR_LOG_LEVEL`: Default logging level
- `GOOGLE_APPLICATION_CREDENTIALS`: Google API credentials path

## See Also

- [Downloader Module](./downloader/README.md)
- [Analyzer Module](./analyzer/README.md)
- [CLI Module](./cli/README.md)
- [Utils Module](./utils/README.md)