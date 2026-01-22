"""Tests for GoogleDriveUploader class."""

import io
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

from gdrive_download.config import DownloaderConfig
from gdrive_download.downloader.drive_uploader import GoogleDriveUploader


@pytest.fixture
def mock_credentials_file(tmp_path):
    """Create a mock credentials file."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text('{"installed": {"client_id": "test"}}')
    return creds_file


@pytest.fixture
def mock_config(mock_credentials_file, tmp_path):
    """Create a mock downloader config."""
    return DownloaderConfig(
        credentials_file=mock_credentials_file,
        token_file=tmp_path / "token.pickle",
        output_dir=tmp_path / "output"
    )


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample markdown file for testing."""
    md_file = tmp_path / "test_document.md"
    md_file.write_text("""# Test Document

This is a **test** document with:

- Item 1
- Item 2
- Item 3

## Section Two

Some more content with [a link](https://example.com).
""")
    return md_file


@pytest.fixture
def large_markdown_file(tmp_path):
    """Create a large markdown file that exceeds size limit."""
    md_file = tmp_path / "large_document.md"
    # Create content larger than 1.5MB
    content = "# Large Document\n\n" + ("x" * 2 * 1024 * 1024)
    md_file.write_text(content)
    return md_file


@pytest.fixture
def mock_uploader(mock_config):
    """Create a GoogleDriveUploader with mocked dependencies."""
    with patch('gdrive_download.downloader.drive_uploader.InstalledAppFlow') as mock_flow, \
         patch('gdrive_download.downloader.drive_uploader.build') as mock_build, \
         patch('gdrive_download.downloader.drive_uploader.pickle') as mock_pickle:

        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = Mock(valid=True)
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance

        mock_service = Mock()
        mock_build.return_value = mock_service

        uploader = GoogleDriveUploader(mock_config)
        uploader._mock_service = mock_service  # Store for test access

        yield uploader


class TestGoogleDriveUploaderInit:
    """Tests for GoogleDriveUploader initialization."""

    @patch('gdrive_download.downloader.drive_uploader.pickle')
    @patch('gdrive_download.downloader.drive_uploader.InstalledAppFlow')
    @patch('gdrive_download.downloader.drive_uploader.build')
    def test_init_with_new_auth(self, mock_build, mock_flow, mock_pickle, mock_config):
        """Test initialization with new OAuth flow."""
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = Mock(valid=True)
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance

        uploader = GoogleDriveUploader(mock_config)

        assert uploader.service is not None
        mock_build.assert_called_once_with('drive', 'v3', credentials=mock_flow_instance.run_local_server.return_value)

    @patch('gdrive_download.downloader.drive_uploader.InstalledAppFlow')
    @patch('gdrive_download.downloader.drive_uploader.build')
    @patch('gdrive_download.downloader.drive_uploader.pickle')
    def test_init_with_existing_token(self, mock_pickle, mock_build, mock_flow, mock_config, tmp_path):
        """Test initialization with existing valid token."""
        # Create a mock token file
        token_file = tmp_path / "token.pickle"
        token_file.touch()
        mock_config.token_file = token_file

        mock_creds = Mock(valid=True)
        mock_pickle.load.return_value = mock_creds

        uploader = GoogleDriveUploader(mock_config)

        assert uploader.service is not None
        mock_flow.from_client_secrets_file.assert_not_called()


class TestExtractFolderId:
    """Tests for folder ID extraction from URLs."""

    def test_extract_from_folders_url(self, mock_uploader):
        """Test extracting folder ID from /folders/ URL."""
        url = "https://drive.google.com/drive/folders/1ABC123XYZ"
        folder_id = mock_uploader.extract_folder_id(url)
        assert folder_id == "1ABC123XYZ"

    def test_extract_from_folders_url_with_query(self, mock_uploader):
        """Test extracting folder ID from URL with query params."""
        url = "https://drive.google.com/drive/folders/1ABC123XYZ?usp=sharing"
        folder_id = mock_uploader.extract_folder_id(url)
        assert folder_id == "1ABC123XYZ"

    def test_extract_from_id_query_param(self, mock_uploader):
        """Test extracting folder ID from id query parameter."""
        url = "https://drive.google.com/drive?id=1ABC123XYZ"
        folder_id = mock_uploader.extract_folder_id(url)
        assert folder_id == "1ABC123XYZ"

    def test_extract_invalid_url(self, mock_uploader):
        """Test extracting folder ID from invalid URL raises error."""
        with pytest.raises(ValueError, match="Cannot extract folder ID"):
            mock_uploader.extract_folder_id("https://google.com")


