#!/usr/bin/env python3
"""
Example script demonstrating how to search for files by pattern and download them.

This example shows how to:
1. Search for files matching a pattern across Google Drive
2. Download all matching files
3. Convert them to markdown
4. Organize outputs by search pattern
"""

import sys
import re
from pathlib import Path
from gdrive_download.config import GlobalConfig
from gdrive_download.downloader import GoogleDriveDownloader, FileConverter, GoogleDriveSearcher

def sanitize_pattern_for_dir(pattern: str) -> str:
    """Convert a search pattern to a safe directory name."""
    # Remove regex anchors and special characters
    safe_name = pattern.replace('^', '').replace('$', '').replace('.*', '_')
    safe_name = re.sub(r'[<>:"/\\|?*\[\]]', '_', safe_name)
    safe_name = safe_name.strip('_. ')
    
    if not safe_name:
        safe_name = "search_results"
    
    return safe_name[:50]  # Limit length


def main():
    """Demonstrate search and download workflow."""
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("❌ Please provide a search pattern")
        print("Usage: python search_and_download.py <pattern> [drive_scope]")
        print("\nExamples:")
        print("  python search_and_download.py 'AAR*'              # Files starting with AAR")
        print("  python search_and_download.py '*2024*'            # Files containing 2024")
        print("  python search_and_download.py '^AAR.*\\.docx$'    # Regex pattern")
        print("  python search_and_download.py 'AAR*' personal     # Search only personal drive")
        print("  python search_and_download.py 'AAR*' all          # Search all drives (default)")
        print("\nDrive scopes: personal, all, shared")
        return
    
    pattern = sys.argv[1]
    drive_scope = sys.argv[2] if len(sys.argv) > 2 else "all"
    
    # Configuration
    config = GlobalConfig()
    credentials_file = Path("credentials.json")
    token_file = Path("token.pickle")
    
    # Check credentials
    if not credentials_file.exists():
        print("❌ credentials.json not found!")
        print("💡 Please:")
        print("   1. Download credentials from Google Cloud Console")
        print("   2. Save as 'credentials.json' in the current directory")
        print("   3. See README.md for detailed setup instructions")
        return
    
    # Create output directory based on pattern
    base_dir = Path(f"search_{sanitize_pattern_for_dir(pattern)}")
    config.downloader.output_dir = base_dir / "downloads"
    config.downloader.credentials_file = credentials_file
    config.downloader.token_file = token_file
    markdown_dir = base_dir / "markdown"
    
    # Create directories
    for dir_path in [base_dir, config.downloader.output_dir, markdown_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("🔍 Google Drive File Search and Download")
    print(f"📋 Search pattern: {pattern}")
    print(f"🌐 Search scope: {drive_scope}")
    print(f"📁 Output directory: {base_dir}/")
    
    # Step 1: Search for files
    print("\n🔎 Step 1: Searching for files...")
    
    try:
        searcher = GoogleDriveSearcher(config.downloader)
        
        # Search with document type filter for AAR documents
        search_results = searcher.search_files(
            pattern=pattern,
            drive_scope=drive_scope,
            file_types=['document'],  # Focus on documents
            max_results=100
        )
        
        print(f"\n✅ Found {len(search_results)} matching files")
        
        if not search_results:
            print("💡 No files found. Try a different pattern or check permissions.")
            return
        
        # Display results
        searcher.display_results(search_results, show_limit=10)
        
        # Save search results
        results_file = base_dir / "search_results.csv"
        searcher.save_results(search_results, results_file)
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        return
    
    # Ask for confirmation before downloading
    if len(search_results) > 10:
        response = input(f"\n⚠️  Download all {len(search_results)} files? (y/N): ")
        if response.lower() != 'y':
            print("❌ Download cancelled")
            return
    
    # Step 2: Download files
    print("\n📥 Step 2: Downloading files...")
    
    try:
        downloader = GoogleDriveDownloader(config.downloader)
        download_results = downloader.download_search_results(search_results)
        
        successful_downloads = [r for r in download_results if r[1] is not None]
        print(f"✅ Successfully downloaded {len(successful_downloads)} files")
        
    except Exception as e:
        print(f"❌ Error during download: {e}")
        return
    
    # Step 3: Convert to markdown
    print("\n🔄 Step 3: Converting to markdown...")
    
    converter = FileConverter(
        input_dir=config.downloader.output_dir,
        output_dir=markdown_dir
    )
    
    converted_files = converter.convert_all_files()
    print(f"✅ Converted {len(converted_files)} files to markdown")
    
    # Step 4: Create summary report
    print("\n📝 Step 4: Creating summary report...")
    
    summary_file = base_dir / "search_summary.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# Google Drive Search Results\n\n")
        f.write(f"**Search Pattern:** `{pattern}`\n")
        f.write(f"**Search Scope:** {drive_scope}\n")
        f.write(f"**Files Found:** {len(search_results)}\n")
        f.write(f"**Files Downloaded:** {len(successful_downloads)}\n")
        f.write(f"**Files Converted:** {len(converted_files)}\n\n")
        
        f.write("## Files by Drive\n\n")
        
        # Group by drive
        drives = {}
        for result in search_results:
            drive = result.get('drive', 'Unknown')
            if drive not in drives:
                drives[drive] = []
            drives[drive].append(result)
        
        for drive, files in drives.items():
            f.write(f"### {drive} ({len(files)} files)\n\n")
            for file in files[:10]:  # First 10 files
                f.write(f"- [{file['name']}]({file.get('webViewLink', '#')})\n")
            if len(files) > 10:
                f.write(f"- ... and {len(files) - 10} more files\n")
            f.write("\n")
    
    print(f"✅ Summary saved to: {summary_file}")
    
    # Show final summary
    print("\n🎉 Search and Download Complete!")
    print(f"📁 All outputs saved to: {base_dir}/")
    print("\n📊 Summary:")
    print(f"   • Files found: {len(search_results)}")
    print(f"   • Files downloaded: {len(successful_downloads)}")
    print(f"   • Files converted: {len(converted_files)}")
    print(f"   • Drives searched: {len(drives)}")


if __name__ == "__main__":
    main()