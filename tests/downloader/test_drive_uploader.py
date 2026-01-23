"""Tests for GoogleDriveUploader class."""

import io
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

from gdrive_download.config import DownloaderConfig
from gdrive_download.downloader.drive_uploader import GoogleDriveUploader, MarkdownToDocsConverter


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

        mock_drive_service = Mock()
        mock_docs_service = Mock()

        # Return different services based on API name
        def build_side_effect(api_name, version, credentials):
            if api_name == 'drive':
                return mock_drive_service
            elif api_name == 'docs':
                return mock_docs_service
            return Mock()

        mock_build.side_effect = build_side_effect

        uploader = GoogleDriveUploader(mock_config)
        uploader._mock_service = mock_drive_service  # Store for test access (backwards compat)
        uploader.drive_service = mock_drive_service
        uploader.docs_service = mock_docs_service

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
        assert uploader.drive_service is not None
        assert uploader.docs_service is not None
        # build is called twice: once for Drive API, once for Docs API
        assert mock_build.call_count == 2

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

    def test_convert_markdown_uses_style_inheritance(self, mock_uploader, sample_markdown_file):
        """Test that generated HTML uses 'inherit' for fonts to respect target document styles."""
        html = mock_uploader.convert_markdown_to_html(sample_markdown_file)

        # Verify CSS is included
        assert "<style>" in html
        assert "</style>" in html

        # Verify font-family: inherit is used for text elements
        assert "font-family: inherit" in html

        # Verify font-size: inherit is used for text elements
        assert "font-size: inherit" in html

        # Verify code blocks still use monospace (explicit font)
        assert "Courier New" in html or "monospace" in html

        # Verify styling doesn't hardcode specific fonts for normal text
        # The key is that p, h1-h6 should inherit, not specify fonts
        assert "p {" in html or "p{" in html
        # Check that the p style block contains inherit
        import re
        p_style_match = re.search(r'p\s*\{[^}]*\}', html, re.DOTALL)
        assert p_style_match is not None
        assert "inherit" in p_style_match.group(0)


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


class TestExtractDocAndTabId:
    """Tests for extracting document and tab IDs from URLs."""

    def test_extract_doc_id_only(self, mock_uploader):
        """Test extracting document ID from URL without tab."""
        url = "https://docs.google.com/document/d/1ABC123XYZ/edit"
        doc_id, tab_id = mock_uploader.extract_doc_and_tab_id(url)

        assert doc_id == "1ABC123XYZ"
        assert tab_id is None

    def test_extract_doc_and_tab_from_query(self, mock_uploader):
        """Test extracting both IDs from URL with query parameter."""
        url = "https://docs.google.com/document/d/1ABC123/edit?tab=t.xyz789"
        doc_id, tab_id = mock_uploader.extract_doc_and_tab_id(url)

        assert doc_id == "1ABC123"
        assert tab_id == "t.xyz789"

    def test_extract_doc_and_tab_from_fragment(self, mock_uploader):
        """Test extracting both IDs from URL with fragment."""
        url = "https://docs.google.com/document/d/1ABC123/edit#tab=t.abc"
        doc_id, tab_id = mock_uploader.extract_doc_and_tab_id(url)

        assert doc_id == "1ABC123"
        assert tab_id == "t.abc"

    def test_extract_invalid_url(self, mock_uploader):
        """Test extracting from invalid URL raises error."""
        with pytest.raises(ValueError, match="Cannot extract document ID"):
            mock_uploader.extract_doc_and_tab_id("https://google.com/not-a-doc")


