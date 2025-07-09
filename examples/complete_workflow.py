#!/usr/bin/env python3
"""
Complete Workflow Example: Download, Convert, and Analyze Documents

This script demonstrates the complete workflow from Google Drive to analysis:
1. Download documents from Google Drive (folder or search)
2. Convert documents to markdown
3. Track file relationships
4. Prepare for analysis with document_analyzer

Usage:
    python complete_workflow.py folder <folder_url> [project_name]
    python complete_workflow.py search <pattern> [project_name]

Examples:
    python complete_workflow.py folder "https://drive.google.com/drive/folders/1ABC..." my_project
    python complete_workflow.py search "AAR*" aar_analysis
"""

import sys
from pathlib import Path
from rich.console import Console
import json

# Add the src directory to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gdrive_download.config import GlobalConfig
from gdrive_download.downloader import GoogleDriveSearcher, GoogleDriveDownloader, FileConverter, FileRelationshipTracker

console = Console()

def download_from_folder(folder_url: str, project_name: str, config: GlobalConfig):
    """Download documents from a specific Google Drive folder."""
    
    console.print(f"[bold blue]📁 Downloading from folder[/bold blue]")
    console.print(f"URL: [cyan]{folder_url}[/cyan]")
    
    try:
        downloader = GoogleDriveDownloader(config.downloader)
        folder_id = downloader.extract_folder_id(folder_url)
        
        # Get folder info if project name not provided
        if not project_name:
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
        
        # Download all files
        download_results = downloader.download_folder(folder_url)
        url_mappings = downloader.extract_all_urls(folder_url)
        
        return download_results, url_mappings, project_name
        
    except Exception as e:
        console.print(f"[red]Error downloading from folder: {e}[/red]")
        return None, None, project_name

def search_and_download(pattern: str, project_name: str, config: GlobalConfig):
    """Search for documents matching a pattern and download them."""
    
    console.print(f"[bold blue]🔍 Searching for documents[/bold blue]")
    console.print(f"Pattern: [cyan]{pattern}[/cyan]")
    
    try:
        searcher = GoogleDriveSearcher(config.downloader)
        search_results = searcher.search_files(
            pattern=pattern,
            drive_scope="all",
            file_types=['document'],
            max_results=100
        )
        
        console.print(f"[green]✓ Found {len(search_results)} matching files[/green]")
        
        if not search_results:
            console.print("[yellow]No files found matching pattern[/yellow]")
            return None, None, project_name
        
        if not project_name:
            project_name = f"search_{pattern.replace('*', 'star').replace('?', 'q')}"
        
        # Download files
        downloader = GoogleDriveDownloader(config.downloader)
        download_results = downloader.download_search_results(search_results)
        
        # Create URL mappings from search results
        url_mappings = [
            {"name": result["name"], "url": result.get("webViewLink", "")}
            for result in search_results
        ]
        
        return download_results, url_mappings, project_name
        
    except Exception as e:
        console.print(f"[red]Error searching/downloading: {e}[/red]")
        return None, None, project_name

