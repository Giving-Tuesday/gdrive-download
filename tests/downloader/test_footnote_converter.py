"""Tests for footnote preservation in HTML to Markdown conversion."""

import pytest
from bs4 import BeautifulSoup

from gdrive_download.downloader.file_converter import FootnotePreservingConverter


class TestFootnotePreservingConverter:
    """Test suite for FootnotePreservingConverter."""

    def test_basic_footnote_conversion(self):
        """Test converting a single footnote from HTML to Pandoc markdown."""
        html = """
        <p>This is a text with a footnote.<sup><a href="#fn1">[1]</a></sup></p>
        <ol>
            <li id="fn1">This is the footnote content. ↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Should have footnote reference
        assert '[^1]' in result
        # Should have footnote definition
        assert '[^1]: This is the footnote content.' in result
        # Should not have HTML artifacts
        assert '<sup>' not in result
        assert '<a href' not in result
        assert '↩' not in result

    def test_multiple_footnotes(self):
        """Test converting multiple footnotes with sequential numbering."""
        html = """
        <p>First reference<sup><a href="#fn1">[1]</a></sup> and second<sup><a href="#fn2">[2]</a></sup>.</p>
        <ol>
            <li id="fn1">First footnote content. ↩</li>
            <li id="fn2">Second footnote content. ↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Check references
        assert '[^1]' in result
        assert '[^2]' in result

        # Check definitions
        assert '[^1]: First footnote content.' in result
        assert '[^2]: Second footnote content.' in result

        # Verify order (definitions should come after text)
        ref1_pos = result.find('[^1]')
        def1_pos = result.find('[^1]: First')
        assert ref1_pos < def1_pos

    def test_footnote_with_formatting(self):
        """Test footnote content with nested HTML formatting."""
        html = """
        <p>Text with footnote<sup><a href="#fn1">[1]</a></sup>.</p>
        <ol>
            <li id="fn1">Footnote with <strong>bold</strong> and <em>italic</em> text. ↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Should preserve the footnote structure
        assert '[^1]' in result
        # Content should be extracted (formatting may vary based on converter)
        assert '[^1]:' in result
        assert 'bold' in result
        assert 'italic' in result

    def test_no_footnotes_passthrough(self):
        """Test that content without footnotes is handled normally."""
        html = """
        <h1>Heading</h1>
        <p>Regular paragraph with <strong>bold</strong> text.</p>
        <ol>
            <li>Regular list item 1</li>
            <li>Regular list item 2</li>
        </ol>
        """

        converter = FootnotePreservingConverter(heading_style="ATX")
        result = converter.convert(html)

        # Should not create footnote markers
        assert '[^' not in result
        # Should process normally
        assert '# Heading' in result
        assert 'Regular paragraph' in result

    def test_mixed_content_footnotes_and_lists(self):
        """Test document with both footnotes and regular lists."""
        html = """
        <p>Text with footnote<sup><a href="#fn1">[1]</a></sup>.</p>
        <ol>
            <li>Regular list item</li>
        </ol>
        <p>More text<sup><a href="#fn2">[2]</a></sup>.</p>
        <ol>
            <li id="fn1">First footnote. ↩</li>
            <li id="fn2">Second footnote. ↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Check footnote markers
        assert '[^1]' in result
        assert '[^2]' in result

        # Check footnote definitions
        assert '[^1]: First footnote.' in result
        assert '[^2]: Second footnote.' in result

        # Check regular list is preserved
        assert 'Regular list item' in result

    def test_superscript_without_footnote(self):
        """Test that regular superscript (not footnotes) is handled normally."""
        html = """
        <p>E=mc<sup>2</sup> is Einstein's equation.</p>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Should not create footnote marker
        assert '[^' not in result
        # Should preserve content
        assert 'Einstein' in result

    def test_footnote_numbering_stability(self):
        """Test that footnote numbers are assigned consistently."""
        html = """
        <p>First<sup><a href="#fn1">[1]</a></sup>, second<sup><a href="#fn2">[2]</a></sup>,
        first again<sup><a href="#fn1">[1]</a></sup>.</p>
        <ol>
            <li id="fn1">Footnote one. ↩</li>
            <li id="fn2">Footnote two. ↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Split into text and footnote definitions sections
        parts = result.split('\n\n')
        text_part = parts[0] if parts else ''

        # Count references in text (before definitions)
        # Should have 2 references to [^1] in the text
        assert text_part.count('[^1]') == 2
        assert text_part.count('[^2]') == 1

        # Should have one definition for each
        assert result.count('[^1]: Footnote one.') == 1
        assert result.count('[^2]: Footnote two.') == 1

    def test_empty_footnote_content(self):
        """Test handling of footnote with minimal content."""
        html = """
        <p>Text<sup><a href="#fn1">[1]</a></sup>.</p>
        <ol>
            <li id="fn1">↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Should create footnote structure even with empty content
        assert '[^1]' in result
        assert '[^1]:' in result

    def test_footnote_content_cleanup(self):
        """Test that backlink arrows and whitespace are cleaned up."""
        html = """
        <p>Text<sup><a href="#fn1">[1]</a></sup>.</p>
        <ol>
            <li id="fn1">Content with spaces and arrow   ↩   </li>
        </ol>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Arrow should be removed
        assert '↩' not in result
        # Content should be cleaned
        assert '[^1]: Content with spaces and arrow' in result

    def test_complex_footnote_content(self):
        """Test footnote with complex nested content."""
        html = """
        <p>Reference<sup><a href="#fn1">[1]</a></sup>.</p>
        <ol>
            <li id="fn1">See Smith, J. (2024). <em>Title of Work</em>. Publisher. ↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Should preserve citation structure
        assert '[^1]:' in result
        assert 'Smith, J.' in result
        assert '2024' in result
        assert 'Title of Work' in result

    def test_heading_style_option(self):
        """Test that heading_style option is respected."""
        html = """
        <h1>Heading</h1>
        <p>Text<sup><a href="#fn1">[1]</a></sup>.</p>
        <ol>
            <li id="fn1">Footnote. ↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter(heading_style="ATX")
        result = converter.convert(html)

        # Should use ATX style headings
        assert '# Heading' in result
        # Should still preserve footnotes
        assert '[^1]' in result
        assert '[^1]: Footnote.' in result

    def test_footnote_map_tracking(self):
        """Test that footnote_map is built correctly during conversion."""
        html = """
        <p>First<sup><a href="#fn1">[1]</a></sup> and second<sup><a href="#fn2">[2]</a></sup>.</p>
        <ol>
            <li id="fn1">First. ↩</li>
            <li id="fn2">Second. ↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter()
        result = converter.convert(html)

        # Check internal state after conversion
        assert 'fn1' in converter.footnote_map
        assert 'fn2' in converter.footnote_map
        assert converter.footnote_map['fn1'] == 1
        assert converter.footnote_map['fn2'] == 2
        assert converter.footnote_counter == 3  # Next number to assign

    def test_real_world_aar_pattern(self):
        """Test with HTML pattern that matches real AAR documents from Mammoth."""
        # This simulates actual output from Mammoth when converting Word footnotes
        html = """
        <p>The project team identified several key challenges during implementation
        <sup><a href="#footnote-1">[1]</a></sup> that impacted the timeline.</p>

        <p>Budget constraints<sup><a href="#footnote-2">[2]</a></sup> required creative
        solutions and resource reallocation.</p>

        <ol>
            <li id="footnote-1">Specifically, integration with legacy systems proved
            more complex than anticipated, requiring additional development time. ↩</li>
            <li id="footnote-2">The initial budget of $500,000 was reduced by 20%
            mid-project due to organizational restructuring. ↩</li>
        </ol>
        """

        converter = FootnotePreservingConverter(heading_style="ATX")
        result = converter.convert(html)

        # Verify footnote references are converted
        assert result.count('[^1]') >= 1
        assert result.count('[^2]') >= 1

        # Verify footnote definitions are present and cleaned
        assert '[^1]: Specifically, integration with legacy systems' in result
        assert '[^2]: The initial budget of $500,000' in result

        # Verify no HTML artifacts remain
        assert '<sup>' not in result
        assert '<a href=' not in result
        assert '↩' not in result
        assert '<ol>' not in result
        assert '<li id=' not in result
