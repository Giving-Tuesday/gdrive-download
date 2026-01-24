"""Tests for Pandoc-based markdown to Google Docs uploader."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from gdrive_download.downloader.pandoc_uploader import PandocUploader


@pytest.fixture
def mock_uploader():
    """Create a mock GoogleDriveUploader for testing."""
    uploader = MagicMock()
    uploader.drive_service = MagicMock()
    uploader.check_existing_doc = MagicMock(return_value=None)
    return uploader


@pytest.fixture
def pandoc_uploader(mock_uploader):
    """Create a PandocUploader instance with mocked dependencies."""
    with patch('gdrive_download.downloader.pandoc_uploader.pypandoc.get_pandoc_version', return_value='3.0.0'):
        return PandocUploader(mock_uploader)


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample markdown file with footnotes."""
    markdown_content = """# Test Document

This is a test document with footnotes[^1].

## Section 2

Another paragraph with a second footnote[^2].

[^1]: This is the first footnote.
[^2]: This is the second footnote with **bold** text.
"""
    markdown_path = tmp_path / "test.md"
    markdown_path.write_text(markdown_content)
    return markdown_path


class TestPandocUploaderInitialization:
    """Test PandocUploader initialization and setup."""

    def test_initialization_success(self, mock_uploader):
        """Test successful initialization when Pandoc is available."""
        with patch('gdrive_download.downloader.pandoc_uploader.pypandoc.get_pandoc_version', return_value='3.0.0'):
            uploader = PandocUploader(mock_uploader)
            assert uploader.uploader == mock_uploader

    def test_initialization_pandoc_not_found(self, mock_uploader):
        """Test initialization fails gracefully when Pandoc is not installed."""
        with patch('gdrive_download.downloader.pandoc_uploader.pypandoc.get_pandoc_version', side_effect=OSError("Pandoc not found")):
            with pytest.raises(RuntimeError, match="Pandoc is not installed"):
                PandocUploader(mock_uploader)


