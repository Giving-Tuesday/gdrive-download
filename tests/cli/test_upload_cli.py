"""Tests for upload CLI command."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from gdrive_download.cli.upload import upload, collect_markdown_files


@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_credentials_file(tmp_path):
    """Create a mock credentials file."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text('{"installed": {"client_id": "test"}}')
    return creds_file


@pytest.fixture
def sample_markdown_files(tmp_path):
    """Create sample markdown files for testing."""
    files = []
    for i in range(3):
        md_file = tmp_path / f"doc_{i}.md"
        md_file.write_text(f"# Document {i}\n\nContent for document {i}.")
        files.append(md_file)
    return files


class TestCollectMarkdownFiles:
    """Tests for the collect_markdown_files helper function."""

    def test_collect_from_explicit_files(self, tmp_path):
        """Test collecting explicitly specified files."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        files = collect_markdown_files((str(md_file),), None, "*.md")

        assert len(files) == 1
        assert files[0] == md_file

    def test_collect_from_directory(self, tmp_path, sample_markdown_files):
        """Test collecting files from a directory."""
        files = collect_markdown_files((), tmp_path, "*.md")

        assert len(files) == 3
        assert all(f.suffix == '.md' for f in files)

    def test_collect_skips_non_markdown(self, tmp_path):
        """Test that non-markdown files are skipped."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Not markdown")

        files = collect_markdown_files((str(txt_file), str(md_file)), None, "*.md")

        assert len(files) == 1
        assert files[0] == md_file

    def test_collect_deduplicates(self, tmp_path, sample_markdown_files):
        """Test that duplicate files are removed."""
        # Specify same file explicitly and via directory
        files = collect_markdown_files(
            (str(sample_markdown_files[0]),),
            tmp_path,
            "*.md"
        )

        # Should have all 3 unique files
        assert len(files) == 3

    def test_collect_with_pattern(self, tmp_path):
        """Test collecting with custom glob pattern."""
        # Create files with different extensions
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Text file")

        files = collect_markdown_files((), tmp_path, "*.txt")

        # Should not pick up non-markdown files even with txt pattern
        # because we filter by extension in the function
        assert len(files) == 0


