# Google Drive Download Tools

A Python toolkit for searching, downloading, and organizing documents from Google Drive. One simple but important ability is **creating shortcuts (aliases) in a Google Drive folder** that link to all files matching a search pattern—useful for organizing scattered documents without moving or duplicating them. This toolkit serves as the foundation for more advanced document analysis tools used in other GivingTuesday Data Commons projects.

## Key Features

- **Create Shortcuts**: Automatically create Google Drive shortcuts to files matching a search pattern, organizing them in a single folder without moving the originals
- **Search Across Drives**: Search for files by pattern across your personal drive and all shared drives you have access to
- **Download & Convert**: Download Google Docs and Word documents, automatically converting them to markdown format
- **Track Relationships**: Maintain CSV records linking original Google Drive URLs to downloaded files
- **Filter by Date**: Find files modified within a time range (last 7 days, since a specific date, etc.)

## Desktop Application (GUI)

A simple graphical interface is available for users who prefer not to use the command line.

### Download Pre-Built Application

Download the latest release for your platform from the [Releases page](https://github.com/givingtuesday/gdrive-download/releases):

| Platform | Download |
|----------|----------|
| macOS | `GDrive Tools.app` (in .zip) |
| Windows | `GDrive Tools.exe` |
| Linux | `GDrive Tools` |

### First-Time Setup

1. **Get Google API credentials** (see [Getting Google API Credentials](#getting-google-api-credentials))
2. **Place `credentials.json`** in:
   - **Windows**: `%APPDATA%\gdrive-download\`
   - **macOS**: `~/Library/Application Support/gdrive-download/`
   - **Linux**: `~/.config/gdrive-download/`
3. **Launch the application** and use the Browse button to select your credentials if needed

### First Run Notes

- **macOS**: Right-click → Open → Open (to bypass Gatekeeper for unsigned apps)
- **Windows**: Click "More info" → "Run anyway" if SmartScreen appears

---

## Command-Line Installation (For Developers)

### Prerequisites

Before you begin, you'll need:

1. **Python 3.9 or higher** - Check with `python --version` in your terminal
2. **Git** - For cloning the repository
3. **Google Drive API credentials** - See [Getting Google API Credentials](#getting-google-api-credentials) below

### Step 1: Open Your Terminal

- **macOS**: Press `Cmd + Space`, type "Terminal", and press Enter
- **Windows**: Press `Win + R`, type "cmd", and press Enter (or use PowerShell)
- **Linux**: Press `Ctrl + Alt + T` or find Terminal in your applications

### Step 2: Clone the Repository

```bash
# Navigate to where you want to put the project
cd ~/Documents

# Clone the repository
git clone https://github.com/givingtuesday/gdrive-download.git

# Enter the project directory
cd gdrive-download
```

### Step 3: Set Up Python Environment

```bash
# Create a virtual environment
python -m venv .venv

# Activate it
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Install the package
pip install -e .
```

### Step 4: Add Your Google Credentials

Copy your `credentials.json` file (see [Getting Google API Credentials](#getting-google-api-credentials)) into the `gdrive-download` folder.

### Step 5: First Run (Authentication)

The first time you run a command, a browser window will open asking you to authorize access to your Google Drive. After you approve, a `token.pickle` file will be created to remember your authorization.

```bash
# Test with a simple search
gdrive-search -p "test*" --no-download
```

---

## Creating Shortcuts

One simple but important capability is creating **shortcuts** (also called aliases or links) in a Google Drive folder. This lets you:

- Collect related documents from across multiple shared drives into one folder
- Organize files without moving or duplicating them
- Share a curated collection with others by sharing just the shortcuts folder

### Basic Shortcut Creation

```bash
# Search for files and create shortcuts to them (without downloading)
gdrive-search -p "Project Brief*" --no-download --create-shortcuts FOLDER_ID

# Search, download, AND create shortcuts
gdrive-search -p "AAR*" --create-shortcuts FOLDER_ID
```

### Finding Your Folder ID

The `FOLDER_ID` is the long string of characters at the end of a Google Drive folder URL:

```
https://drive.google.com/drive/folders/1ABC123xyz789DEF456ghi
                                        └────────────────────┘
                                         This is the FOLDER_ID
```

**To get a folder ID:**

1. Open Google Drive in your web browser
2. Navigate to the folder where you want shortcuts created (or create a new folder)
3. Look at the URL in your browser's address bar
4. Copy the part after `/folders/`

**Example:**
- URL: `https://drive.google.com/drive/folders/1UuS4Q2z1nsFI-eEy5K4TLx6qoJvzHrAK`
- Folder ID: `1UuS4Q2z1nsFI-eEy5K4TLx6qoJvzHrAK`

### Common Shortcut Workflows

```bash
# Collect all project briefs into one folder
gdrive-search -p "Project Brief*" --no-download --create-shortcuts 1ABC123xyz

# Find recent AARs and organize them
gdrive-search -p "AAR*" --since 30d --no-download --create-shortcuts 1ABC123xyz

# Search only shared drives
gdrive-search -p "Report*" -s shared --no-download --create-shortcuts 1ABC123xyz
```

---

## All Command-Line Tools

### `gdrive-search` - Search and Organize

The primary tool for finding files and creating shortcuts.

```bash
gdrive-search [OPTIONS]

Required:
  -p, --pattern TEXT        File name pattern to search for (supports wildcards)

Options:
  -s, --scope [personal|all|shared]
                            Where to search [default: all]
                            - personal: Only your personal drive
                            - shared: Only shared drives
                            - all: Both personal and shared drives

  --shared-drive-id TEXT    Search a specific shared drive by its ID

  -t, --file-types TEXT     File types to find [default: document]
                            Options: document, spreadsheet, presentation, pdf

  -o, --output-dir TEXT     Where to save downloads [default: search_<pattern>]

  -c, --credentials TEXT    Path to credentials file [default: credentials.json]

  --download/--no-download  Download the files found [default: download]

  --convert/--no-convert    Convert docs to markdown [default: convert]

  --max-results INT         Maximum files to find [default: 100]

  --create-shortcuts TEXT   Create shortcuts in this folder ID

  --since TEXT              Only files modified since this date
                            Examples: 7d, 2w, 30d, 2024-01-01
```

**Examples:**

```bash
# Find all AAR documents
gdrive-search -p "AAR*"

# Find files modified in the last week, create shortcuts only
gdrive-search -p "*2024*" --since 7d --no-download --create-shortcuts FOLDER_ID

# Search only personal drive with a regex pattern
gdrive-search -p "^Report.*\.docx$" -s personal

# Search with specific file types
gdrive-search -p "Budget*" -t spreadsheet
```

### `gdrive-download` - Download from a Folder

Download all documents from a specific Google Drive folder.

```bash
gdrive-download [OPTIONS]

Required:
  -u, --folder-url TEXT     Google Drive folder URL

Options:
  -o, --output-dir TEXT     Where to save files [default: auto-generated]
  -c, --credentials TEXT    Credentials file [default: credentials.json]
  --convert/--no-convert    Convert to markdown [default: convert]
  --track-relationships     Create CSV tracking file [default: True]
```

**Finding a Folder URL:**

1. Open the folder in Google Drive
2. Copy the entire URL from your browser

**Example:**

```bash
gdrive-download -u "https://drive.google.com/drive/folders/1UuS4Q2z1nsFI-eEy5K4TLx6qoJvzHrAK"
```

### `gdrive-manage` - Utilities

```bash
gdrive-manage [COMMAND]

Commands:
  status        Show download/conversion status
  init-config   Create a configuration file
  version       Show version information
```

---

## Understanding Google Drive URLs and IDs

### Folder URLs and IDs

| What | Example |
|------|---------|
| Folder URL | `https://drive.google.com/drive/folders/1ABC123xyz789DEF456` |
| Folder ID | `1ABC123xyz789DEF456` |

### File URLs and IDs

| What | Example |
|------|---------|
| File URL | `https://drive.google.com/file/d/1XYZ789abc123DEF456/view` |
| File ID | `1XYZ789abc123DEF456` |

### Shared Drive URLs

| What | Example |
|------|---------|
| Shared Drive URL | `https://drive.google.com/drive/folders/0APQ123abc789?resourcekey=...` |
| Shared Drive ID | `0APQ123abc789` |

**Tip:** Shared drive IDs often start with `0A`.

---

## Getting Google API Credentials

To use these tools, you need to create Google API credentials:

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top, then "New Project"
3. Name it something like "Drive Download Tool"
4. Click "Create"

### Step 2: Enable the Google Drive API

1. In your new project, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

### Step 3: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless you have a Workspace account)
   - Fill in the required fields (app name, email)
   - Add yourself as a test user
4. For Application type, choose "Desktop app"
5. Click "Create"

### Step 4: Download Credentials

1. Click the download icon next to your new credential
2. Rename the file to `credentials.json`
3. Move it to your `gdrive-download` folder

---

## Output Structure

When you download files, this structure is created:

```
search_AAR/                      # Output directory (named after search)
├── documents/                   # Downloaded original files
│   ├── AAR_Project_Alpha.docx
│   └── AAR_Project_Beta.docx
├── markdown/                    # Converted markdown files
│   ├── AAR_Project_Alpha.md
│   └── AAR_Project_Beta.md
├── search_results.csv           # Metadata about found files
└── file_relationships.csv       # Maps URLs to local files
```

---

## Search Patterns

The `-p/--pattern` option supports several pattern types:

| Pattern | Matches |
|---------|---------|
| `AAR*` | Files starting with "AAR" |
| `*2024*` | Files containing "2024" anywhere |
| `*.docx` | Files ending with ".docx" |
| `Project Brief*` | Files starting with "Project Brief" |
| `^AAR.*\.docx$` | Regex: AAR files that are .docx |

---

## Configuration File (Optional)

Create `gdrive_config.yaml` for persistent settings:

```yaml
downloader:
  output_dir: documents
  batch_size: 10
  credentials_file: credentials.json
  token_file: token.pickle

working_dir: .
log_level: INFO
```

---

## Troubleshooting

### "credentials.json not found"

Make sure your `credentials.json` file is in the current directory, or specify its path:

```bash
gdrive-search -p "AAR*" -c /path/to/credentials.json
```

### "Access denied" or "File not found"

- Verify you have access to the folder/files in Google Drive
- Check that the folder ID or URL is correct
- For shared drives, you may need to be explicitly added as a member

### "Token has been expired or revoked"

Delete `token.pickle` and run the command again to re-authenticate:

```bash
rm token.pickle
gdrive-search -p "test*" --no-download
```

### Browser doesn't open for authentication

If running on a remote server, you may need to copy the authentication URL and open it manually in a local browser.

---

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/gdrive_download
```

### Code Quality

```bash
black src/ tests/      # Format code
isort src/ tests/      # Sort imports
mypy src/              # Type checking
flake8 src/ tests/     # Linting
```

---

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request