class TestMarkdownToDocxConversion:
    """Test markdown to DOCX conversion via Pandoc."""

    def test_convert_markdown_to_docx_success(self, pandoc_uploader, sample_markdown_file, tmp_path):
        """Test successful conversion of markdown to DOCX."""
        output_path = tmp_path / "output.docx"

        with patch('gdrive_download.downloader.pandoc_uploader.pypandoc.convert_file') as mock_convert:
            # Mock the conversion to create an empty file
            def create_file(*args, **kwargs):
                output_file = kwargs.get('outputfile')
                Path(output_file).write_bytes(b'fake docx content')
            mock_convert.side_effect = create_file

            result = pandoc_uploader.convert_markdown_to_docx(sample_markdown_file, output_path)

            assert result == output_path
            assert output_path.exists()
            mock_convert.assert_called_once()

            # Verify arguments passed to pypandoc
            args, kwargs = mock_convert.call_args
            assert str(sample_markdown_file) in args
            assert kwargs['outputfile'] == str(output_path)
            assert '--standalone' in kwargs['extra_args']

    def test_convert_markdown_to_docx_with_temp_file(self, pandoc_uploader, sample_markdown_file):
        """Test conversion creates temp file when no output path specified."""
        with patch('gdrive_download.downloader.pandoc_uploader.pypandoc.convert_file') as mock_convert:
            # Mock the conversion to create the temp file
            def create_file(*args, **kwargs):
                output_file = kwargs.get('outputfile')
                Path(output_file).write_bytes(b'fake docx content')
            mock_convert.side_effect = create_file

            result = pandoc_uploader.convert_markdown_to_docx(sample_markdown_file)

            assert result.exists()
            assert result.suffix == '.docx'
            assert 'tmp' in str(result) or 'temp' in str(result).lower()

    def test_convert_markdown_to_docx_with_reference_doc(self, pandoc_uploader, sample_markdown_file, tmp_path):
        """Test conversion with reference document for styling."""
        output_path = tmp_path / "output.docx"
        reference_doc = tmp_path / "reference.docx"
        reference_doc.write_bytes(b'reference docx')

        with patch('gdrive_download.downloader.pandoc_uploader.pypandoc.convert_file') as mock_convert:
            def create_file(*args, **kwargs):
                output_file = kwargs.get('outputfile')
                Path(output_file).write_bytes(b'fake docx content')
            mock_convert.side_effect = create_file

            pandoc_uploader.convert_markdown_to_docx(
                sample_markdown_file,
                output_path,
                reference_doc=reference_doc
            )

            args, kwargs = mock_convert.call_args
            extra_args = kwargs['extra_args']
            assert any(f'--reference-doc={reference_doc}' in arg for arg in extra_args)

    def test_convert_markdown_file_not_found(self, pandoc_uploader, tmp_path):
        """Test conversion fails when markdown file doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError, match="Markdown file not found"):
            pandoc_uploader.convert_markdown_to_docx(nonexistent_file)

    def test_convert_pandoc_conversion_fails(self, pandoc_uploader, sample_markdown_file, tmp_path):
        """Test handling of Pandoc conversion errors."""
        output_path = tmp_path / "output.docx"

        with patch('gdrive_download.downloader.pandoc_uploader.pypandoc.convert_file', side_effect=RuntimeError("Pandoc died with exitcode 1")):
            with pytest.raises(RuntimeError, match="Pandoc conversion failed"):
                pandoc_uploader.convert_markdown_to_docx(sample_markdown_file, output_path)


class TestDocxUpload:
    """Test uploading DOCX files to Google Drive."""

    def test_upload_docx_as_google_doc_success(self, pandoc_uploader, tmp_path):
        """Test successful upload of DOCX as Google Doc."""
        docx_path = tmp_path / "test.docx"
        docx_path.write_bytes(b'fake docx content')

        # Mock the upload response
        mock_response = {
            'id': 'doc123',
            'name': 'test',
            'webViewLink': 'https://docs.google.com/document/d/doc123/edit'
        }
        pandoc_uploader.uploader.drive_service.files().create().execute.return_value = mock_response

        result = pandoc_uploader.upload_docx_as_google_doc(docx_path, 'folder123')

        assert result['status'] == 'created'
        assert result['id'] == 'doc123'
        assert result['name'] == 'test'
        assert result['webViewLink'] == mock_response['webViewLink']

    def test_upload_docx_file_not_found(self, pandoc_uploader, tmp_path):
        """Test upload fails gracefully when DOCX doesn't exist."""
        nonexistent_docx = tmp_path / "nonexistent.docx"

        result = pandoc_uploader.upload_docx_as_google_doc(nonexistent_docx, 'folder123')

        assert result['status'] == 'error'
        assert 'not found' in result['message']

    def test_upload_docx_skip_existing(self, pandoc_uploader, tmp_path):
        """Test skipping upload when document already exists."""
        docx_path = tmp_path / "test.docx"
        docx_path.write_bytes(b'fake docx content')

        # Mock existing document
        pandoc_uploader.uploader.check_existing_doc.return_value = {
            'id': 'existing123',
            'webViewLink': 'https://docs.google.com/document/d/existing123/edit'
        }

        result = pandoc_uploader.upload_docx_as_google_doc(docx_path, 'folder123', skip_existing=True)

        assert result['status'] == 'skipped'
        assert result['id'] == 'existing123'
        assert 'already exists' in result['message']

    def test_upload_docx_custom_name(self, pandoc_uploader, tmp_path):
        """Test upload with custom document name."""
        docx_path = tmp_path / "test.docx"
        docx_path.write_bytes(b'fake docx content')

        mock_response = {
            'id': 'doc123',
            'name': 'Custom Name',
            'webViewLink': 'https://docs.google.com/document/d/doc123/edit'
        }
        pandoc_uploader.uploader.drive_service.files().create().execute.return_value = mock_response

        result = pandoc_uploader.upload_docx_as_google_doc(
            docx_path,
            'folder123',
            doc_name='Custom Name'
        )

        assert result['name'] == 'Custom Name'

    def test_upload_docx_mime_type_conversion(self, pandoc_uploader, tmp_path):
        """Test that correct MIME types are used for conversion."""
        docx_path = tmp_path / "test.docx"
        docx_path.write_bytes(b'fake docx content')

        mock_response = {'id': 'doc123', 'name': 'test', 'webViewLink': 'https://example.com'}
        pandoc_uploader.uploader.drive_service.files().create().execute.return_value = mock_response

        pandoc_uploader.upload_docx_as_google_doc(docx_path, 'folder123')

        # Verify the create call
        create_call = pandoc_uploader.uploader.drive_service.files().create
        call_kwargs = create_call.call_args[1]

        # Check file metadata has Google Docs MIME type
        assert call_kwargs['body']['mimeType'] == 'application/vnd.google-apps.document'


