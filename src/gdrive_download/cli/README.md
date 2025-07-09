# CLI Module

Command-line interfaces for the Google Drive Download package.

## Commands

### download.py
- **gdrive-download**: Download and convert Google Drive documents
  - Downloads from Google Drive folders
  - Converts Word documents to markdown
  - Tracks file relationships
  - Supports batch processing

### search.py
- **gdrive-search**: Search Google Drive by file patterns
  - Pattern-based search across drives
  - Wildcard and regex support
  - Date filtering for recent files
  - Optional downloading and conversion
  - Shortcut creation for organizing results

### analyze.py
- **gdrive-analyze**: Analyze documents and generate reports
  - Processes markdown documents
  - Identifies patterns and themes
  - Generates multiple report types
  - Exports analysis data

### extract_data.py
- **gdrive-extract-data**: Extract specific data from documents
  - Section extraction from templated documents
  - JSON transformation of document content
  - Batch processing capabilities

### manage.py
- **gdrive-manage**: Management and utility commands
  - Initialize configuration files
  - Check system status
  - Update file relationships
  - Clean temporary files
  - Display version information

## Common Options

All CLI commands support:
- `--config-file`: Custom configuration file path
- `--log-level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `--help`: Display command help

## Examples

```bash
# Download documents
gdrive-download -u "https://drive.google.com/drive/folders/..." -c credentials.json

# Search for files
gdrive-search -p "*" --since 7d

# Analyze and report
gdrive-analyze -i markdown -o reports

# Check status
gdrive-manage status
```