class TestMarkdownToDocsConverter:
    """Tests for the MarkdownToDocsConverter class."""

    def test_convert_heading(self):
        """Test converting a markdown heading."""
        converter = MarkdownToDocsConverter()
        requests = converter.convert("# Hello World\n")

        # Should have insertText and updateParagraphStyle
        assert len(requests) >= 2
        assert any('insertText' in r for r in requests)
        assert any('updateParagraphStyle' in r for r in requests)

        # Check the inserted text
        insert_req = next(r for r in requests if 'insertText' in r)
        assert 'Hello World' in insert_req['insertText']['text']

        # Check heading style
        style_req = next(r for r in requests if 'updateParagraphStyle' in r)
        assert style_req['updateParagraphStyle']['paragraphStyle']['namedStyleType'] == 'HEADING_1'

    def test_convert_paragraph_with_bold(self):
        """Test converting a paragraph with bold text."""
        converter = MarkdownToDocsConverter()
        requests = converter.convert("This is **bold** text.\n")

        # Should have insertText and updateTextStyle for bold
        assert any('insertText' in r for r in requests)

        # Check bold style was applied
        bold_reqs = [r for r in requests if 'updateTextStyle' in r and r['updateTextStyle'].get('textStyle', {}).get('bold')]
        assert len(bold_reqs) >= 1

    def test_convert_bullet_list(self):
        """Test converting a bullet list."""
        converter = MarkdownToDocsConverter()
        requests = converter.convert("- Item 1\n- Item 2\n")

        # Should have insertText and createParagraphBullets
        assert any('insertText' in r for r in requests)
        assert any('createParagraphBullets' in r for r in requests)

        bullet_req = next(r for r in requests if 'createParagraphBullets' in r)
        assert 'BULLET' in bullet_req['createParagraphBullets']['bulletPreset']

    def test_convert_with_tab_id(self):
        """Test that tab ID is included in requests."""
        converter = MarkdownToDocsConverter()
        requests = converter.convert("# Test\n", tab_id="t.abc123")

        # Check that tabId is in location/range
        for req in requests:
            if 'insertText' in req:
                assert req['insertText']['location'].get('tabId') == 't.abc123'
            elif 'updateParagraphStyle' in req:
                assert req['updateParagraphStyle']['range'].get('tabId') == 't.abc123'

    def test_convert_link(self):
        """Test converting a link."""
        converter = MarkdownToDocsConverter()
        requests = converter.convert("Check [this link](https://example.com).\n")

        # Should have link style
        link_reqs = [r for r in requests if 'updateTextStyle' in r and 'link' in r['updateTextStyle'].get('textStyle', {})]
        assert len(link_reqs) >= 1
        assert link_reqs[0]['updateTextStyle']['textStyle']['link']['url'] == 'https://example.com'

    def test_footnote_plugin_enabled(self):
        """Test that the footnote plugin is enabled for parsing."""
        converter = MarkdownToDocsConverter()

        # Check that mdit-py-plugins is available and footnote_definitions exists
        assert hasattr(converter, 'footnote_definitions')
        assert isinstance(converter.footnote_definitions, dict)

    def test_convert_footnote_as_text(self):
        """Test that footnotes in markdown are rendered as plain text.

        Note: Google Docs API footnote creation requires a complex two-pass
        process that is not currently supported. Footnotes appear as text.
        """
        converter = MarkdownToDocsConverter()
        markdown = "This is text with a footnote[^1].\n\n[^1]: This is the footnote content.\n"

        requests = converter.convert(markdown)

        # Should have insertText for the main paragraph
        insert_reqs = [r for r in requests if 'insertText' in r]
        assert len(insert_reqs) >= 1

        # Footnote references and definitions are parsed but rendered as text
        # (no createFootnote requests since that's not supported)
        footnote_reqs = [r for r in requests if 'createFootnote' in r]
        assert len(footnote_reqs) == 0  # Not supported in current implementation