class TestUploadCLI:
    """Tests for the upload CLI command."""

    def test_requires_folder_specification(self, cli_runner, tmp_path):
        """Test that --folder-id or --folder-url is required."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        result = cli_runner.invoke(upload, ['-f', str(md_file)])

        assert result.exit_code != 0
        assert "Either --folder-id or --folder-url is required" in result.output

    def test_requires_file_specification(self, cli_runner):
        """Test that --file or --directory is required."""
        result = cli_runner.invoke(upload, ['--folder-id', '123abc'])

        assert result.exit_code != 0
        assert "Either --file or --directory is required" in result.output

    def test_rejects_both_folder_id_and_url(self, cli_runner, tmp_path):
        """Test that specifying both folder-id and folder-url is rejected."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        result = cli_runner.invoke(upload, [
            '-f', str(md_file),
            '--folder-id', '123abc',
            '--folder-url', 'https://drive.google.com/drive/folders/xyz'
        ])

        assert result.exit_code != 0
        assert "not both" in result.output

    @patch('gdrive_download.cli.upload.GoogleDriveUploader')
    def test_upload_single_file(self, mock_uploader_class, cli_runner, tmp_path):
        """Test uploading a single file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Document")

        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        mock_uploader = Mock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.verify_folder_access.return_value = {
            'id': 'folder_123',
            'name': 'Test Folder',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        mock_uploader.upload_multiple.return_value = [{
            'status': 'created',
            'name': 'test',
            'id': 'doc_123',
            'webViewLink': 'https://docs.google.com/test',
            'source_file': str(md_file),
            'message': 'Successfully uploaded'
        }]

        result = cli_runner.invoke(upload, [
            '-f', str(md_file),
            '--folder-id', 'folder_123',
            '-c', str(creds_file),
            '--no-preview'
        ])

        assert result.exit_code == 0
        assert "Upload complete" in result.output
        mock_uploader.upload_multiple.assert_called_once()

    @patch('gdrive_download.cli.upload.GoogleDriveUploader')
    def test_upload_from_directory(self, mock_uploader_class, cli_runner, tmp_path, sample_markdown_files):
        """Test uploading files from a directory."""
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        mock_uploader = Mock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.verify_folder_access.return_value = {
            'id': 'folder_123',
            'name': 'Test Folder',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        mock_uploader.upload_multiple.return_value = [
            {
                'status': 'created',
                'name': f'doc_{i}',
                'id': f'doc_{i}_id',
                'webViewLink': f'https://docs.google.com/doc_{i}',
                'source_file': str(sample_markdown_files[i]),
                'message': 'Successfully uploaded'
            }
            for i in range(3)
        ]

        result = cli_runner.invoke(upload, [
            '-d', str(tmp_path),
            '--folder-id', 'folder_123',
            '-c', str(creds_file),
            '--no-preview'
        ])

        assert result.exit_code == 0
        assert "Upload complete" in result.output
        mock_uploader.upload_multiple.assert_called_once()

        # Check that all 3 files were passed to upload_multiple
        call_args = mock_uploader.upload_multiple.call_args
        assert len(call_args[0][0]) == 3

    @patch('gdrive_download.cli.upload.GoogleDriveUploader')
    def test_upload_with_folder_url(self, mock_uploader_class, cli_runner, tmp_path):
        """Test uploading with folder URL instead of ID."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        mock_uploader = Mock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.extract_folder_id.return_value = 'extracted_folder_id'
        mock_uploader.verify_folder_access.return_value = {
            'id': 'extracted_folder_id',
            'name': 'Test Folder',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        mock_uploader.upload_multiple.return_value = [{
            'status': 'created',
            'name': 'test',
            'id': 'doc_123',
            'webViewLink': 'https://docs.google.com/test',
            'source_file': str(md_file),
            'message': 'Successfully uploaded'
        }]

        result = cli_runner.invoke(upload, [
            '-f', str(md_file),
            '--folder-url', 'https://drive.google.com/drive/folders/abc123',
            '-c', str(creds_file),
            '--no-preview'
        ])

        assert result.exit_code == 0
        mock_uploader.extract_folder_id.assert_called_with('https://drive.google.com/drive/folders/abc123')

    @patch('gdrive_download.cli.upload.GoogleDriveUploader')
    def test_upload_handles_credentials_not_found(self, mock_uploader_class, cli_runner, tmp_path):
        """Test error handling when credentials file is not found."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        mock_uploader_class.side_effect = FileNotFoundError("Credentials file not found")

        result = cli_runner.invoke(upload, [
            '-f', str(md_file),
            '--folder-id', 'folder_123',
            '-c', str(tmp_path / "nonexistent.json")
        ])

        # Should fail because credentials file doesn't exist (Click validates path)
        assert result.exit_code != 0

    @patch('gdrive_download.cli.upload.GoogleDriveUploader')
    def test_upload_handles_folder_access_error(self, mock_uploader_class, cli_runner, tmp_path):
        """Test error handling when folder access verification fails."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        mock_uploader = Mock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.verify_folder_access.side_effect = ValueError("Folder not found")

        result = cli_runner.invoke(upload, [
            '-f', str(md_file),
            '--folder-id', 'invalid_folder',
            '-c', str(creds_file)
        ])

        assert result.exit_code != 0
        assert "Folder not found" in result.output

    @patch('gdrive_download.cli.upload.GoogleDriveUploader')
    def test_upload_no_files_found(self, mock_uploader_class, cli_runner, tmp_path):
        """Test handling when no markdown files are found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        mock_uploader = Mock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.verify_folder_access.return_value = {
            'id': 'folder_123',
            'name': 'Test Folder',
            'mimeType': 'application/vnd.google-apps.folder'
        }

        result = cli_runner.invoke(upload, [
            '-d', str(empty_dir),
            '--folder-id', 'folder_123',
            '-c', str(creds_file),
            '--no-preview'
        ])

        assert result.exit_code == 0
        assert "No markdown files found" in result.output


class TestUploadPreview:
    """Tests for upload preview functionality."""

    @patch('gdrive_download.cli.upload.GoogleDriveUploader')
    @patch('gdrive_download.cli.upload.Confirm')
    def test_preview_prompts_for_confirmation(self, mock_confirm, mock_uploader_class, cli_runner, tmp_path):
        """Test that preview mode prompts for confirmation."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        mock_uploader = Mock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.verify_folder_access.return_value = {
            'id': 'folder_123',
            'name': 'Test Folder',
            'mimeType': 'application/vnd.google-apps.folder'
        }

        mock_confirm.ask.return_value = False

        result = cli_runner.invoke(upload, [
            '-f', str(md_file),
            '--folder-id', 'folder_123',
            '-c', str(creds_file),
            '--preview'
        ])

        assert "cancelled" in result.output.lower()
        mock_uploader.upload_multiple.assert_not_called()

    @patch('gdrive_download.cli.upload.GoogleDriveUploader')
    def test_no_preview_skips_confirmation(self, mock_uploader_class, cli_runner, tmp_path):
        """Test that --no-preview skips confirmation prompt."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        mock_uploader = Mock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.verify_folder_access.return_value = {
            'id': 'folder_123',
            'name': 'Test Folder',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        mock_uploader.upload_multiple.return_value = [{
            'status': 'created',
            'name': 'test',
            'id': 'doc_123',
            'webViewLink': 'https://docs.google.com/test',
            'source_file': str(md_file),
            'message': 'Success'
        }]

        result = cli_runner.invoke(upload, [
            '-f', str(md_file),
            '--folder-id', 'folder_123',
            '-c', str(creds_file),
            '--no-preview'
        ])

        assert result.exit_code == 0
        mock_uploader.upload_multiple.assert_called_once()
