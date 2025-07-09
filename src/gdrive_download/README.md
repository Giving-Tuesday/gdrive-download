# Google Drive Download Package

Core Python package for downloading and converting documents from Google Drive to markdown format.

## Package Structure

```
gdrive_download/
├── __init__.py          # Package initialization and exports
├── config.py            # Configuration management with Pydantic
├── downloader/          # Google Drive operations
├── cli/                 # Command-line interfaces
└── utils/               # Utility functions
```

## Key Classes

### config.py
- **GlobalConfig**: Main configuration container
- **DownloaderConfig**: Settings for Google Drive operations

### downloader/
- **GoogleDriveDownloader**: OAuth authentication and file downloads
- **GoogleDriveSearcher**: Search files across Google Drive
- **FileConverter**: Convert Word documents to markdown
- **FileRelationshipTracker**: Track file relationships

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from gdrive_download import GoogleDriveDownloader, FileConverter
from gdrive_download.config import GlobalConfig

# Load configuration
config = GlobalConfig.from_yaml("gdrive_config.yaml")

# Download documents
downloader = GoogleDriveDownloader(config.downloader)
files = downloader.download_folder(folder_url)

# Convert to markdown
converter = FileConverter()
for file_path in files:
    converter.convert_to_markdown(file_path)
```

## CLI Usage

```bash
# Download and convert documents
gdrive-download -u "https://drive.google.com/drive/folders/FOLDER_ID" -c credentials.json

# Search for files
gdrive-search -p "*.docx" -c credentials.json

# Manage configuration
gdrive-manage init-config
gdrive-manage status
```

## Environment Variables

- `GDRIVE_CONFIG_FILE`: Default configuration file path
- `GDRIVE_LOG_LEVEL`: Default logging level
- `GOOGLE_APPLICATION_CREDENTIALS`: Google API credentials path

## See Also

- [Downloader Module](./downloader/README.md)
- [CLI Module](./cli/README.md)
- [Utils Module](./utils/README.md)

## Analysis

For document analysis capabilities, see the separate `document_analyzer` package.