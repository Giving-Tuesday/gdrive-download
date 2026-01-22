"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock

from gdrive_download.config import GlobalConfig, DownloaderConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample configuration for testing."""
    config = GlobalConfig()
    config.downloader.output_dir = temp_dir / "downloads"
    return config


@pytest.fixture
def sample_docx_content():
    """Sample DOCX-like content for testing."""
    return """
    <h1>Sample AAR Document</h1>
    <h2>What went well</h2>
    <p>Great leadership development across the team.</p>
    <p>Excellent content creation and engagement metrics.</p>
    
    <h2>Areas for improvement</h2>
    <p>Resource constraints limited our capacity.</p>
    <p>Data collection was challenging and incomplete.</p>
    """


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """# Sample AAR Document

## What went well
- Great leadership development across the team
- Excellent content creation and engagement metrics
- Strong partnerships enabled success

## Areas for improvement
- Resource constraints limited our capacity
- Data collection was challenging and incomplete
- Communication gaps affected coordination
"""


@pytest.fixture
def mock_drive_service():
    """Mock Google Drive service for testing."""
    service = Mock()
    
    # Mock file list response
    service.files().list().execute.return_value = {
        'files': [
            {
                'id': 'file1',
                'name': 'Test AAR.docx',
                'mimeType': 'application/vnd.google-apps.document',
                'webViewLink': 'https://drive.google.com/file/d/file1/view',
                'parents': ['folder1']
            },
            {
                'id': 'file2', 
                'name': 'Another AAR.docx',
                'mimeType': 'application/vnd.google-apps.document',
                'webViewLink': 'https://drive.google.com/file/d/file2/view',
                'parents': ['folder1']
            }
        ],
        'nextPageToken': None
    }
    
    return service


@pytest.fixture
def sample_url_mappings():
    """Sample URL mappings for testing."""
    return [
        {
            'name': 'Test AAR.docx',
            'url': 'https://drive.google.com/file/d/file1/view',
            'id': 'file1',
            'mime_type': 'application/vnd.google-apps.document'
        },
        {
            'name': 'Another AAR.docx', 
            'url': 'https://drive.google.com/file/d/file2/view',
            'id': 'file2',
            'mime_type': 'application/vnd.google-apps.document'
        }
    ]


@pytest.fixture
def sample_analysis_results():
    """Sample analysis results for testing."""
    return {
        'summary': {
            'resource_constraints': 5,
            'data_collection': 3,
            'communication': 2
        },
        'detailed_results': {
            'test_file.md': {
                'resource_constraints': [('Resource constraints limited capacity', 100)],
                'data_collection': [('Data collection was challenging', 200)]
            }
        },
        'representative_quotes': {
            'resource_constraints': [
                ('Resource constraints limited capacity', 'test_file.md')
            ],
            'data_collection': [
                ('Data collection was challenging', 'test_file.md')
            ]
        }
    }