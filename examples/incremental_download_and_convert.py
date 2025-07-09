#!/usr/bin/env python3
"""
Incremental Download and Convert Script

This script downloads files from a Google Drive folder and converts them to markdown,
but only if the markdown file doesn't already exist. This allows for efficient
incremental updates without re-processing existing files.

Usage:
    python incremental_download_and_convert.py <folder_url> [--output-dir DIR] [--docs-dir DIR]

Examples:
    # Basic usage with default directories
    python incremental_download_and_convert.py "https://drive.google.com/drive/folders/1ABC..."
    
    # Custom output directories
    python incremental_download_and_convert.py "https://drive.google.com/drive/folders/1ABC..." \
        --output-dir ./downloads --docs-dir ./markdown_docs
"""

import argparse
import sys
from pathlib import Path
from typing import Set

from gdrive_download.config import DownloaderConfig
from gdrive_download.downloader.drive_downloader import GoogleDriveDownloader
from gdrive_download.downloader.file_converter import FileConverter
from rich.console import Console


def get_existing_markdown_files(docs_dir: Path) -> Set[str]:
    """Get set of existing markdown filenames (without .md extension)."""
    if not docs_dir.exists():
        return set()
    
    existing = set()
    for md_file in docs_dir.glob("*.md"):
        # Remove .md extension to get base name
        base_name = md_file.stem
        existing.add(base_name)
    
    return existing


def get_base_name_for_file(file_path: Path) -> str:
    """Get the base name that would be used for the markdown file."""
    # Remove file extension to get base name
    if file_path.suffix.lower() in ['.docx', '.doc']:
        return file_path.stem
    else:
        # For other file types, use full name without extension
        return file_path.stem


