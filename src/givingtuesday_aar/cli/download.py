"""CLI for downloading and converting AAR documents."""

import click
from pathlib import Path
from rich.console import Console

from ..config import get_config, DownloaderConfig
from ..downloader import GoogleDriveDownloader, FileConverter, FileRelationshipTracker
from ..utils import setup_logging


@click.command()
@click.option('--folder-url', '-u', required=True, help='Google Drive folder URL to download from')
@click.option('--output-dir', '-o', default='downloads', help='Output directory for downloaded files')
@click.option('--markdown-dir', '-m', default='markdown', help='Output directory for converted markdown files')
@click.option('--credentials', '-c', help='Path to Google API credentials file')
@click.option('--convert/--no-convert', default=True, help='Convert downloaded files to markdown')
@click.option('--track-relationships/--no-track', default=True, help='Track file relationships')
@click.option('--config-file', help='Path to configuration file')
@click.option('--log-level', default='INFO', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
def main(folder_url, output_dir, markdown_dir, credentials, convert, track_relationships, config_file, log_level):
    """Download AAR documents from Google Drive and convert to markdown."""
    
    # Setup logging
    logger = setup_logging(level=log_level)
    console = Console()
    
    try:
        # Load configuration
        config = get_config(Path(config_file) if config_file else None)
        
        # Override with CLI arguments
        config.downloader.output_dir = Path(output_dir)
        if credentials:
            config.downloader.credentials_file = Path(credentials)
        
        # Initialize downloader
        downloader = GoogleDriveDownloader(config.downloader)
        
        console.print(f"[blue]Downloading from: {folder_url}[/blue]")
        console.print(f"[blue]Output directory: {output_dir}[/blue]")
        
        # Download files
        results = downloader.download_folder(folder_url)
        
        console.print(f"[green]Downloaded {len(results)} files[/green]")
        
        # Convert to markdown if requested
        converted_files = []
        if convert:
            console.print(f"[blue]Converting files to markdown...[/blue]")
            
            converter = FileConverter(
                input_dir=config.downloader.output_dir,
                output_dir=Path(markdown_dir)
            )
            
            converted_files = converter.convert_all_files()
            console.print(f"[green]Converted {len(converted_files)} files to markdown[/green]")
        
        # Track relationships if requested
        if track_relationships:
            console.print(f"[blue]Tracking file relationships...[/blue]")
            
            # Extract URL mappings
            url_mappings = downloader.extract_all_urls(folder_url)
            
            tracker = FileRelationshipTracker(
                downloads_dir=config.downloader.output_dir,
                markdown_dir=Path(markdown_dir)
            )
            
            relationships = tracker.scan_file_relationships(url_mappings)
            
            # Save relationships
            csv_path = Path('file_relationships.csv')
            tracker.save_relationships_csv(relationships, csv_path)
            
            # Generate report
            report = tracker.generate_report(relationships)
            console.print(f"[green]File relationship tracking complete[/green]")
            console.print(report)
        
        console.print(f"[bold green]Download and conversion complete![/bold green]")
        
    except Exception as e:
        logger.error(f"Error during download: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


if __name__ == '__main__':
    main()