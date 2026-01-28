"""Tests for GoogleDriveDownloader functionality."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from gdrive_download.downloader.drive_downloader import GoogleDriveDownloader
from gdrive_download.config import DownloaderConfig


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration."""
    config = DownloaderConfig(
        output_dir=temp_dir / "downloads",
        credentials_file=temp_dir / "credentials.json",
        token_file=temp_dir / "token.pickle"
    )
    return config


class TestExtractFileId:
    """Tests for extract_file_id method."""

    @patch.object(GoogleDriveDownloader, '_setup_service')
    def test_extract_from_docs_url(self, mock_setup, mock_config):
        """Test extracting file ID from Google Docs URL."""
        downloader = GoogleDriveDownloader(mock_config)

        url = "https://docs.google.com/document/d/1abc123DEF_xyz/edit"
        file_id = downloader.extract_file_id(url)

        assert file_id == "1abc123DEF_xyz"

    @patch.object(GoogleDriveDownloader, '_setup_service')
    def test_extract_from_sheets_url(self, mock_setup, mock_config):
        """Test extracting file ID from Google Sheets URL."""
        downloader = GoogleDriveDownloader(mock_config)

        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=0"
        file_id = downloader.extract_file_id(url)

        assert file_id == "abc123"

    @patch.object(GoogleDriveDownloader, '_setup_service')
    def test_extract_from_slides_url(self, mock_setup, mock_config):
        """Test extracting file ID from Google Slides URL."""
        downloader = GoogleDriveDownloader(mock_config)

        url = "https://docs.google.com/presentation/d/abc-123_XYZ/edit"
        file_id = downloader.extract_file_id(url)

        assert file_id == "abc-123_XYZ"

    @patch.object(GoogleDriveDownloader, '_setup_service')
    def test_extract_from_drive_file_url(self, mock_setup, mock_config):
        """Test extracting file ID from Drive file URL."""
        downloader = GoogleDriveDownloader(mock_config)

        url = "https://drive.google.com/file/d/1a2b3c4d5e/view?usp=sharing"
        file_id = downloader.extract_file_id(url)

        assert file_id == "1a2b3c4d5e"

    @patch.object(GoogleDriveDownloader, '_setup_service')
    def test_extract_from_open_url(self, mock_setup, mock_config):
        """Test extracting file ID from open?id= URL."""
        downloader = GoogleDriveDownloader(mock_config)

        url = "https://drive.google.com/open?id=abc123xyz"
        file_id = downloader.extract_file_id(url)

        assert file_id == "abc123xyz"

    @patch.object(GoogleDriveDownloader, '_setup_service')
    def test_extract_invalid_url(self, mock_setup, mock_config):
        """Test that invalid URL raises ValueError."""
        downloader = GoogleDriveDownloader(mock_config)

        with pytest.raises(ValueError, match="Cannot extract file ID"):
            downloader.extract_file_id("https://example.com/not-a-drive-url")


class TestGetFileMetadata:
    """Tests for get_file_metadata method."""

    @patch.object(GoogleDriveDownloader, '_setup_service')
    def test_get_metadata_success(self, mock_setup, mock_config):
        """Test getting file metadata successfully."""
        downloader = GoogleDriveDownloader(mock_config)

        # Mock the service
        mock_service = MagicMock()
        downloader.service = mock_service
        mock_service.files().get().execute.return_value = {
            'id': 'abc123',
            'name': 'Test Document',
            'mimeType': 'application/vnd.google-apps.document',
            'webViewLink': 'https://docs.google.com/document/d/abc123/edit'
        }

        metadata = downloader.get_file_metadata('abc123')

        assert metadata['id'] == 'abc123'
        assert metadata['name'] == 'Test Document'
        assert metadata['mimeType'] == 'application/vnd.google-apps.document'

    @patch.object(GoogleDriveDownloader, '_setup_service')
    def test_get_metadata_not_found(self, mock_setup, mock_config):
        """Test getting metadata for non-existent file."""
        downloader = GoogleDriveDownloader(mock_config)

        # Mock the service to raise an error
        mock_service = MagicMock()
        downloader.service = mock_service
        mock_service.files().get().execute.side_effect = Exception("File not found")

        with pytest.raises(ValueError, match="Cannot get metadata"):
            downloader.get_file_metadata('nonexistent')


class TestDownloadSingleFile:
    """Tests for download_single_file method."""

    @patch.object(GoogleDriveDownloader, '_setup_service')
    @patch.object(GoogleDriveDownloader, 'get_file_metadata')
    @patch.object(GoogleDriveDownloader, 'download_file')
    def test_download_by_file_id(self, mock_download, mock_metadata, mock_setup, mock_config, temp_dir):
        """Test downloading a single file by ID."""
        downloader = GoogleDriveDownloader(mock_config)

        mock_metadata.return_value = {
            'id': 'abc123',
            'name': 'Test Document',
            'mimeType': 'application/vnd.google-apps.document',
            'webViewLink': 'https://docs.google.com/document/d/abc123/edit'
        }
        mock_download.return_value = temp_dir / 'Test Document.docx'

        web_link, file_path = downloader.download_single_file(file_id='abc123')

        assert web_link == 'https://docs.google.com/document/d/abc123/edit'
        assert file_path == temp_dir / 'Test Document.docx'
        mock_metadata.assert_called_once_with('abc123')

    @patch.object(GoogleDriveDownloader, '_setup_service')
    @patch.object(GoogleDriveDownloader, 'extract_file_id')
    @patch.object(GoogleDriveDownloader, 'get_file_metadata')
    @patch.object(GoogleDriveDownloader, 'download_file')
    def test_download_by_url(self, mock_download, mock_metadata, mock_extract, mock_setup, mock_config, temp_dir):
        """Test downloading a single file by URL."""
        downloader = GoogleDriveDownloader(mock_config)

        mock_extract.return_value = 'abc123'
        mock_metadata.return_value = {
            'id': 'abc123',
            'name': 'Test Document',
            'mimeType': 'application/vnd.google-apps.document',
            'webViewLink': 'https://docs.google.com/document/d/abc123/edit'
        }
        mock_download.return_value = temp_dir / 'Test Document.docx'

        web_link, file_path = downloader.download_single_file(
            file_url='https://docs.google.com/document/d/abc123/edit'
        )

        assert web_link == 'https://docs.google.com/document/d/abc123/edit'
        mock_extract.assert_called_once_with('https://docs.google.com/document/d/abc123/edit')

    @patch.object(GoogleDriveDownloader, '_setup_service')
    def test_download_no_args(self, mock_setup, mock_config):
        """Test that calling without arguments raises ValueError."""
        downloader = GoogleDriveDownloader(mock_config)

        with pytest.raises(ValueError, match="Either file_id or file_url must be provided"):
            downloader.download_single_file()