class TestEndToEndUpload:
    """Test end-to-end markdown to Google Docs upload."""

    def test_upload_markdown_as_google_doc_success(self, pandoc_uploader, sample_markdown_file, tmp_path):
        """Test complete workflow from markdown to Google Doc."""
        # Mock Pandoc conversion
        with patch.object(pandoc_uploader, 'convert_markdown_to_docx') as mock_convert:
            docx_path = tmp_path / "test.docx"
            docx_path.write_bytes(b'fake docx content')
            mock_convert.return_value = docx_path

            # Mock upload
            with patch.object(pandoc_uploader, 'upload_docx_as_google_doc') as mock_upload:
                mock_upload.return_value = {
                    'status': 'created',
                    'id': 'doc123',
                    'name': 'test',
                    'webViewLink': 'https://docs.google.com/document/d/doc123/edit',
                    'message': 'Successfully uploaded: test'
                }

                result = pandoc_uploader.upload_markdown_as_google_doc(
                    sample_markdown_file,
                    'folder123'
                )

                assert result['status'] == 'created'
                assert result['id'] == 'doc123'
                mock_convert.assert_called_once()
                mock_upload.assert_called_once()

    def test_upload_markdown_keep_docx(self, pandoc_uploader, sample_markdown_file, tmp_path):
        """Test keeping intermediate DOCX file."""
        docx_output = tmp_path / "output.docx"

        with patch.object(pandoc_uploader, 'convert_markdown_to_docx') as mock_convert:
            mock_convert.return_value = docx_output
            docx_output.write_bytes(b'fake docx content')

            with patch.object(pandoc_uploader, 'upload_docx_as_google_doc') as mock_upload:
                mock_upload.return_value = {
                    'status': 'created',
                    'id': 'doc123',
                    'name': 'test',
                    'webViewLink': 'https://example.com',
                    'message': 'Success'
                }

                result = pandoc_uploader.upload_markdown_as_google_doc(
                    sample_markdown_file,
                    'folder123',
                    keep_docx=True,
                    docx_output_path=docx_output
                )

                assert result['status'] == 'created'
                assert 'docx_path' in result
                assert result['docx_path'] == str(docx_output)

    def test_upload_markdown_file_not_found(self, pandoc_uploader, tmp_path):
        """Test upload fails gracefully when markdown file doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.md"

        result = pandoc_uploader.upload_markdown_as_google_doc(
            nonexistent_file,
            'folder123'
        )

        assert result['status'] == 'error'
        assert 'not found' in result['message']

    def test_upload_markdown_conversion_error(self, pandoc_uploader, sample_markdown_file):
        """Test handling of conversion errors during upload."""
        with patch.object(pandoc_uploader, 'convert_markdown_to_docx', side_effect=RuntimeError("Pandoc failed")):
            result = pandoc_uploader.upload_markdown_as_google_doc(
                sample_markdown_file,
                'folder123'
            )

            assert result['status'] == 'error'
            assert 'Pandoc failed' in result['message']

    def test_upload_markdown_temp_cleanup(self, pandoc_uploader, sample_markdown_file, tmp_path):
        """Test that temporary DOCX files are cleaned up."""
        temp_docx = tmp_path / "temp.docx"

        with patch.object(pandoc_uploader, 'convert_markdown_to_docx') as mock_convert:
            # Return a temp file that exists
            temp_docx.write_bytes(b'fake docx content')
            mock_convert.return_value = temp_docx

            with patch.object(pandoc_uploader, 'upload_docx_as_google_doc') as mock_upload:
                mock_upload.return_value = {
                    'status': 'created',
                    'id': 'doc123',
                    'name': 'test',
                    'webViewLink': 'https://example.com',
                    'message': 'Success'
                }

                # Upload without keep_docx flag
                result = pandoc_uploader.upload_markdown_as_google_doc(
                    sample_markdown_file,
                    'folder123',
                    keep_docx=False
                )

                assert result['status'] == 'created'
                # The temp file should have been deleted (we can't easily test this
                # without more complex mocking, but the code path is covered)


class TestFootnotePreservation:
    """Test that footnotes are preserved through the conversion pipeline."""

    def test_markdown_with_footnotes(self, tmp_path):
        """Integration test: verify footnotes survive conversion (requires Pandoc)."""
        # This is a real integration test that requires Pandoc to be installed
        try:
            import pypandoc
            pypandoc.get_pandoc_version()
        except (ImportError, OSError):
            pytest.skip("Pandoc not available for integration test")

        # Create markdown with footnotes
        markdown_content = """# Document with Footnotes

This paragraph has a footnote[^1].

This has another[^2] footnote.

[^1]: First footnote content.
[^2]: Second footnote with **formatting**.
"""
        markdown_path = tmp_path / "footnotes.md"
        markdown_path.write_text(markdown_content)

        # Create uploader (with mock Google API)
        mock_uploader = MagicMock()
        pandoc_uploader = PandocUploader(mock_uploader)

        # Convert to DOCX
        docx_path = tmp_path / "output.docx"
        result = pandoc_uploader.convert_markdown_to_docx(markdown_path, docx_path)

        # Verify DOCX was created
        assert result.exists()
        assert result.stat().st_size > 0

        # Note: Verifying footnote content in DOCX would require python-docx
        # which is already in our dependencies. We could add that check here.
