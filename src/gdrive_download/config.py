"""Configuration management for gdrive-download tools."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field


class DownloaderConfig(BaseModel):
    """Configuration for Google Drive downloader."""
    
    output_dir: Path = Field(default=Path("documents"), description="Directory to save downloaded files (relative to base directory)")
    credentials_file: Optional[Path] = Field(default=None, description="Google API credentials file")
    token_file: Optional[Path] = Field(default=None, description="OAuth token storage file")
    batch_size: int = Field(default=10, description="Number of concurrent downloads")
    
    class Config:
        arbitrary_types_allowed = True


# Analyzer configuration moved to document_analyzer package


class GlobalConfig(BaseModel):
    """Global configuration for gdrive-download tools."""
    
    downloader: DownloaderConfig = Field(default_factory=DownloaderConfig)
    working_dir: Path = Field(default=Path.cwd(), description="Base working directory")
    log_level: str = Field(default="INFO", description="Logging level")
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> "GlobalConfig":
        """Load configuration from YAML file."""
        if not config_path.exists():
            return cls()
        
        with open(config_path) as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def to_yaml(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert Path objects to strings for YAML serialization
        data = self.model_dump(mode='json')
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)


def get_config(config_path: Optional[Path] = None) -> GlobalConfig:
    """Get configuration from file or defaults."""
    if config_path is None:
        config_path = Path.cwd() / "gdrive_config.yaml"
    
    return GlobalConfig.from_yaml(config_path)