def main():
    parser = argparse.ArgumentParser(
        description="Incrementally download and convert Google Drive files to markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "folder_url",
        help="Google Drive folder URL to download from"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./downloads"),
        help="Directory to download files to (default: ./downloads)"
    )
    
    parser.add_argument(
        "--docs-dir", 
        type=Path,
        default=Path("./markdown_docs"),
        help="Directory containing markdown files (default: ./markdown_docs)"
    )
    
    parser.add_argument(
        "--credentials",
        type=Path,
        default=Path("./credentials.json"),
        help="Path to Google Drive credentials file (default: ./credentials.json)"
    )
    
    parser.add_argument(
        "--token",
        type=Path,
        default=Path("./token.pickle"),
        help="Path to store authentication tokens (default: ./token.pickle)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded/converted without actually doing it"
    )
    
    args = parser.parse_args()
    
    console = Console()
    
    # Validate inputs
    if not args.credentials.exists():
        console.print(f"[red]❌ Credentials file not found: {args.credentials}[/red]")
        console.print("Please download your Google Drive API credentials and save as credentials.json")
        return 1
    
    # Create output directories
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.docs_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Get existing markdown files
        console.print(f"[blue]📁 Checking existing markdown files in {args.docs_dir}[/blue]")
        existing_markdown = get_existing_markdown_files(args.docs_dir)
        console.print(f"[green]Found {len(existing_markdown)} existing markdown files[/green]")
        
        # Setup downloader
        downloader_config = DownloaderConfig(
            output_dir=args.output_dir,
            credentials_file=args.credentials,
            token_file=args.token
        )
        
        downloader = GoogleDriveDownloader(downloader_config)
        
        # Get list of files that would be downloaded
        console.print(f"[blue]🔍 Scanning Google Drive folder...[/blue]")
        folder_id = downloader.extract_folder_id(args.folder_url)
        files = downloader.list_files_in_folder(folder_id)
        
        # Filter downloadable files (exclude folders)
        downloadable_files = [
            f for f in files 
            if f['mimeType'] != 'application/vnd.google-apps.folder'
        ]
        
        console.print(f"[green]Found {len(downloadable_files)} files in Google Drive[/green]")
        
        # Determine which files need to be processed
        files_to_process = []
        files_skipped = []
        
        for file_info in downloadable_files:
            # Get the filename that would be used locally
            safe_filename = downloader._sanitize_filename(file_info['name'])
            
            # Add appropriate extension for Google Workspace files
            if file_info['mimeType'] == 'application/vnd.google-apps.document':
                if not safe_filename.endswith('.docx'):
                    safe_filename += '.docx'
            elif file_info['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                if not safe_filename.endswith('.xlsx'):
                    safe_filename += '.xlsx'
            elif file_info['mimeType'] == 'application/vnd.google-apps.presentation':
                if not safe_filename.endswith('.pptx'):
                    safe_filename += '.pptx'
            
            # Check if markdown version already exists
            base_name = get_base_name_for_file(Path(safe_filename))
            
            if base_name in existing_markdown:
                files_skipped.append((file_info, safe_filename, base_name))
            else:
                files_to_process.append((file_info, safe_filename, base_name))
        
        # Report what will be done
        console.print(f"\n[yellow]📊 Processing Summary:[/yellow]")
        console.print(f"  • Files to download and convert: {len(files_to_process)}")
        console.print(f"  • Files already converted (skipping): {len(files_skipped)}")
        
        if files_skipped:
            console.print(f"\n[dim]Files being skipped (markdown already exists):[/dim]")
            for file_info, safe_filename, base_name in files_skipped[:10]:  # Show first 10
                console.print(f"  • {file_info['name']} -> {base_name}.md")
            if len(files_skipped) > 10:
                console.print(f"  • ... and {len(files_skipped) - 10} more")
        
        if not files_to_process:
            console.print(f"\n[green]✅ All files already converted! Nothing to do.[/green]")
            return 0
        
        if args.dry_run:
            console.print(f"\n[yellow]🔍 DRY RUN - Files that would be processed:[/yellow]")
            for file_info, safe_filename, base_name in files_to_process:
                console.print(f"  • {file_info['name']} -> {safe_filename} -> {base_name}.md")
            return 0
        
        console.print(f"\n[blue]⬇️ Starting download and conversion...[/blue]")
        
        # Setup file converter for markdown conversion
        converter = FileConverter(
            input_dir=args.output_dir,
            output_dir=args.docs_dir
        )
        
        # Process each file that needs it
        success_count = 0
        error_count = 0
        
        for i, (file_info, safe_filename, base_name) in enumerate(files_to_process, 1):
            console.print(f"\n[cyan]📄 [{i}/{len(files_to_process)}] Processing: {file_info['name']}[/cyan]")
            
            try:
                # Download the file
                downloaded_path = downloader.download_file(
                    file_info['id'],
                    file_info['name'], 
                    file_info['mimeType']
                )
                
                if downloaded_path and downloaded_path.exists():
                    # Convert to markdown if it's a document
                    if downloaded_path.suffix.lower() in ['.docx', '.doc']:
                        converted_path = converter.convert_file(downloaded_path)
                        if converted_path:
                            console.print(f"[green]✅ Converted to: {converted_path.name}[/green]")
                        else:
                            console.print(f"[red]❌ Failed to convert: {safe_filename}[/red]")
                            error_count += 1
                            continue
                    else:
                        console.print(f"[yellow]⚠️ Downloaded but not converted (unsupported format): {safe_filename}[/yellow]")
                    
                    success_count += 1
                else:
                    console.print(f"[red]❌ Failed to download: {file_info['name']}[/red]")
                    error_count += 1
                    
            except Exception as e:
                console.print(f"[red]❌ Error processing {file_info['name']}: {e}[/red]")
                error_count += 1
        
        # Final summary
        console.print(f"\n[yellow]📊 Final Results:[/yellow]")
        console.print(f"  • Successfully processed: {success_count}")
        console.print(f"  • Errors: {error_count}")
        console.print(f"  • Skipped (already existed): {len(files_skipped)}")
        console.print(f"  • Total files in folder: {len(downloadable_files)}")
        
        if error_count == 0:
            console.print(f"\n[green]🎉 All files processed successfully![/green]")
            return 0
        else:
            console.print(f"\n[yellow]⚠️ Completed with {error_count} errors[/yellow]")
            return 1
            
    except KeyboardInterrupt:
        console.print(f"\n[yellow]⏹️ Interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return 1


if __name__ == "__main__":
    sys.exit(main())