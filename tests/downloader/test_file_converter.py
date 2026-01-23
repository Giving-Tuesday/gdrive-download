"""Tests for file conversion functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from gdrive_download.downloader.file_converter import FileConverter


def test_file_converter_init(temp_dir):
    """Test FileConverter initialization."""
    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output"
    
    converter = FileConverter(input_dir, output_dir)
    
    assert converter.input_dir == input_dir
    assert converter.output_dir == output_dir
    assert output_dir.exists()  # Should be created


@patch('gdrive_download.downloader.file_converter.mammoth')
@patch('gdrive_download.downloader.file_converter.FootnotePreservingConverter')
def test_convert_docx_to_markdown(mock_converter_class, mock_mammoth, temp_dir, sample_docx_content):
    """Test DOCX to markdown conversion."""
    # Setup mocks
    mock_result = MagicMock()
    mock_result.value = sample_docx_content
    mock_result.messages = []
    mock_mammoth.convert_to_html.return_value = mock_result

    # Mock the converter instance
    mock_converter_instance = MagicMock()
    mock_converter_instance.convert.return_value = "# Converted Markdown"
    mock_converter_class.return_value = mock_converter_instance

    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output"
    input_dir.mkdir()

    # Create test file
    test_file = input_dir / "test.docx"
    test_file.write_bytes(b"fake docx content")

    converter = FileConverter(input_dir, output_dir)

    with patch('builtins.open', mock_open(read_data=b"fake docx content")):
        result = converter.convert_docx_to_markdown(test_file)

    assert result == "# Converted Markdown"
    mock_mammoth.convert_to_html.assert_called_once()
    mock_converter_class.assert_called_once_with(heading_style="ATX")
    mock_converter_instance.convert.assert_called_once_with(sample_docx_content)


def test_convert_file_docx(temp_dir):
    """Test converting a single DOCX file."""
    input_dir = temp_dir / "input" 
    output_dir = temp_dir / "output"
    input_dir.mkdir()
    
    # Create test DOCX file
    test_file = input_dir / "test.docx"
    test_file.write_bytes(b"fake docx content")
    
    converter = FileConverter(input_dir, output_dir)
    
    with patch.object(converter, 'convert_docx_to_markdown', return_value="# Test Markdown"):
        result = converter.convert_file(test_file)
    
    assert result == output_dir / "test.md"
    assert result.exists()
    assert result.read_text() == "# Test Markdown"


def test_convert_file_unsupported_type(temp_dir):
    """Test converting unsupported file type."""
    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output" 
    input_dir.mkdir()
    
    # Create test file with unsupported extension
    test_file = input_dir / "test.txt"
    test_file.write_text("test content")
    
    converter = FileConverter(input_dir, output_dir)
    result = converter.convert_file(test_file)
    
    assert result is None


def test_convert_file_nonexistent(temp_dir):
    """Test converting non-existent file."""
    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output"
    
    converter = FileConverter(input_dir, output_dir)
    result = converter.convert_file(input_dir / "nonexistent.docx")
    
    assert result is None


def test_convert_file_existing_output(temp_dir):
    """Test that existing output files are skipped."""
    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    
    # Create input and output files
    test_file = input_dir / "test.docx"
    test_file.write_bytes(b"fake docx content")
    
    output_file = output_dir / "test.md"
    output_file.write_text("existing content")
    
    converter = FileConverter(input_dir, output_dir)
    result = converter.convert_file(test_file)
    
    assert result == output_file
    assert output_file.read_text() == "existing content"  # Should be unchanged


def test_convert_all_files(temp_dir):
    """Test converting all files in a directory."""
    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output"
    input_dir.mkdir()
    
    # Create test files
    (input_dir / "test1.docx").write_bytes(b"content1")
    (input_dir / "test2.docx").write_bytes(b"content2")
    (input_dir / "test3.txt").write_text("should be ignored")
    
    converter = FileConverter(input_dir, output_dir)
    
    with patch.object(converter, 'convert_file') as mock_convert:
        mock_convert.side_effect = [
            output_dir / "test1.md",
            output_dir / "test2.md"
        ]
        
        results = converter.convert_all_files()
    
    assert len(results) == 2
    assert mock_convert.call_count == 2


def test_get_conversion_stats(temp_dir):
    """Test getting conversion statistics."""
    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    
    # Create input and output files
    (input_dir / "test1.docx").write_bytes(b"content1")
    (input_dir / "test2.docx").write_bytes(b"content2")
    (output_dir / "test1.md").write_text("converted1")
    
    converter = FileConverter(input_dir, output_dir)
    stats = converter.get_conversion_stats()
    
    assert stats['input_files'] == 2
    assert stats['output_files'] == 1
    assert stats['conversion_rate'] == 0.5