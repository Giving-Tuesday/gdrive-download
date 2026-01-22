"""CLI command for uploading markdown files to Google Drive as native Google Docs."""

from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from gdrive_download.config import GlobalConfig
from gdrive_download.downloader import GoogleDriveUploader

console = Console()


def collect_markdown_files(
    files: tuple,
    directory: Optional[Path],
    pattern: str
) -> List[Path]:
    """Collect markdown files from file arguments and/or directory.

    Args:
        files: Tuple of file paths from --file options
        directory: Directory path from --directory option
        pattern: Glob pattern for directory search

    Returns:
        List of unique Path objects
    """
    markdown_files = []
    seen = set()

    # Add explicitly specified files
    for file_path in files:
        path = Path(file_path)
        if path.exists() and path.suffix.lower() == '.md':
            if path not in seen:
                markdown_files.append(path)
                seen.add(path)
        elif path.exists():
            console.print(f"[yellow]Warning: Skipping non-markdown file: {path}[/yellow]")
        else:
            console.print(f"[yellow]Warning: File not found: {path}[/yellow]")

    # Add files from directory
    if directory:
        dir_path = Path(directory)
        if dir_path.is_dir():
            for path in dir_path.glob(pattern):
                # Only include markdown files
                if path.is_file() and path.suffix.lower() == '.md' and path not in seen:
                    markdown_files.append(path)
                    seen.add(path)
        else:
            console.print(f"[yellow]Warning: Directory not found: {dir_path}[/yellow]")

    return sorted(markdown_files, key=lambda p: p.name.lower())


def display_preview_table(files: List[Path], folder_name: str):
    """Display a preview table of files to upload.

    Args:
        files: List of markdown file paths
        folder_name: Name of target folder
    """
    table = Table(title=f"Files to upload to '{folder_name}'")
    table.add_column("#", style="dim", width=4)
    table.add_column("File", style="cyan", no_wrap=False)
    table.add_column("Size", style="green", justify="right")

    for i, path in enumerate(files, 1):
        size = path.stat().st_size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / 1024 / 1024:.2f} MB"

        table.add_row(str(i), str(path), size_str)

    console.print(table)
    console.print(f"\n[bold]Total: {len(files)} files[/bold]")


def display_results_table(results: List[dict]):
    """Display a results table after upload.

    Args:
        results: List of upload result dicts
    """
    table = Table(title="Upload Results")
    table.add_column("Status", style="bold", width=8)
    table.add_column("Document", style="cyan", no_wrap=False)
    table.add_column("Link", style="blue", no_wrap=False)

    for result in results:
        status = result['status']
        if status == 'created':
            status_str = "[green]Created[/green]"
        elif status == 'skipped':
            status_str = "[yellow]Skipped[/yellow]"
        else:
            status_str = "[red]Error[/red]"

        link = ""
        if result.get('webViewLink'):
            # Make the link clickable in Rich terminal
            link = f"[link={result['webViewLink']}]Open[/link]"

        table.add_row(status_str, result['name'], link)

    console.print(table)

    # Summary
    created = len([r for r in results if r['status'] == 'created'])
    skipped = len([r for r in results if r['status'] == 'skipped'])
    errors = len([r for r in results if r['status'] == 'error'])

    console.print(f"\n[bold]Summary:[/bold] {created} created, {skipped} skipped, {errors} errors")


@click.command()
@click.option('-f', '--file', 'files', multiple=True, type=click.Path(),
              help='Markdown file(s) to upload (can be specified multiple times)')
@click.option('-d', '--directory', type=click.Path(exists=True),
              help='Directory containing markdown files')
@click.option('-t', '--folder-id', 'folder_id',
              help='Target Google Drive folder ID')
@click.option('--folder-url', 'folder_url',
              help='Target Google Drive folder URL (alternative to --folder-id)')
@click.option('-c', '--credentials', type=click.Path(exists=True),
              default='credentials.json',
              help='Google API credentials file (default: credentials.json)')
