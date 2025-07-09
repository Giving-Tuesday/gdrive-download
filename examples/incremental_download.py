#!/usr/bin/env python3
"""
Incremental Download Example: Smart Updates for Existing Projects

This script demonstrates how to efficiently update an existing project by:
1. Checking what files already exist as markdown
2. Only downloading and converting new/changed files
3. Maintaining the standard directory structure

Usage:
    python incremental_download.py <folder_url> [project_name]

Examples:
    python incremental_download.py "https://drive.google.com/drive/folders/1ABC..." my_project
    python incremental_download.py "https://drive.google.com/drive/folders/1ABC..."
"""

import sys
from pathlib import Path
from typing import Set
from rich.console import Console

# Add the src directory to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gdrive_download.config import GlobalConfig
from gdrive_download.downloader import GoogleDriveDownloader, FileConverter

console = Console()

def get_existing_markdown_files(markdown_dir: Path) -> Set[str]:
    """Get set of existing markdown filenames (without .md extension)."""
    if not markdown_dir.exists():
        return set()
    
    existing = set()
    for md_file in markdown_dir.glob("*.md"):
        existing.add(md_file.stem)
    
    return existing

def get_base_name_for_file(file_path: Path) -> str:
    """Get the base name that would be used for the markdown file."""
    return file_path.stem

def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python incremental_download.py <folder_url> [project_name]")
        print("\\nExamples:")
        print("  python incremental_download.py 'https://drive.google.com/drive/folders/1ABC...' my_project")
        print("  python incremental_download.py 'https://drive.google.com/drive/folders/1ABC...'")
        return 1
    
    folder_url = sys.argv[1]
    project_name = sys.argv[2] if len(sys.argv) > 2 else ""
    
    # Configuration
    config = GlobalConfig()
    config.downloader.credentials_file = Path("credentials.json")
    config.downloader.token_file = Path("token.pickle")
    
    # Check credentials
    if not config.downloader.credentials_file.exists():
        console.print(f"[red]❌ Credentials file not found: {config.downloader.credentials_file}[/red]")
        console.print("Please download your Google Drive API credentials and save as credentials.json")
        return 1
    
    # Get project name from folder if not provided
    if not project_name:
        try:
            downloader = GoogleDriveDownloader(config.downloader)
            folder_id = downloader.extract_folder_id(folder_url)
            folder_info = downloader.service.files().get(
                fileId=folder_id,
                fields="id,name,mimeType",
                supportsAllDrives=True
            ).execute()
            project_name = folder_info.get('name', 'gdrive_folder')
        except:
            project_name = "gdrive_folder"
    
    # Standard directory structure
    base_dir = Path(project_name.replace(' ', '_').replace('/', '_'))
    documents_dir = base_dir / "documents"
    markdown_dir = base_dir / "markdown"
    
    # Update config
    config.downloader.output_dir = documents_dir
    
    # Create directories
    for dir_path in [base_dir, documents_dir, markdown_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold blue]📁 Incremental Download for Project: {project_name}[/bold blue]")
    console.print(f"Base directory: [cyan]{base_dir}[/cyan]")
    
    # Get existing markdown files
    console.print(f"\\n[blue]📋 Checking existing markdown files[/blue]")
    existing_markdown = get_existing_markdown_files(markdown_dir)
    console.print(f"[green]Found {len(existing_markdown)} existing markdown files[/green]")
    
    # Get list of files in Google Drive
    console.print(f"\\n[blue]🔍 Scanning Google Drive folder[/blue]")
    
    try:
        downloader = GoogleDriveDownloader(config.downloader)
        folder_id = downloader.extract_folder_id(folder_url)
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
            
            # Check if markdown version already exists
            base_name = get_base_name_for_file(Path(safe_filename))
            
            if base_name in existing_markdown:
                files_skipped.append((file_info, safe_filename, base_name))
            else:
                files_to_process.append((file_info, safe_filename, base_name))
        
        # Report what will be done
        console.print(f"\\n[yellow]📊 Processing Summary:[/yellow]")
        console.print(f"  • Files to download and convert: {len(files_to_process)}")
        console.print(f"  • Files already converted (skipping): {len(files_skipped)}")
        
        if files_skipped:
            console.print(f"\\n[dim]Files being skipped (markdown already exists):[/dim]")
            for file_info, safe_filename, base_name in files_skipped[:5]:  # Show first 5
                console.print(f"  • {file_info['name']} -> {base_name}.md")
            if len(files_skipped) > 5:
                console.print(f"  • ... and {len(files_skipped) - 5} more")
        
        if not files_to_process:
            console.print(f"\\n[green]✅ All files already converted! Nothing to do.[/green]")
            return 0
        
        console.print(f"\\n[blue]📥 Processing new files[/blue]")
        
        # Setup file converter
        converter = FileConverter(
            input_dir=documents_dir,
            output_dir=markdown_dir
        )
        
        # Process each file that needs it
        success_count = 0
        error_count = 0
        
        for i, (file_info, safe_filename, base_name) in enumerate(files_to_process, 1):
            console.print(f"\\n[cyan]📄 [{i}/{len(files_to_process)}] Processing: {file_info['name']}[/cyan]")
            
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
        console.print(f"\\n[bold green]🎉 Incremental update complete![/bold green]")
        console.print(f"[green]📊 Results:[/green]")
        console.print(f"  • Successfully processed: {success_count}")
        console.print(f"  • Errors: {error_count}")
        console.print(f"  • Skipped (already existed): {len(files_skipped)}")
        console.print(f"  • Total files in folder: {len(downloadable_files)}")
        
        console.print(f"\\n[cyan]📁 Project structure:[/cyan]")
        console.print(f"  {base_dir}/")
        console.print(f"  ├── documents/ ({len(downloadable_files)} files)")
        console.print(f"  └── markdown/ ({len(existing_markdown) + success_count} files)")
        
        return 0 if error_count == 0 else 1
            
    except Exception as e:
        console.print(f"\\n[red]❌ Unexpected error: {e}[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())