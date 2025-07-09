# Examples Directory

This directory contains 3 essential example scripts that demonstrate the core functionality of the `gdrive-download` package.

## Prerequisites

Before running any examples, you need:

1. **Google Drive API Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create/select a project
   - Enable Google Drive API
   - Create OAuth 2.0 credentials
   - Download and save as `credentials.json` in this directory

2. **Python Dependencies**
   ```bash
   pip install -e .  # Install gdrive-download package
   ```

## Example Scripts

### 1. `getting_started.py` - Basic Download and Conversion

**Best for:** First-time users, simple document collection

```bash
python getting_started.py "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" my_project
```

**What it does:**
- Downloads all files from a Google Drive folder
- Converts documents to markdown
- Creates standard directory structure
- Tracks file relationships
- Generates a project README

**Output structure:**
```
my_project/
├── documents/              # Downloaded files
├── markdown/               # Converted markdown files
├── file_relationships.csv  # URL mappings
└── README.md               # Project overview
```

### 2. `complete_workflow.py` - Full Workflow with Analysis Prep

**Best for:** Complete projects, analysis preparation, flexible input sources

```bash
# Download from folder
python complete_workflow.py folder "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" my_project

# Search and download
python complete_workflow.py search "AAR*" aar_analysis
```

**What it does:**
- Downloads from folder URL OR searches by pattern
- Converts documents to markdown
- Tracks file relationships
- Prepares configuration for document analysis
- Creates comprehensive project documentation

**Output structure:**
```
my_project/
├── documents/              # Downloaded files
├── markdown/               # Converted markdown files
├── analysis/               # Ready for analysis
├── file_relationships.csv  # URL mappings
├── analysis_config.json    # Analysis configuration
└── README.md               # Project overview
```

### 3. `incremental_download.py` - Smart Updates

**Best for:** Updating existing projects, avoiding re-downloads

```bash
python incremental_download.py "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" my_project
```

**What it does:**
- Checks what files already exist as markdown
- Only downloads and converts new/changed files
- Maintains existing project structure
- Provides detailed progress reporting

**Use cases:**
- Updating a project with new documents
- Resuming an interrupted download
- Periodic synchronization with Google Drive

## Integration with Document Analysis

All examples create projects compatible with the `document-analyzer` package:

```bash
# After running any example
cd my_project
document-analyzer -i markdown -o analysis --template aar
```

## Directory Structure Pattern

All examples follow the same standardized pattern:

```
<project_name>/
├── documents/              # Original downloaded files
├── markdown/               # Converted markdown files  
├── analysis/               # Analysis results (optional)
├── file_relationships.csv  # URL to file mappings
└── README.md               # Project documentation
```

This structure ensures:
- **Consistency** across all projects
- **Traceability** back to original Google Drive sources
- **Compatibility** with analysis tools
- **Easy sharing** and archiving

## Common Patterns

### Basic Usage
```bash
# Simple download
python getting_started.py "https://drive.google.com/drive/folders/..." project_name

# Search-based download
python complete_workflow.py search "AAR*" aar_project

# Update existing project
python incremental_download.py "https://drive.google.com/drive/folders/..." project_name
```

### Error Handling
- Check that `credentials.json` exists
- Verify folder URL is correct and accessible
- Ensure you have read permissions on the folder
- Re-run if authentication tokens need refresh

### Project Organization
- Use descriptive project names
- Keep projects in separate directories
- Include the CSV file when sharing projects
- Document the original Google Drive source

## Next Steps

1. **Choose your example** based on your use case
2. **Set up credentials** (credentials.json)
3. **Run the example** with your Google Drive folder
4. **Explore the results** in the created project directory
5. **Analyze documents** using the document-analyzer package

For more information, see the main [README.md](../README.md) and [DIRECTORY_STRUCTURE.md](../DIRECTORY_STRUCTURE.md).