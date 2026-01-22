"""Tests for configuration management."""

import pytest
from pathlib import Path

from gdrive_download.config import GlobalConfig, DownloaderConfig, get_config


def test_default_config():
    """Test default configuration creation."""
    config = GlobalConfig()
    
    assert config.downloader.output_dir == Path("downloads")
    assert config.log_level == "INFO"


def test_config_validation():
    """Test configuration validation."""
    config = GlobalConfig()
    
    # Test that paths are converted to Path objects
    assert isinstance(config.downloader.output_dir, Path)
    assert isinstance(config.working_dir, Path)


def test_config_from_yaml(temp_dir):
    """Test loading configuration from YAML file."""
    config_file = temp_dir / "test_config.yaml"
    
    # Create sample config file
    config_content = """
downloader:
  output_dir: custom_downloads
  batch_size: 5
  
log_level: DEBUG
"""
    
    config_file.write_text(config_content)
    
    config = GlobalConfig.from_yaml(config_file)
    
    assert config.downloader.output_dir == Path("custom_downloads")
    assert config.downloader.batch_size == 5
    assert config.log_level == "DEBUG"


def test_config_to_yaml(temp_dir):
    """Test saving configuration to YAML file."""
    config = GlobalConfig()
    config.log_level = "DEBUG"
    
    config_file = temp_dir / "output_config.yaml"
    config.to_yaml(config_file)
    
    assert config_file.exists()
    
    # Load it back
    loaded_config = GlobalConfig.from_yaml(config_file)
    assert loaded_config.log_level == "DEBUG"


def test_get_config_nonexistent_file():
    """Test get_config with non-existent file returns defaults."""
    config = get_config(Path("nonexistent.yaml"))
    
    assert config.log_level == "INFO"
    assert config.downloader.output_dir == Path("downloads")


# Analyzer configuration tests moved to document_analyzer package