@click.option('-p', '--pattern', default='*.md',
              help='Glob pattern for directory search (default: *.md)')
@click.option('--preview/--no-preview', default=True,
              help='Preview files before upload (default: preview)')
@click.option('--skip-existing/--replace-existing', 'skip_existing', default=True,
              help='Skip documents that already exist (default: skip)')
def upload(
    files: tuple,
    directory: Optional[str],
    folder_id: Optional[str],
    folder_url: Optional[str],
    credentials: str,
    pattern: str,
    preview: bool,
    skip_existing: bool
):
    """Upload markdown files to Google Drive as native Google Docs.

    Converts markdown files to HTML and uploads them as Google Docs,
    preserving formatting like headers, bold, lists, and links.

    Examples:

    \b
    # Upload a single file
    gdrive-upload -f report.md --folder-id 1ABC123

    \b
    # Upload multiple files
    gdrive-upload -f doc1.md -f doc2.md --folder-id 1ABC123

    \b
    # Upload all markdown files from a directory
    gdrive-upload -d markdown/ --folder-id 1ABC123

    \b
    # Upload using folder URL instead of ID
    gdrive-upload -f doc.md --folder-url "https://drive.google.com/drive/folders/1ABC123"

    \b
    # Upload without preview prompt
    gdrive-upload -f doc.md --folder-id 1ABC123 --no-preview

    \b
    # Replace existing documents instead of skipping
    gdrive-upload -f doc.md --folder-id 1ABC123 --replace-existing
    """
    # Validate folder specification
    if not folder_id and not folder_url:
        raise click.UsageError("Either --folder-id or --folder-url is required")

    if folder_id and folder_url:
        raise click.UsageError("Specify either --folder-id or --folder-url, not both")

    # Validate file specification
    if not files and not directory:
        raise click.UsageError("Either --file or --directory is required")

    # Setup configuration
    config = GlobalConfig()
    credentials_path = Path(credentials)
    config.downloader.credentials_file = credentials_path
    config.downloader.token_file = credentials_path.parent / "token.pickle"

    console.print(f"[bold blue]Preparing to upload markdown files to Google Drive[/bold blue]")

    # Initialize uploader
    try:
        uploader = GoogleDriveUploader(config.downloader)
    except ImportError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()

    # Extract folder ID from URL if provided
    target_folder_id = folder_id
    if folder_url:
        try:
            target_folder_id = uploader.extract_folder_id(folder_url)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise click.Abort()

    # Verify folder access
    console.print(f"[blue]Verifying folder access...[/blue]")
    try:
        folder_info = uploader.verify_folder_access(target_folder_id)
        console.print(f"[green]Target folder: {folder_info['name']}[/green]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()

    # Collect markdown files
    dir_path = Path(directory) if directory else None
    markdown_files = collect_markdown_files(files, dir_path, pattern)

    if not markdown_files:
        console.print("[yellow]No markdown files found to upload.[/yellow]")
        return

    # Preview and confirm
    if preview:
        display_preview_table(markdown_files, folder_info['name'])

        if not Confirm.ask("\nProceed with upload?"):
            console.print("[yellow]Upload cancelled.[/yellow]")
            return

    # Upload files
    console.print(f"\n[bold blue]Uploading files...[/bold blue]")

    results = uploader.upload_multiple(
        markdown_files,
        target_folder_id,
        skip_existing=skip_existing
    )

    # Display results
    console.print()
    display_results_table(results)

    # Print clickable links for created documents
    created_docs = [r for r in results if r['status'] == 'created' and r.get('webViewLink')]
    if created_docs:
        console.print(f"\n[bold green]Created documents:[/bold green]")
        for doc in created_docs:
            console.print(f"  - {doc['webViewLink']}")

    console.print(f"\n[bold green]Upload complete![/bold green]")


if __name__ == '__main__':
    upload()
