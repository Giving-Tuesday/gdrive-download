# Utils Module

Utility functions and helpers used throughout the GivingTuesday AAR Tools package.

## Components

### logging.py
- **setup_logging**: Configure logging for the application
  - Colored console output with Rich
  - File logging support
  - Configurable log levels
  - Structured log formatting

### file_utils.py
- **ensure_directory**: Create directories if they don't exist
  - Safe directory creation
  - Parent directory handling
  - Permission management
  
- **sanitize_filename**: Clean filenames for filesystem compatibility
  - Remove invalid characters
  - Handle unicode properly
  - Prevent path traversal
  
- **get_file_hash**: Calculate file checksums
  - MD5 and SHA256 support
  - Efficient chunked reading
  - Duplicate detection

## Usage

```python
from givingtuesday_aar.utils import setup_logging, ensure_directory

# Setup logging
logger = setup_logging(log_level="INFO")

# Ensure output directory exists
ensure_directory("output/reports")
```

## Features

- Cross-platform file handling
- Robust error handling
- Performance optimizations
- Type-safe interfaces