"""
Document Analyzer - Generic framework for analyzing collections of structured documents.

This package provides a configurable framework for analyzing documents using templates.
AAR (After Action Review) analysis is provided as the primary template, but the framework
is designed to be extensible for other document types.
"""

from .templates.base_template import DocumentTemplate, load_template, list_available_templates
from .core.document_analyzer import DocumentAnalyzer
from .core.pattern_matcher import PatternMatcher, PatternMatch
from .core.report_generator import ReportGenerator

__version__ = "1.0.0"
__all__ = [
    "DocumentTemplate",
    "load_template",
    "list_available_templates",
    "DocumentAnalyzer",
    "PatternMatcher", 
    "PatternMatch",
    "ReportGenerator"
]