def main():
    """Complete workflow: download, convert, and prepare for analysis."""
    
    # Parse command line arguments
    if len(sys.argv) < 3:
        print("Usage: python complete_workflow.py <mode> <target> [project_name]")
        print("\\nModes:")
        print("  folder <folder_url>    Download from specific Google Drive folder")
        print("  search <pattern>       Search for files matching pattern")
        print("\\nExamples:")
        print("  python complete_workflow.py folder 'https://drive.google.com/drive/folders/1ABC...' my_project")
        print("  python complete_workflow.py search 'AAR*' aar_analysis")
        return 1
    
    mode = sys.argv[1]
    target = sys.argv[2]
    project_name = sys.argv[3] if len(sys.argv) > 3 else ""
    
    if mode not in ['folder', 'search']:
        console.print(f"[red]Error: Invalid mode '{mode}'. Use 'folder' or 'search'[/red]")
        return 1
    
    # Configuration
    config = GlobalConfig()
    config.downloader.credentials_file = Path("credentials.json")
    config.downloader.token_file = Path("token.pickle")
    
    # Check credentials
    if not config.downloader.credentials_file.exists():
        console.print(f"[red]❌ Credentials file not found: {config.downloader.credentials_file}[/red]")
        console.print("Please download your Google Drive API credentials and save as credentials.json")
        return 1
    
    console.print(f"[bold blue]🚀 Starting Complete Workflow[/bold blue]")
    console.print(f"Mode: [cyan]{mode}[/cyan]")
    console.print(f"Target: [cyan]{target}[/cyan]")
    
    # Project setup
    base_dir = Path(project_name.replace(' ', '_').replace('/', '_')) if project_name else Path("temp_project")
    
    # Standard directory structure
    documents_dir = base_dir / "documents"
    markdown_dir = base_dir / "markdown"
    analysis_dir = base_dir / "analysis"
    
    # Update config
    config.downloader.output_dir = documents_dir
    
    # Step 1: Download documents
    console.print(f"\\n[bold blue]📥 Step 1: Downloading documents[/bold blue]")
    
    if mode == 'folder':
        download_results, url_mappings, project_name = download_from_folder(target, project_name, config)
    else:  # search
        download_results, url_mappings, project_name = search_and_download(target, project_name, config)
    
    if not download_results:
        console.print("[red]Download failed or no files found[/red]")
        return 1
    
    # Update base_dir with final project name
    base_dir = Path(project_name.replace(' ', '_').replace('/', '_'))
    documents_dir = base_dir / "documents"
    markdown_dir = base_dir / "markdown"
    analysis_dir = base_dir / "analysis"
    
    # Create directories
    for dir_path in [base_dir, documents_dir, markdown_dir, analysis_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold blue]📁 Setting up project[/bold blue]")
    console.print(f"Project: [cyan]{project_name}[/cyan]")
    console.print(f"Base directory: [cyan]{base_dir}[/cyan]")
    
    successful_downloads = [r for r in download_results if r[1] is not None]
    console.print(f"[green]✓ Downloaded {len(successful_downloads)} files[/green]")
    
    # Step 2: Convert to markdown
    console.print(f"\\n[bold blue]🔄 Step 2: Converting to markdown[/bold blue]")
    
    converter = FileConverter(
        input_dir=documents_dir,
        output_dir=markdown_dir
    )
    
    converted_files = converter.convert_all_files()
    console.print(f"[green]✓ Converted {len(converted_files)} files[/green]")
    
    # Step 3: Track relationships
    console.print(f"\\n[bold blue]📊 Step 3: Tracking file relationships[/bold blue]")
    
    tracker = FileRelationshipTracker(
        downloads_dir=documents_dir,
        markdown_dir=markdown_dir
    )
    
    relationships = tracker.scan_file_relationships(url_mappings)
    
    # Save relationships
    csv_path = base_dir / "file_relationships.csv"
    tracker.save_relationships_csv(relationships, csv_path)
    
    # Step 4: Prepare for analysis
    console.print(f"\\n[bold blue]🔬 Step 4: Preparing for analysis[/bold blue]")
    
    # Create analysis configuration
    analysis_config = {
        "project_name": project_name,
        "markdown_dir": str(markdown_dir),
        "analysis_dir": str(analysis_dir),
        "template": "aar",
        "file_count": len(converted_files),
        "relationships_file": str(csv_path)
    }
    
    # Save analysis config
    config_file = base_dir / "analysis_config.json"
    with open(config_file, 'w') as f:
        json.dump(analysis_config, f, indent=2)
    
    # Create README for the project
    readme_file = base_dir / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(f"# {project_name.replace('_', ' ').title()}\\n\\n")
        f.write(f"This project contains {len(converted_files)} documents downloaded from Google Drive.\\n\\n")
        f.write("## Directory Structure\\n\\n")
        f.write("```\\n")
        f.write(f"{base_dir.name}/\\n")
        f.write("├── documents/              # Original downloaded files\\n")
        f.write("├── markdown/               # Converted markdown files\\n")
        f.write("├── analysis/               # Analysis results (to be generated)\\n")
        f.write("├── file_relationships.csv  # URL to file mappings\\n")
        f.write("├── analysis_config.json    # Analysis configuration\\n")
        f.write("└── README.md               # This file\\n")
        f.write("```\\n\\n")
        f.write("## Next Steps\\n\\n")
        f.write("To analyze the documents, run:\\n\\n")
        f.write("```bash\\n")
        f.write(f"document-analyzer -i {markdown_dir} -o {analysis_dir} --template aar\\n")
        f.write("```\\n\\n")
        f.write("## Files Overview\\n\\n")
        f.write(f"- **Mode:** {mode}\\n")
        f.write(f"- **Target:** {target}\\n")
        f.write(f"- **Files Downloaded:** {len(successful_downloads)}\\n")
        f.write(f"- **Files Converted:** {len(converted_files)}\\n")
    
    # Final summary
    console.print(f"\\n[bold green]🎉 Project setup complete![/bold green]")
    console.print(f"[green]📁 Project structure:[/green]")
    console.print(f"  [cyan]{base_dir}/[/cyan]")
    console.print(f"  ├── [cyan]documents/[/cyan] ({len(successful_downloads)} files)")
    console.print(f"  ├── [cyan]markdown/[/cyan] ({len(converted_files)} files)")
    console.print(f"  ├── [cyan]analysis/[/cyan] (ready for analysis)")
    console.print(f"  ├── [cyan]file_relationships.csv[/cyan]")
    console.print(f"  ├── [cyan]analysis_config.json[/cyan]")
    console.print(f"  └── [cyan]README.md[/cyan]")
    
    console.print(f"\\n[bold cyan]Next step:[/bold cyan]")
    console.print(f"[cyan]cd {base_dir} && document-analyzer -i markdown -o analysis --template aar[/cyan]")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())