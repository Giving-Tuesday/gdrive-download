#!/usr/bin/env python3
"""Test the shortcuts functionality directly."""

import sys
sys.path.insert(0, '/Users/pricemat/src/gdrive-download/src')

from gdrive_download.config import GlobalConfig
from gdrive_download.downloader.drive_searcher import GoogleDriveSearcher
from pathlib import Path

# Setup
config = GlobalConfig()
config.downloader.credentials_file = Path("credentials.json")
config.downloader.token_file = Path("token.pickle")

# Create searcher
searcher = GoogleDriveSearcher(config.downloader)

# Search for files
print("🔍 Searching for 'Project Brief*' files...")
results = searcher.search_files(
    pattern="Project Brief*",
    drive_scope="all",
    file_types=['document'],
    max_results=20
)

print(f"✅ Found {len(results)} files")

# Display results
searcher.display_results(results, show_limit=5)

# Create shortcuts
folder_id = "1l6STAueoQ1zMbnxpcAlvBK7YSC4nOvjy"
print(f"\n🔗 Creating shortcuts in folder ID: {folder_id}")

try:
    shortcut_results = searcher.create_shortcuts(results, folder_id)
    
    print(f"\n✅ Created {shortcut_results['success_count']} shortcuts in '{shortcut_results['folder_name']}'")
    
    if shortcut_results['errors']:
        print(f"\n⚠️  {len(shortcut_results['errors'])} errors occurred:")
        for error in shortcut_results['errors'][:3]:
            print(f"  • {error}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()