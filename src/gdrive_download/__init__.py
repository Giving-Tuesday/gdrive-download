"""GivingTuesday AAR Tools - A modular system for downloading and analyzing After Action Review documents."""

__version__ = "1.0.0"
__author__ = "GivingTuesday"

from .downloader import GoogleDriveDownloader, FileConverter
# Analysis functionality moved to document_analyzer package

__all__ = [
    "GoogleDriveDownloader",
    "FileConverter", 
    "AARAnalyzer",
    "ReportGenerator",
]