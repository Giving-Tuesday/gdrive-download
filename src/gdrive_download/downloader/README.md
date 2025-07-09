# Downloader Module

This module handles all interactions with Google Drive for downloading and converting documents.

## Components

### drive_downloader.py
- **GoogleDriveDownloader**: Main class for Google Drive operations
  - OAuth2 authentication with token persistence
  - Batch downloading of files from folders
  - Progress tracking and error handling
  - Support for both personal and shared drives

### drive_searcher.py
- **GoogleDriveSearcher**: Search functionality across Google Drive
  - Pattern-based file search (wildcards and regex)
  - Multi-drive search (personal, shared, or all)
  - Date filtering for recent files
  - Shortcut creation for organizing search results

### file_converter.py
- **FileConverter**: Document format conversion
  - Converts .docx files to clean markdown
  - Uses mammoth for high-quality Word document parsing
  - Preserves document structure and formatting
  - Handles embedded images and tables

### relationship_tracker.py
- **FileRelationshipTracker**: Maintains links between files
  - Tracks Google Drive URLs to local file mappings
  - CSV-based persistent storage
  - Enables citation generation in reports
  - Supports URL updates and relationship queries

## Usage

```python
from gdrive_download.downloader import GoogleDriveDownloader, GoogleDriveSearcher

# Download files
downloader = GoogleDriveDownloader(config)
results = downloader.download_folder("https://drive.google.com/drive/folders/...")

# Search files
searcher = GoogleDriveSearcher(config)
files = searcher.search_files(pattern="*", drive_scope="all")
```