class TestWriteToTab:
    """Tests for writing to document tabs."""

    def test_get_tab_info(self, mock_uploader):
        """Test getting tab information."""
        mock_uploader.docs_service.documents().get().execute.return_value = {
            'tabs': [{
                'tabProperties': {
                    'tabId': 't.0',
                    'title': 'Main Tab',
                    'index': 0
                },
                'documentTab': {
                    'body': {
                        'content': [
                            {'endIndex': 100}
                        ]
                    }
                }
            }]
        }

        tab_info = mock_uploader.get_tab_info('doc123')

        assert tab_info['id'] == 't.0'
        assert tab_info['title'] == 'Main Tab'
        assert tab_info['content_length'] == 100

    def test_get_tab_info_specific_tab(self, mock_uploader):
        """Test getting info for a specific tab."""
        mock_uploader.docs_service.documents().get().execute.return_value = {
            'tabs': [
                {
                    'tabProperties': {'tabId': 't.0', 'title': 'Tab One', 'index': 0},
                    'documentTab': {'body': {'content': [{'endIndex': 50}]}}
                },
                {
                    'tabProperties': {'tabId': 't.1', 'title': 'Tab Two', 'index': 1},
                    'documentTab': {'body': {'content': [{'endIndex': 200}]}}
                }
            ]
        }

        tab_info = mock_uploader.get_tab_info('doc123', 't.1')

        assert tab_info['id'] == 't.1'
        assert tab_info['title'] == 'Tab Two'
        assert tab_info['content_length'] == 200

    def test_get_tab_info_not_found(self, mock_uploader):
        """Test error when tab not found."""
        mock_uploader.docs_service.documents().get().execute.return_value = {
            'tabs': [{
                'tabProperties': {'tabId': 't.0', 'title': 'Tab One', 'index': 0},
                'documentTab': {'body': {'content': []}}
            }]
        }

        with pytest.raises(ValueError, match="Tab not found"):
            mock_uploader.get_tab_info('doc123', 't.nonexistent')

    def test_write_to_tab_success(self, mock_uploader):
        """Test successful write to tab."""
        # Mock get_tab_info
        mock_uploader.docs_service.documents().get().execute.return_value = {
            'tabs': [{
                'tabProperties': {'tabId': 't.0', 'title': 'Main', 'index': 0},
                'documentTab': {'body': {'content': [{'endIndex': 1}]}}
            }]
        }

        # Mock batchUpdate
        mock_uploader.docs_service.documents().batchUpdate().execute.return_value = {}

        result = mock_uploader.write_to_tab('doc123', '# Hello\n', 't.0', replace=True)

        assert result['status'] == 'success'
        assert 'webViewLink' in result
        mock_uploader.docs_service.documents().batchUpdate.assert_called()

    def test_write_to_tab_no_permission(self, mock_uploader):
        """Test write fails without permission."""
        from googleapiclient.errors import HttpError

        mock_uploader.docs_service.documents().get().execute.return_value = {
            'tabs': [{
                'tabProperties': {'tabId': 't.0', 'title': 'Main', 'index': 0},
                'documentTab': {'body': {'content': [{'endIndex': 1}]}}
            }]
        }

        # Mock permission error
        mock_response = Mock()
        mock_response.status = 403
        mock_uploader.docs_service.documents().batchUpdate().execute.side_effect = HttpError(
            mock_response, b'Permission denied'
        )

        result = mock_uploader.write_to_tab('doc123', '# Hello\n')

        assert result['status'] == 'error'
        assert 'permission' in result['message'].lower()


class TestGetTabContentPreview:
    """Tests for getting tab content previews."""

    def test_get_preview(self, mock_uploader):
        """Test getting content preview."""
        mock_uploader.docs_service.documents().get().execute.return_value = {
            'tabs': [{
                'tabProperties': {'tabId': 't.0', 'title': 'Main', 'index': 0},
                'documentTab': {
                    'body': {
                        'content': [{
                            'paragraph': {
                                'elements': [{
                                    'textRun': {'content': 'Hello World! This is test content.'}
                                }]
                            }
                        }]
                    }
                }
            }]
        }

        preview = mock_uploader.get_tab_content_preview('doc123')

        assert 'Hello World' in preview

    def test_get_preview_empty(self, mock_uploader):
        """Test preview of empty tab."""
        mock_uploader.docs_service.documents().get().execute.return_value = {
            'tabs': [{
                'tabProperties': {'tabId': 't.0', 'title': 'Main', 'index': 0},
                'documentTab': {'body': {'content': []}}
            }]
        }

        preview = mock_uploader.get_tab_content_preview('doc123')

        assert preview == "(empty)"

    def test_get_preview_truncated(self, mock_uploader):
        """Test preview is truncated for long content."""
        long_content = "A" * 1000
        mock_uploader.docs_service.documents().get().execute.return_value = {
            'tabs': [{
                'tabProperties': {'tabId': 't.0', 'title': 'Main', 'index': 0},
                'documentTab': {
                    'body': {
                        'content': [{
                            'paragraph': {
                                'elements': [{
                                    'textRun': {'content': long_content}
                                }]
                            }
                        }]
                    }
                }
            }]
        }

        preview = mock_uploader.get_tab_content_preview('doc123', max_chars=100)

        assert len(preview) <= 103  # 100 + "..."
        assert preview.endswith("...")
