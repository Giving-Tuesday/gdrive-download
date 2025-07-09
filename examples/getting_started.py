#!/usr/bin/env python3
"""
Getting Started Example: Basic Download and Conversion

This example demonstrates the simplest way to get started with gdrive-download:
1. Download documents from a Google Drive folder
2. Convert them to markdown
3. Organize files using the standard directory structure

Usage:
    python getting_started.py <folder_url> [project_name]

Examples:
    python getting_started.py "https://drive.google.com/drive/folders/1ABC..." my_documents
    python getting_started.py "https://drive.google.com/drive/folders/1ABC..."
"""

import sys
from pathlib import Path
from rich.console import Console

# Add the src directory to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gdrive_download.config import GlobalConfig
from gdrive_download.downloader import GoogleDriveDownloader, FileConverter, FileRelationshipTracker

console = Console()

def main():
    """Simple download and conversion workflow."""
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python getting_started.py <folder_url> [project_name]")
        print("\\nExamples:")
        print("  python getting_started.py 'https://drive.google.com/drive/folders/1ABC...' my_docs")
        print("  python getting_started.py 'https://drive.google.com/drive/folders/1ABC...'")
        print("\\nFirst time setup:")
        print("  1. Get Google Drive API credentials from Google Cloud Console")
        print("  2. Save as 'credentials.json' in current directory")
        print("  3. Run this script")
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
        console.print("\\n[yellow]Setup required:[/yellow]")
        console.print("1. Go to Google Cloud Console")
        console.print("2. Create/select a project")
        console.print("3. Enable Google Drive API")
        console.print("4. Create credentials (OAuth 2.0)")
        console.print("5. Download and save as 'credentials.json'")
        return 1
    
    console.print(f"[bold blue]🚀 Getting Started with gdrive-download[/bold blue]")
    console.print(f"Folder: [cyan]{folder_url}[/cyan]")
    
    try:
        # Get project name from folder if not provided
        if not project_name:
            downloader = GoogleDriveDownloader(config.downloader)
            folder_id = downloader.extract_folder_id(folder_url)
            
            try:
                folder_info = downloader.service.files().get(
                    fileId=folder_id,
                    fields="id,name,mimeType",
                    supportsAllDrives=True
                ).execute()
                project_name = folder_info.get('name', 'gdrive_folder')
                console.print(f"[green]✓ Found folder: {folder_info.get('name', 'Unknown')}[/green]")
            except:
                project_name = f"gdrive_folder_{folder_id[:8]}"
        
        # Create project directory structure
        base_dir = Path(project_name.replace(' ', '_').replace('/', '_'))
        documents_dir = base_dir / "documents"
        markdown_dir = base_dir / "markdown"
        
        # Create directories
        for dir_path in [base_dir, documents_dir, markdown_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        config.downloader.output_dir = documents_dir
        
        console.print(f"\\n[bold blue]📁 Project: {project_name}[/bold blue]")
        console.print(f"Directory: [cyan]{base_dir}[/cyan]")
        
        # Step 1: Download files
        console.print(f"\\n[bold blue]📥 Step 1: Downloading files[/bold blue]")
        
        downloader = GoogleDriveDownloader(config.downloader)
        download_results = downloader.download_folder(folder_url)
        
        console.print(f"[green]✓ Downloaded {len(download_results)} files[/green]")
        
        # Step 2: Convert to markdown
        console.print(f"\\n[bold blue]🔄 Step 2: Converting to markdown[/bold blue]")
        
        converter = FileConverter(
            input_dir=documents_dir,
            output_dir=markdown_dir
        )
        
        converted_files = converter.convert_all_files()
        console.print(f"[green]✓ Converted {len(converted_files)} files[/green]")
        
        # Step 3: Track relationships
        console.print(f"\\n[bold blue]📊 Step 3: Creating file relationships[/bold blue]")
        
        # Get URL mappings for traceability
        url_mappings = downloader.extract_all_urls(folder_url)
        
        tracker = FileRelationshipTracker(
            downloads_dir=documents_dir,
            markdown_dir=markdown_dir
        )
        
        relationships = tracker.scan_file_relationships(url_mappings)
        csv_path = base_dir / "file_relationships.csv"
        tracker.save_relationships_csv(relationships, csv_path)
        
        console.print(f"[green]✓ Saved file relationships[/green]")
        
        # Create a simple README
        readme_path = base_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {project_name.replace('_', ' ').title()}\\n\\n")
            f.write(f"Downloaded from: {folder_url}\\n\\n")
            f.write("## Contents\\n\\n")
            f.write(f"- **{len(download_results)} files** downloaded to `documents/`\\n")
            f.write(f"- **{len(converted_files)} files** converted to `markdown/`\\n")
            f.write(f"- **File relationships** tracked in `file_relationships.csv`\\n\\n")
            f.write("## Next Steps\\n\\n")
            f.write("To analyze these documents:\\n\\n")
            f.write("```bash\\n")
            f.write("document-analyzer -i markdown -o analysis --template aar\\n")
            f.write("```\\n")
        
        # Success summary
        console.print(f"\\n[bold green]🎉 Success![/bold green]")
        console.print(f"[green]Created project structure:[/green]")
        console.print(f"  [cyan]{base_dir}/[/cyan]")
        console.print(f"  ├── [cyan]documents/[/cyan] ({len(download_results)} files)")
        console.print(f"  ├── [cyan]markdown/[/cyan] ({len(converted_files)} files)")
        console.print(f"  ├── [cyan]file_relationships.csv[/cyan]")
        console.print(f"  └── [cyan]README.md[/cyan]")
        
        console.print(f"\\n[bold cyan]What's next?[/bold cyan]")
        console.print(f"[cyan]cd {base_dir}[/cyan] - Enter your project directory")
        console.print(f"[cyan]ls -la[/cyan] - Explore the files")
        console.print(f"[cyan]cat README.md[/cyan] - Read the project overview")
        
        return 0
        
    except Exception as e:
        console.print(f"\\n[red]❌ Error: {e}[/red]")
        console.print("\\n[yellow]Troubleshooting:[/yellow]")
        console.print("• Check that the folder URL is correct")
        console.print("• Verify you have access to the folder")
        console.print("• Ensure credentials.json is valid")
        console.print("• Try running again (tokens may need refresh)")
        return 1

if __name__ == "__main__":
    sys.exit(main())