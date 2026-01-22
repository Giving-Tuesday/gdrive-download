"""Google Drive uploading functionality for markdown files."""

import io
import os
import pickle
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ..config import DownloaderConfig

try:
    from markdown_it import MarkdownIt
    MARKDOWN_IT_AVAILABLE = True
except ImportError:
    MARKDOWN_IT_AVAILABLE = False


class GoogleDriveUploader:
    """Uploads markdown files as native Google Docs to Google Drive."""

    SCOPES = ['https://www.googleapis.com/auth/drive']

    # Google Docs import limit (approximately 1.5MB for HTML)
    MAX_IMPORT_SIZE = 1.5 * 1024 * 1024  # 1.5 MB

    def __init__(self, config: DownloaderConfig):
        self.config = config
        self.console = Console()
        self.service = None
        self._setup_service()

        if not MARKDOWN_IT_AVAILABLE:
            raise ImportError(
                "markdown-it-py is required for markdown to HTML conversion. "
                "Install it with: pip install markdown-it-py"
            )

        self.md = MarkdownIt("commonmark", {"html": True, "typographer": True})

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

    def extract_folder_id(self, folder_url: str) -> str:
        """Extract folder ID from Google Drive URL."""
        if '/folders/' in folder_url:
            folder_part = folder_url.split('/folders/')[1]
            return folder_part.split('?')[0].split('/')[0]

        parsed = urlparse(folder_url)
        if 'id' in parse_qs(parsed.query):
            return parse_qs(parsed.query)['id'][0]

        raise ValueError(f"Cannot extract folder ID from URL: {folder_url}")

    def convert_markdown_to_html(self, markdown_path: Path) -> str:
        """Convert a markdown file to HTML.

        Args:
            markdown_path: Path to the markdown file

        Returns:
            HTML string with proper document structure
        """
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Convert markdown to HTML body
        html_body = self.md.render(markdown_content)

        # Wrap in a proper HTML document for Google Docs import
        # Google Docs handles basic HTML well
        title = markdown_path.stem
        html_document = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
{html_body}
</body>
</html>"""

        return html_document

    def verify_folder_access(self, folder_id: str) -> Dict[str, str]:
        """Verify target folder exists and is writable.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            Dict with folder metadata (id, name, mimeType)

        Raises:
            ValueError: If folder doesn't exist or isn't writable
        """
        try:
            folder_info = self.service.files().get(
                fileId=folder_id,
                fields="id,name,mimeType,capabilities",
                supportsAllDrives=True
            ).execute()

            if folder_info.get('mimeType') != 'application/vnd.google-apps.folder':
                raise ValueError(f"Target ID {folder_id} is not a folder")

            # Check write permissions
            capabilities = folder_info.get('capabilities', {})
            can_add_children = capabilities.get('canAddChildren', False)

            if not can_add_children:
                raise ValueError(f"No write access to folder: {folder_info.get('name', folder_id)}")

            return {
                'id': folder_info['id'],
                'name': folder_info.get('name', 'Unknown Folder'),
                'mimeType': folder_info['mimeType']
            }

        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"Folder not found: {folder_id}")
            raise ValueError(f"Cannot access folder: {e}")

    def check_existing_doc(self, folder_id: str, doc_name: str) -> Optional[Dict[str, str]]:
        """Check if a document with the given name exists in the folder.

        Args:
            folder_id: Target folder ID
            doc_name: Document name to check

        Returns:
            File info dict if exists, None otherwise
        """
        try:
            # Search for exact name match in folder
            query = (
                f"'{folder_id}' in parents and "
                f"name = '{doc_name}' and "
                f"mimeType = 'application/vnd.google-apps.document' and "
                f"trashed = false"
            )

            response = self.service.files().list(
                q=query,
                fields="files(id,name,webViewLink)",
                pageSize=1,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = response.get('files', [])
            if files:
                return files[0]
            return None

        except HttpError:
            return None

    def upload_as_google_doc(
        self,
        markdown_path: Path,
        target_folder_id: str,
        custom_name: Optional[str] = None,
        skip_existing: bool = True
    ) -> Dict[str, str]:
        """Upload a markdown file as a native Google Doc.

        Args:
            markdown_path: Path to the markdown file
            target_folder_id: ID of the target Google Drive folder
            custom_name: Custom name for the Google Doc (default: markdown filename without extension)
            skip_existing: Skip if document with same name exists (default: True)

        Returns:
            Dict with upload result:
                - id: Google Doc ID
                - name: Document name
                - webViewLink: URL to view the document
                - status: 'created', 'skipped', or 'error'
                - message: Status message
        """
        # Determine document name
        doc_name = custom_name or markdown_path.stem

        result = {
            'source_file': str(markdown_path),
            'name': doc_name,
            'id': None,
            'webViewLink': None,
            'status': 'pending',
            'message': ''
        }

        # Check if file exists
        if not markdown_path.exists():
            result['status'] = 'error'
            result['message'] = f"File not found: {markdown_path}"
            return result

        # Check for existing document
        if skip_existing:
            existing = self.check_existing_doc(target_folder_id, doc_name)
            if existing:
                result['status'] = 'skipped'
                result['id'] = existing['id']
                result['webViewLink'] = existing.get('webViewLink')
                result['message'] = f"Document already exists: {doc_name}"
                return result

        try:
            # Convert markdown to HTML
            html_content = self.convert_markdown_to_html(markdown_path)

            # Check size limit
            html_bytes = html_content.encode('utf-8')
            if len(html_bytes) > self.MAX_IMPORT_SIZE:
                result['status'] = 'error'
                result['message'] = (
                    f"File too large for Google Docs import. "
                    f"Size: {len(html_bytes) / 1024 / 1024:.2f}MB, "
                    f"Limit: {self.MAX_IMPORT_SIZE / 1024 / 1024:.2f}MB"
                )
                return result

            # Prepare file metadata
            file_metadata = {
                'name': doc_name,
                'mimeType': 'application/vnd.google-apps.document',
                'parents': [target_folder_id]
            }

            # Create media upload from HTML content
            media = MediaIoBaseUpload(
                io.BytesIO(html_bytes),
                mimetype='text/html',
                resumable=True
            )

            # Upload and convert to Google Doc
            uploaded_file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink',
                supportsAllDrives=True
            ).execute()

            result['id'] = uploaded_file['id']
            result['name'] = uploaded_file['name']
            result['webViewLink'] = uploaded_file.get('webViewLink')
            result['status'] = 'created'
            result['message'] = f"Successfully uploaded: {doc_name}"

        except HttpError as e:
            result['status'] = 'error'
            result['message'] = f"Upload failed: {e}"

        except Exception as e:
            result['status'] = 'error'
            result['message'] = f"Error processing file: {e}"

        return result

    def upload_multiple(
        self,
        markdown_paths: List[Path],
        target_folder_id: str,
        skip_existing: bool = True,
        progress_callback=None
    ) -> List[Dict[str, str]]:
        """Upload multiple markdown files as Google Docs.

        Args:
            markdown_paths: List of markdown file paths
            target_folder_id: ID of the target Google Drive folder
            skip_existing: Skip if document with same name exists
            progress_callback: Optional callback function for progress updates

        Returns:
            List of upload result dicts
        """
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("Uploading files...", total=len(markdown_paths))

            for markdown_path in markdown_paths:
                result = self.upload_as_google_doc(
                    markdown_path,
                    target_folder_id,
                    skip_existing=skip_existing
                )
                results.append(result)

                if progress_callback:
                    progress_callback(result)

                progress.advance(task)

        return results
