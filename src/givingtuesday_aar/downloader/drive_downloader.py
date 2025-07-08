"""Google Drive downloading functionality."""
# MATURE CODE.  DO NOT TOUCH THIS FILE WITHOUT SPECIFIC INSTRUCTION

import io
import os
import pickle
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ..config import DownloaderConfig


class GoogleDriveDownloader:
    """Downloads files from Google Drive with support for shared folders."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, config: DownloaderConfig):
        self.config = config
        self.console = Console()
        self.service = None
        self._setup_service()
    
    def _setup_service(self):
        """Initialize Google Drive API service."""
        creds = None
        
        if self.config.token_file and self.config.token_file.exists():
            with open(self.config.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.config.credentials_file or not self.config.credentials_file.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.config.credentials_file}"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            if self.config.token_file:
                self.config.token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config.token_file, 'wb') as token:
                    pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage."""
        # Replace problematic characters with safe alternatives
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Handle forward slashes specifically (common in document titles)
        sanitized = sanitized.replace('/', '_')
        
        # Remove or replace other problematic characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)  # Control characters
        
        # Trim whitespace and dots from ends (Windows doesn't like trailing dots)
        sanitized = sanitized.strip(' .')
        
        # Ensure filename isn't empty after sanitization
        if not sanitized:
            sanitized = 'unnamed_file'
        
        # Limit length to reasonable size (most filesystems support 255 chars)
        if len(sanitized) > 200:
            name_part, ext_part = os.path.splitext(sanitized)
            sanitized = name_part[:200-len(ext_part)] + ext_part
        
        return sanitized
    
    def _follow_shortcut(self, shortcut_id: str, shortcut_name: str, recursion_depth: int = 0) -> Optional[Path]:
        """Follow a Google Drive shortcut to download the target file."""
        try:
            # Get shortcut metadata to find the target file
            shortcut_metadata = self.service.files().get(
                fileId=shortcut_id,
                fields="shortcutDetails",
                supportsAllDrives=True
            ).execute()
            
            target_id = shortcut_metadata.get('shortcutDetails', {}).get('targetId')
            if not target_id:
                self.console.print(f"[red]Could not resolve shortcut target for: {shortcut_name}[/red]")
                return None
            
            # Get target file metadata
            target_metadata = self.service.files().get(
                fileId=target_id,
                fields="name, mimeType",
                supportsAllDrives=True
            ).execute()
            
            target_name = target_metadata.get('name', shortcut_name)
            target_mime = target_metadata.get('mimeType')
            
            self.console.print(f"[blue]Following shortcut '{shortcut_name}' -> '{target_name}' ({target_mime})[/blue]")
            
            # Download the target file with incremented recursion depth
            return self.download_file(target_id, target_name, target_mime, recursion_depth + 1)
            
        except Exception as e:
            self.console.print(f"[red]Error following shortcut {shortcut_name}: {e}[/red]")
            return None
    
    def extract_folder_id(self, folder_url: str) -> str:
        """Extract folder ID from Google Drive URL."""
        # Handle various folder URL formats
        if '/folders/' in folder_url:
            # Extract folder ID from /folders/ or /u/0/folders/ URLs
            folder_part = folder_url.split('/folders/')[1]
            return folder_part.split('?')[0].split('/')[0]
        
        parsed = urlparse(folder_url)
        if 'id' in parse_qs(parsed.query):
            return parse_qs(parsed.query)['id'][0]
        
        raise ValueError(f"Cannot extract folder ID from URL: {folder_url}")
    
    def list_files_in_folder(self, folder_id: str, recursive: bool = True) -> List[Dict]:
        """List all files in a Google Drive folder."""
        items = []
        page_token = None
        
        while True:
            try:
                # Try with Shared Drive support first
                query = f"'{folder_id}' in parents and trashed=false"
                self.console.print(f"[blue]🔍 API Call Debug:[/blue]")
                self.console.print(f"   Query: {query}")
                self.console.print(f"   Folder ID: {folder_id}")
                self.console.print(f"   Page token: {page_token}")
                self.console.print(f"   supportsAllDrives: True")
                self.console.print(f"   includeItemsFromAllDrives: True")
                
                results = self.service.files().list(
                    q=query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, parents, webViewLink, size, shortcutDetails)",
                    pageToken=page_token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                
                self.console.print(f"[blue]📨 API Response:[/blue]")
                self.console.print(f"   Raw response keys: {list(results.keys())}")
                
                files = results.get('files', [])
                self.console.print(f"   Files array length: {len(files)}")
                
                if files:
                    self.console.print(f"   Sample file: {files[0].get('name', 'NO NAME')} ({files[0].get('mimeType', 'NO TYPE')})")
                
                items.extend(files)
                page_token = results.get('nextPageToken')
                
                self.console.print(f"[green]Found {len(files)} items in this batch (total so far: {len(items)})[/green]")
                self.console.print(f"   Next page token: {page_token}")
                
                if not page_token:
                    break
            except Exception as e:
                self.console.print(f"[red]❌ DETAILED ERROR with Shared Drive support:[/red]")
                self.console.print(f"   Error type: {type(e).__name__}")
                self.console.print(f"   Error message: {str(e)}")
                import traceback
                self.console.print(f"   Traceback: {traceback.format_exc()}")
                # Fallback to regular Drive access
                self.console.print("[yellow]🔄 Trying fallback to regular Drive API...[/yellow]")
                try:
                    results = self.service.files().list(
                        q=f"'{folder_id}' in parents and trashed=false",
                        pageSize=100,
                        fields="nextPageToken, files(id, name, mimeType, parents, webViewLink, size, shortcutDetails)",
                        pageToken=page_token
                    ).execute()
                    
                    self.console.print(f"[blue]📨 Fallback API Response:[/blue]")
                    self.console.print(f"   Raw response keys: {list(results.keys())}")
                    
                    files = results.get('files', [])
                    self.console.print(f"   Files array length: {len(files)}")
                    
                    if files:
                        self.console.print(f"   Sample file: {files[0].get('name', 'NO NAME')} ({files[0].get('mimeType', 'NO TYPE')})")
                    
                    items.extend(files)
                    page_token = results.get('nextPageToken')
                    
                    self.console.print(f"[green]Found {len(files)} items in this batch (regular Drive, total: {len(items)})[/green]")
                    
                    if not page_token:
                        break
                except Exception as regular_error:
                    self.console.print(f"[red]❌ DETAILED FALLBACK ERROR:[/red]")
                    self.console.print(f"   Error type: {type(regular_error).__name__}")
                    self.console.print(f"   Error message: {str(regular_error)}")
                    import traceback
                    self.console.print(f"   Traceback: {traceback.format_exc()}")
                    break
        
        # Handle recursive listing
        if recursive:
            original_count = len(items)
            for file in items[:]:  # Copy list to avoid modification during iteration
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    subfolder_files = self.list_files_in_folder(file['id'], recursive=True)
                    items.extend(subfolder_files)
            self.console.print(f"[blue]Recursive scan: {len(items) - original_count} additional items from subfolders[/blue]")
        
        return items
    
    def download_file(self, file_id: str, file_name: str, mime_type: str, _recursion_depth: int = 0) -> Optional[Path]:
        """Download a single file from Google Drive."""
        # Prevent infinite recursion with shortcuts
        if _recursion_depth > 5:
            self.console.print(f"[red]Max recursion depth reached for: {file_name}[/red]")
            return None
        
        # Sanitize filename for safe file system usage
        safe_filename = self._sanitize_filename(file_name)
        if safe_filename != file_name:
            self.console.print(f"[yellow]Sanitized filename: '{file_name}' -> '{safe_filename}'[/yellow]")
            
        output_path = self.config.output_dir / safe_filename
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists():
            self.console.print(f"[yellow]Skipping existing file: {file_name}[/yellow]")
            return output_path
        
        try:
            # Handle Google Workspace files (need export)
            if mime_type.startswith('application/vnd.google-apps'):
                if mime_type == 'application/vnd.google-apps.document':
                    export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    if not safe_filename.endswith('.docx'):
                        safe_filename += '.docx'
                        output_path = self.config.output_dir / safe_filename
                elif mime_type == 'application/vnd.google-apps.spreadsheet':
                    export_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    if not safe_filename.endswith('.xlsx'):
                        safe_filename += '.xlsx'
                        output_path = self.config.output_dir / safe_filename
                elif mime_type == 'application/vnd.google-apps.presentation':
                    export_mime = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    if not safe_filename.endswith('.pptx'):
                        safe_filename += '.pptx'
                        output_path = self.config.output_dir / safe_filename
                elif mime_type == 'application/vnd.google-apps.shortcut':
                    # Follow the shortcut to get the target file
                    return self._follow_shortcut(file_id, file_name, _recursion_depth)
                else:
                    self.console.print(f"[yellow]Unsupported Google Apps type: {mime_type}[/yellow]")
                    return None
                
                request = self.service.files().export_media(
                    fileId=file_id, 
                    mimeType=export_mime
                )
            else:
                # Regular file download
                request = self.service.files().get_media(fileId=file_id)
            
            # Download the file
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            
            while done is False:
                status, done = downloader.next_chunk()
            
            # Write to file
            with open(output_path, 'wb') as f:
                f.write(fh.getvalue())
            
            self.console.print(f"[green]Downloaded: {safe_filename}[/green]")
            return output_path
            
        except Exception as e:
            self.console.print(f"[red]Error downloading {file_name}: {e}[/red]")
            return None
    
    def download_folder(self, folder_url: str, progress_callback=None) -> List[Tuple[str, Optional[Path]]]:
        """Download all files from a Google Drive folder."""
        folder_id = self.extract_folder_id(folder_url)
        files = self.list_files_in_folder(folder_id)
        
        # Filter out folders only (we'll handle shortcuts in download_file)
        downloadable_files = [
            f for f in files 
            if f['mimeType'] != 'application/vnd.google-apps.folder'
        ]
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("Downloading files...", total=len(downloadable_files))
            
            for file_info in downloadable_files:
                file_path = self.download_file(
                    file_info['id'], 
                    file_info['name'], 
                    file_info['mimeType']
                )
                results.append((file_info['webViewLink'], file_path))
                
                if progress_callback:
                    progress_callback(file_info, file_path)
                
                progress.advance(task)
        
        return results
    
    def extract_all_urls(self, folder_url: str) -> List[Dict[str, str]]:
        """Extract all file URLs from a Google Drive folder."""
        folder_id = self.extract_folder_id(folder_url)
        files = self.list_files_in_folder(folder_id)
        
        file_mappings = []
        for file_info in files:
            if file_info['mimeType'] != 'application/vnd.google-apps.folder':
                file_mappings.append({
                    'name': file_info['name'],
                    'url': file_info['webViewLink'],
                    'id': file_info['id'],
                    'mime_type': file_info['mimeType']
                })
        
        return file_mappings