class TestConvertMarkdownToHtml:
    """Tests for markdown to HTML conversion."""

    def test_convert_basic_markdown(self, mock_uploader, sample_markdown_file):
        """Test converting basic markdown to HTML."""
        html = mock_uploader.convert_markdown_to_html(sample_markdown_file)

        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "<title>test_document</title>" in html
        assert "<h1>" in html
        assert "Test Document" in html
        assert "<strong>test</strong>" in html
        assert "<li>" in html
        assert "<h2>" in html
        assert 'href="https://example.com"' in html


class TestUploadAsGoogleDoc:
    """Tests for the upload functionality."""

    def test_upload_file_not_found(self, mock_uploader, tmp_path):
        """Test upload with non-existent file returns error."""
        result = mock_uploader.upload_as_google_doc(
            tmp_path / "nonexistent.md",
            "folder_id_123"
        )

        assert result['status'] == 'error'
        assert "File not found" in result['message']

    def test_upload_file_too_large(self, mock_uploader, large_markdown_file):
        """Test upload with file exceeding size limit returns error."""
        # Mock check_existing_doc to return None (no existing doc)
        mock_uploader._mock_service.files().list().execute.return_value = {'files': []}

        result = mock_uploader.upload_as_google_doc(
            large_markdown_file,
            "folder_id_123"
        )

        assert result['status'] == 'error'
        assert "too large" in result['message']

    def test_upload_skip_existing(self, mock_uploader, sample_markdown_file):
        """Test upload skips existing document."""
        # Mock existing document
        mock_uploader._mock_service.files().list().execute.return_value = {
            'files': [{'id': 'existing_id', 'name': 'test_document', 'webViewLink': 'https://docs.google.com/existing'}]
        }

        result = mock_uploader.upload_as_google_doc(
            sample_markdown_file,
            "folder_id_123",
            skip_existing=True
        )

        assert result['status'] == 'skipped'
        assert result['id'] == 'existing_id'
        assert "already exists" in result['message']

    def test_upload_success(self, mock_uploader, sample_markdown_file):
        """Test successful upload."""
        # Mock no existing document
        mock_uploader._mock_service.files().list().execute.return_value = {'files': []}

        # Mock successful upload
        mock_uploader._mock_service.files().create().execute.return_value = {
            'id': 'new_doc_id',
            'name': 'test_document',
            'webViewLink': 'https://docs.google.com/new'
        }

        result = mock_uploader.upload_as_google_doc(
            sample_markdown_file,
            "folder_id_123"
        )

        assert result['status'] == 'created'
        assert result['id'] == 'new_doc_id'
        assert result['webViewLink'] == 'https://docs.google.com/new'


class TestVerifyFolderAccess:
    """Tests for folder access verification."""

    def test_verify_folder_success(self, mock_uploader):
        """Test successful folder verification."""
        mock_uploader._mock_service.files().get().execute.return_value = {
            'id': 'folder_id',
            'name': 'Test Folder',
            'mimeType': 'application/vnd.google-apps.folder',
            'capabilities': {'canAddChildren': True}
        }

        result = mock_uploader.verify_folder_access('folder_id')

        assert result['id'] == 'folder_id'
        assert result['name'] == 'Test Folder'

    def test_verify_folder_not_a_folder(self, mock_uploader):
        """Test verification fails for non-folder item."""
        mock_uploader._mock_service.files().get().execute.return_value = {
            'id': 'file_id',
            'name': 'Test File',
            'mimeType': 'application/vnd.google-apps.document'
        }

        with pytest.raises(ValueError, match="not a folder"):
            mock_uploader.verify_folder_access('file_id')

    def test_verify_folder_no_write_access(self, mock_uploader):
        """Test verification fails for read-only folder."""
        mock_uploader._mock_service.files().get().execute.return_value = {
            'id': 'folder_id',
            'name': 'Read Only Folder',
            'mimeType': 'application/vnd.google-apps.folder',
            'capabilities': {'canAddChildren': False}
        }

        with pytest.raises(ValueError, match="No write access"):
            mock_uploader.verify_folder_access('folder_id')


class TestUploadMultiple:
    """Tests for uploading multiple files."""

    def test_upload_multiple_files(self, mock_uploader, tmp_path):
        """Test uploading multiple files."""
        # Create test files
        files = []
        for i in range(3):
            md_file = tmp_path / f"doc_{i}.md"
            md_file.write_text(f"# Document {i}\n\nContent for document {i}.")
            files.append(md_file)

        # Mock no existing documents
        mock_uploader._mock_service.files().list().execute.return_value = {'files': []}

        # Mock successful uploads
        mock_uploader._mock_service.files().create().execute.side_effect = [
            {'id': f'id_{i}', 'name': f'doc_{i}', 'webViewLink': f'https://docs.google.com/{i}'}
            for i in range(3)
        ]

        results = mock_uploader.upload_multiple(files, "folder_id_123")

        assert len(results) == 3
        assert all(r['status'] == 'created' for r in results)
