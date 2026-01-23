# Installed Tools - gdrive-download v0.1.0

**Installation Method:** `uv tool install --editable .`
**Installation Location:** `~/.local/bin/`
**Last Updated:** 2026-01-23

## Available Commands

All commands are globally available after installation:

### 1. gdrive-download
**Purpose:** Download documents from Google Drive and convert to markdown

**Key Features:**
- Downloads files from Google Drive folders
- Converts Word documents to markdown using mammoth + markdownify
- Tracks file relationships (URLs → local files → markdown)
- Creates standardized directory structure

**Usage:**
```bash
gdrive-download -u "https://drive.google.com/drive/folders/FOLDER_ID" -c credentials.json
```

**Options:**
- `-u, --folder-url` - Google Drive folder URL (required)
- `-o, --output-dir` - Base output directory
- `-c, --credentials` - Path to Google API credentials file
- `--convert / --no-convert` - Convert downloaded files to markdown
- `--track-relationships` - Track file relationships

---

### 2. gdrive-search
**Purpose:** Search for files in Google Drive by name pattern

**Key Features:**
- Search across personal and shared drives
- Pattern matching (glob or regex)
- Time-based filtering (--since flag)
- Optional download of results
- Create shortcuts to search results

**Usage:**
```bash
# Search for AAR documents
gdrive-search -p "AAR*"

# Search with date filter
gdrive-search -p "Report*" --since 7d

# Create shortcuts without downloading
gdrive-search -p "Project*" --no-download --create-shortcuts FOLDER_ID
```

**Options:**
- `-p, --pattern` - Search pattern (glob or regex)
- `-s, --scope` - Search scope (personal, shared, all)
- `--since` - Filter by modification date (e.g., 7d, 2w, 2024-01-01)
- `--create-shortcuts` - Create shortcuts to results in target folder
- `--no-download` - Skip downloading files

---

### 3. gdrive-upload
**Purpose:** Upload markdown files to Google Drive as native Google Docs

**Key Features:**
- Converts markdown → HTML → Google Docs
- Preserves formatting (headers, bold, italic, lists, links)
- Bulk upload support
- Skip existing documents option
- **NEW (2026-01-23):** Enhanced CSS for proper style inheritance

**Usage:**
```bash
# Upload single file
gdrive-upload -f report.md --folder-id 1ABC123

# Upload multiple files
gdrive-upload -f doc1.md -f doc2.md --folder-id 1ABC123

# Upload directory
gdrive-upload -d markdown/ --folder-id 1ABC123
```

**Options:**
- `-f, --file` - Markdown file(s) to upload (multiple allowed)
- `-d, --directory` - Directory containing markdown files
- `-t, --folder-id` - Target Google Drive folder ID
- `--folder-url` - Alternative to folder-id
- `--skip-existing / --replace-existing` - Handle existing documents
- `--preview / --no-preview` - Preview before upload

**Recent Fix (2026-01-23):**
- Fixed inappropriate style attributes in HTML export
- Normal text now inherits target document's font styles
- Only code blocks use explicit monospace fonts

---

### 4. gdrive-write-tab
**Purpose:** Write markdown content to specific tabs in existing Google Docs

**Key Features:**
- Direct API integration (no HTML conversion)
- Tab-specific writing
- Append or replace mode
- Safety confirmations
- Preserves document structure

**Usage:**
```bash
# Write to first tab (append mode)
gdrive-write-tab -f notes.md --doc-id 1ABC123XYZ

# Write to specific tab
gdrive-write-tab -f notes.md --doc-url "https://docs.google.com/document/d/1ABC123/edit?tab=t.0"

# Replace existing content
gdrive-write-tab -f notes.md --doc-id 1ABC123 --replace
```

**Options:**
- `-f, --file` - Markdown file to write (required)
- `--doc-url` - Google Doc URL (may include tab ID)
- `--doc-id` - Google Doc document ID
- `--tab-id` - Tab ID to write to (default: first tab)
- `--append / --replace` - Append or replace content
- `--force` - Skip confirmation prompt

**Safety Features:**
- Shows preview of existing content
- Requires confirmation unless --force
- Append mode by default

---

### 5. gdrive-manage
**Purpose:** Manage tools, workflows, and maintenance tasks

**Key Features:**
- Status reporting
- Configuration management
- Cleanup utilities
- Version information

**Usage:**
```bash
# Show status
gdrive-manage status

# Initialize config
gdrive-manage init-config

# Cleanup temporary files
gdrive-manage cleanup

# Show version
gdrive-manage version
```

**Subcommands:**
- `status` - Show status of files and relationships
- `init-config` - Initialize new configuration file
- `cleanup` - Clean up temporary files and duplicates
- `version` - Show version information

---

### 6. gdrive-gui
**Purpose:** Graphical user interface for gdrive-download tools

**Key Features:**
- PyQt5-based GUI
- Visual file management
- Integrated search and download
- Settings management

**Usage:**
```bash
gdrive-gui
```

---

## Architecture

### Two Export Workflows

1. **HTML Import Path** (`gdrive-upload`)
   - Markdown → HTML → Google Docs import
   - Uses CSS with `font-family: inherit` for style inheritance
   - Bulk upload optimized

2. **Direct API Path** (`gdrive-write-tab`)
   - Markdown → Google Docs API batchUpdate requests
   - Direct content insertion into tabs
   - Fine-grained control over formatting

### Core Components

- **GoogleDriveDownloader:** OAuth authentication and file downloads
- **GoogleDriveSearcher:** Advanced search with pattern matching
- **GoogleDriveUploader:** Markdown to Google Docs conversion
- **FileConverter:** Word to markdown conversion
- **FileRelationshipTracker:** URL and file mapping

### Configuration

- Uses Pydantic models for type-safe configuration
- YAML configuration file support
- OAuth2 with credentials.json and token.pickle
- Configurable output directories

---

## Testing

All commands include comprehensive test coverage:
- 33 tests for drive_uploader
- CLI integration tests
- Pattern matching tests
- Authentication flow tests

Test coverage: 75% for core upload functionality

---

## Recent Updates (2026-01-23)

### Fixed: Style Inheritance Issue
- **Problem:** HTML import was applying explicit fonts that overrode target document styles
- **Solution:** Added CSS with `font-family: inherit` to HTML wrapper
- **Result:** Normal text now inherits from target document
- **Files Changed:**
  - `src/gdrive_download/downloader/drive_uploader.py`
  - `tests/downloader/test_drive_uploader.py`

---

## Installation

### Install/Update
```bash
# Install editable version
uv tool install --editable .

# Reinstall after updates
uv tool install --force --editable .
```

### Verify Installation
```bash
# Check all commands are available
which gdrive-download gdrive-search gdrive-upload gdrive-write-tab gdrive-manage gdrive-gui

# List installed tools
uv tool list
```

### Uninstall
```bash
uv tool uninstall gdrive-download
```

---

## Dependencies

**Core:**
- google-api-python-client (Google Drive/Docs API)
- markdown-it-py (Markdown parsing)
- mammoth (Word to markdown conversion)
- click (CLI framework)
- rich (Terminal output)
- PyQt5 (GUI)

**Development:**
- pytest + pytest-cov (Testing)
- black, isort, flake8 (Code quality)
- mypy (Type checking)

---

## See Also

- [README.md](README.md) - Project overview
- [CLAUDE.md](CLAUDE.md) - Development guidelines
- [pyproject.toml](pyproject.toml) - Package configuration
