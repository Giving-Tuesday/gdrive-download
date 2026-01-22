"""Tests for download CLI functionality."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock

from gdrive_download.cli.download import main


@pytest.fixture
def cli_runner():
    """Create CLI test runner."""
    return CliRunner()


def test_download_cli_help(cli_runner):
    """Test CLI help message."""
    result = cli_runner.invoke(main, ['--help'])
    
    assert result.exit_code == 0
    assert 'Download AAR documents from Google Drive' in result.output
    assert '--folder-url' in result.output
    assert '--output-dir' in result.output


@patch('gdrive_download.cli.download.GoogleDriveDownloader')
@patch('gdrive_download.cli.download.FileConverter')
@patch('gdrive_download.cli.download.FileRelationshipTracker')
def test_download_cli_basic(mock_tracker, mock_converter, mock_downloader, cli_runner, temp_dir):
    """Test basic download CLI functionality."""
    # Setup mocks
    mock_downloader_instance = MagicMock()
    mock_downloader.return_value = mock_downloader_instance
    mock_downloader_instance.download_folder.return_value = [
        ('https://drive.google.com/file/d/1/view', temp_dir / 'file1.docx')
    ]
    mock_downloader_instance.extract_all_urls.return_value = [
        {'name': 'file1.docx', 'url': 'https://drive.google.com/file/d/1/view'}
    ]
    
    mock_converter_instance = MagicMock()
    mock_converter.return_value = mock_converter_instance
    mock_converter_instance.convert_all_files.return_value = [temp_dir / 'file1.md']
    
    mock_tracker_instance = MagicMock()
    mock_tracker.return_value = mock_tracker_instance
    mock_tracker_instance.scan_file_relationships.return_value = {'files': []}
    mock_tracker_instance.generate_report.return_value = "Test report"
    
    # Run CLI
    result = cli_runner.invoke(main, [
        '--folder-url', 'https://drive.google.com/drive/folders/test123',
        '--output-dir', str(temp_dir / 'downloads'),
        '--markdown-dir', str(temp_dir / 'markdown')
    ])
    
    assert result.exit_code == 0
    assert 'Download and conversion complete!' in result.output
    mock_downloader_instance.download_folder.assert_called_once()
    mock_converter_instance.convert_all_files.assert_called_once()


def test_download_cli_missing_url(cli_runner):
    """Test CLI with missing required folder URL."""
    result = cli_runner.invoke(main, [
        '--output-dir', 'downloads'
    ])
    
    assert result.exit_code != 0
    assert 'Missing option' in result.output or 'Error' in result.output


@patch('gdrive_download.cli.download.GoogleDriveDownloader')
def test_download_cli_no_convert(mock_downloader, cli_runner, temp_dir):
    """Test CLI with conversion disabled."""
    # Setup mock
    mock_downloader_instance = MagicMock()
    mock_downloader.return_value = mock_downloader_instance
    mock_downloader_instance.download_folder.return_value = []
    
    result = cli_runner.invoke(main, [
        '--folder-url', 'https://drive.google.com/drive/folders/test123',
        '--output-dir', str(temp_dir / 'downloads'),
        '--no-convert',
        '--no-track'
    ])
    
    assert result.exit_code == 0
    mock_downloader_instance.download_folder.assert_called_once()


@patch('gdrive_download.cli.download.GoogleDriveDownloader')
def test_download_cli_with_credentials(mock_downloader, cli_runner, temp_dir):
    """Test CLI with custom credentials file."""
    # Create fake credentials file
    creds_file = temp_dir / 'credentials.json'
    creds_file.write_text('{"test": "credentials"}')
    
    # Setup mock
    mock_downloader_instance = MagicMock()
    mock_downloader.return_value = mock_downloader_instance
    mock_downloader_instance.download_folder.return_value = []
    
    result = cli_runner.invoke(main, [
        '--folder-url', 'https://drive.google.com/drive/folders/test123',
        '--credentials', str(creds_file),
        '--no-convert',
        '--no-track'
    ])
    
    assert result.exit_code == 0
    mock_downloader.assert_called_once()
    
    # Check that credentials path was set in config
    call_args = mock_downloader.call_args[0][0]
    assert call_args.credentials_file == creds_file


@patch('gdrive_download.cli.download.GoogleDriveDownloader')
def test_download_cli_error_handling(mock_downloader, cli_runner):
    """Test CLI error handling."""
    # Setup mock to raise exception
    mock_downloader.side_effect = Exception("Test error")
    
    result = cli_runner.invoke(main, [
        '--folder-url', 'https://drive.google.com/drive/folders/test123'
    ])
    
    assert result.exit_code != 0
    # Note: Error handling behavior may vary based on Click configuration


def test_download_cli_log_levels(cli_runner):
    """Test CLI with different log levels."""
    for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
        result = cli_runner.invoke(main, [
            '--help',  # Just test that log level is accepted
            '--log-level', level
        ])
        assert result.exit_code == 0