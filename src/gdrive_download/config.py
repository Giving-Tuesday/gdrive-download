"""Configuration management for AAR tools."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field


class DownloaderConfig(BaseModel):
    """Configuration for Google Drive downloader."""
    
    output_dir: Path = Field(default=Path("downloads"), description="Directory to save downloaded files")
    credentials_file: Optional[Path] = Field(default=None, description="Google API credentials file")
    token_file: Optional[Path] = Field(default=None, description="OAuth token storage file")
    batch_size: int = Field(default=10, description="Number of concurrent downloads")
    
    class Config:
        arbitrary_types_allowed = True


class AnalyzerConfig(BaseModel):
    """Configuration for AAR analyzer."""
    
    input_dir: Path = Field(default=Path("markdown"), description="Directory containing markdown files")
    output_dir: Path = Field(default=Path("reports"), description="Directory to save analysis reports")
    challenge_patterns: Dict[str, str] = Field(
        default_factory=lambda: {
            "resource_constraints": r"(?i)(resource|staff|capacity|time|budget|money|funding)",
            "data_collection": r"(?i)(data|metric|measurement|tracking|report|survey)",
            "communication": r"(?i)(communication|coordination|messaging|coverage|press)",
            "partnership": r"(?i)(partner|collaboration|relationship|stakeholder)",
            "timing_scope": r"(?i)(timeline|scope|planning|expectation|deadline)"
        },
        description="Regex patterns for identifying challenge categories"
    )
    success_patterns: Dict[str, str] = Field(
        default_factory=lambda: {
            "leadership": r"(?i)(leader|development|empowerment|capacity|growth)",
            "content": r"(?i)(content|engagement|quality|storytelling|media)",
            "agility": r"(?i)(agility|opportunity|adaptive|innovation|strategic)",
            "data_excellence": r"(?i)(measurement|research|data|analysis|insight)",
            "partnerships": r"(?i)(partnership|collaboration|relationship|network)",
            "community": r"(?i)(community|engagement|mobilization|participation)"
        },
        description="Regex patterns for identifying success categories"
    )
    
    class Config:
        arbitrary_types_allowed = True


class GlobalConfig(BaseModel):
    """Global configuration for AAR tools."""
    
    downloader: DownloaderConfig = Field(default_factory=DownloaderConfig)
    analyzer: AnalyzerConfig = Field(default_factory=AnalyzerConfig)
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
        
        with open(config_path, 'w') as f:
            yaml.dump(self.dict(), f, default_flow_style=False)


def get_config(config_path: Optional[Path] = None) -> GlobalConfig:
    """Get configuration from file or defaults."""
    if config_path is None:
        config_path = Path.cwd() / "aar_config.yaml"
    
    return GlobalConfig.from_yaml(config_path)