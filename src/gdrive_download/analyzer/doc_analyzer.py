"""Generic document analyzer for extracting structured data from semi-structured markdown files."""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict
import yaml
from pydantic import BaseModel, Field


class ExtractionConfig(BaseModel):
    """Configuration for text extraction parameters."""
    include_pattern_analysis: bool = Field(default=True, description="Whether to include pattern matching analysis")
    recurring_theme_threshold: int = Field(default=3, description="Minimum files for recurring theme")


class CategoryConfig(BaseModel):
    """Configuration for a document analysis category."""
    description: str = Field(description="Description of what this category represents")
    section_headers: List[str] = Field(default_factory=list, description="Section headers to look for")
    patterns: Dict[str, str] = Field(description="Regex patterns for this category")


class AnalysisConfig(BaseModel):
    """Configuration for document analysis framework."""
    name: str = Field(description="Name of the analysis framework")
    description: Optional[str] = Field(default=None, description="Description of the framework")
    categories: Dict[str, CategoryConfig] = Field(description="Analysis categories")
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> "AnalysisConfig":
        """Load configuration from YAML file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    @classmethod
    def from_json(cls, config_path: Path) -> "AnalysisConfig":
        """Load configuration from JSON file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)


class DocumentAnalyzer:
    """Generic analyzer for extracting structured data from semi-structured markdown files."""
    
    def __init__(self, config: Union[AnalysisConfig, Path, str]):
        """Initialize with analysis configuration.
        
        Args:
            config: AnalysisConfig object, or path to YAML/JSON config file
        """
        if isinstance(config, (Path, str)):
            config_path = Path(config)
            if config_path.suffix.lower() == '.json':
                self.config = AnalysisConfig.from_json(config_path)
            else:
                self.config = AnalysisConfig.from_yaml(config_path)
        else:
            self.config = config
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = {}
        for category_name, category_config in self.config.categories.items():
            self.compiled_patterns[category_name] = {
                pattern_name: re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern_name, pattern in category_config.patterns.items()
            }
    
    def analyze_directory(self, markdown_dir: Path) -> Dict[str, Any]:
        """Analyze all markdown files in a directory.
        
        Args:
            markdown_dir: Directory containing markdown files
            
        Returns:
            Complete analysis results in structured format
        """
        results = {}
        
        # Analyze each category
        for category_name in self.config.categories.keys():
            category_results = self._analyze_category(markdown_dir, category_name)
            results[category_name] = category_results
        
        # Generate cross-category insights
        results['insights'] = self._generate_insights(results)
        results['metadata'] = self._generate_metadata(markdown_dir)
        
        return results
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single markdown file.
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            Analysis results for the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'error': str(e)}
        
        results = {}
        
        # Analyze each category
        for category_name in self.config.categories.keys():
            category_results = self._analyze_content(content, category_name)
            if category_results:
                results[category_name] = category_results
        
        # Extract sections
        sections = self._extract_sections(content)
        if sections:
            results['sections'] = sections
        
        return results
    
    def _analyze_category(self, markdown_dir: Path, category_name: str) -> Dict[str, Any]:
        """Analyze a specific category across all files in directory."""
        file_results = {}
        
        # Analyze each markdown file
        for md_file in markdown_dir.glob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matches = self._analyze_content(content, category_name)
                if matches:
                    file_results[md_file.name] = matches
                    
            except Exception as e:
                file_results[md_file.name] = {'error': str(e)}
        
        # Generate category summary
        summary = self._generate_category_summary(file_results)
        
        # Extract representative quotes
        quotes = self._extract_representative_quotes(file_results, category_name)
        
        return {
            'summary': summary,
            'detailed_results': file_results,
            'representative_quotes': quotes
        }
    
    def _analyze_content(self, content: str, category_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze content for a specific category."""
        if category_name not in self.compiled_patterns:
            return {}
        
        matches = {}
        patterns = self.compiled_patterns[category_name]
        
        for pattern_name, pattern in patterns.items():
            pattern_matches = []
            
            for match in pattern.finditer(content):
                # Extract context around match
                context = self._extract_context(content, match, self.config.extraction.context_chars)
                
                pattern_matches.append({
                    'text': match.group(),
                    'context': context,
                    'position': match.start(),
                    'pattern': pattern_name
                })
            
            if pattern_matches:
                matches[pattern_name] = pattern_matches
        
        return matches
    
    def _extract_context(self, text: str, match: re.Match, context_chars: int) -> str:
        """Extract context around a regex match."""
        start = max(0, match.start() - context_chars)
        end = min(len(text), match.end() + context_chars)
        context = text[start:end].strip()
        
        # Clean up context
        context = re.sub(r'\s+', ' ', context)
        if len(context) > context_chars * 2:
            context = context[:context_chars * 2 - 3] + "..."
        
        return context
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from content based on configured headers."""
        sections = {}
        
        for category_name, category_config in self.config.categories.items():
            if not category_config.section_headers:
                continue
                
            category_sections = self._find_section_content(content, category_config.section_headers)
            if category_sections:
                sections[category_name] = category_sections
        
        return sections
    
    def _find_section_content(self, text: str, section_headers: List[str]) -> Dict[str, str]:
        """Find content under specific section headers."""
        sections = {}
        
        for header in section_headers:
            # Look for various header formats
            patterns = [
                r'^#{1,6}\s*' + re.escape(header) + r'\s*$',  # Markdown headers
                r'^\*\*' + re.escape(header) + r'\*\*\s*$',   # Bold text
                r'^' + re.escape(header) + r':?\s*$',         # Plain text
            ]
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
                if matches:
                    start = matches[0].end()
                    
                    # Find next header or end of text
                    next_header_pattern = r'^(#{1,6}\s*.+|[*]{2}.+[*]{2}|\w+:?\s*)$'
                    next_match = re.search(next_header_pattern, text[start:], re.MULTILINE)
                    
                    if next_match:
                        end = start + next_match.start()
                    else:
                        end = len(text)
                    
                    sections[header] = text[start:end].strip()
                    break
        
        return sections
    
    def _generate_category_summary(self, file_results: Dict[str, Dict]) -> Dict[str, int]:
        """Generate summary statistics for a category."""
        pattern_counts = defaultdict(int)
        
        for file_name, file_data in file_results.items():
            if 'error' in file_data:
                continue
                
            for pattern_name, matches in file_data.items():
                pattern_counts[pattern_name] += len(matches)
        
        return dict(pattern_counts)
    
    def _extract_representative_quotes(self, file_results: Dict[str, Dict], 
                                     category_name: str) -> Dict[str, List[Dict[str, str]]]:
        """Extract representative quotes for each pattern in a category."""
        quotes = {}
        max_quotes = self.config.extraction.max_quotes_per_category
        
        # Get all patterns for this category
        if category_name not in self.config.categories:
            return quotes
        
        patterns = self.config.categories[category_name].patterns.keys()
        
        for pattern_name in patterns:
            pattern_quotes = []
            
            for file_name, file_data in file_results.items():
                if 'error' in file_data or pattern_name not in file_data:
                    continue
                
                for match in file_data[pattern_name]:
                    pattern_quotes.append({
                        'context': match['context'],
                        'file': file_name,
                        'pattern': pattern_name
                    })
                    
                    if len(pattern_quotes) >= max_quotes:
                        break
                
                if len(pattern_quotes) >= max_quotes:
                    break
            
            if pattern_quotes:
                quotes[pattern_name] = pattern_quotes
        
        return quotes
    
    def _find_recurring_themes(self, category_results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Find themes that appear across multiple files."""
        threshold = self.config.extraction.recurring_theme_threshold
        recurring_themes = defaultdict(list)
        
        # Count pattern occurrences across files
        pattern_files = defaultdict(set)
        
        for file_name, file_data in category_results['detailed_results'].items():
            if 'error' in file_data:
                continue
            for pattern_name in file_data.keys():
                pattern_files[pattern_name].add(file_name)
        
        # Identify patterns that appear in multiple files
        for pattern_name, files in pattern_files.items():
            if len(files) >= threshold:
                recurring_themes[pattern_name] = list(files)
        
        return dict(recurring_themes)
    
    def _generate_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cross-category insights."""
        insights = {}
        
        # Find recurring themes for each category
        for category_name, category_results in results.items():
            if category_name in ['insights', 'metadata']:
                continue
                
            insights[f'{category_name}_recurring_themes'] = self._find_recurring_themes(category_results)
        
        # Calculate cross-category statistics
        total_patterns = 0
        total_matches = 0
        
        for category_name, category_results in results.items():
            if category_name in ['insights', 'metadata']:
                continue
                
            summary = category_results.get('summary', {})
            total_patterns += len(summary)
            total_matches += sum(summary.values())
        
        insights['statistics'] = {
            'total_categories': len([k for k in results.keys() if k not in ['insights', 'metadata']]),
            'total_patterns': total_patterns,
            'total_matches': total_matches
        }
        
        return insights
    
    def _generate_metadata(self, markdown_dir: Path) -> Dict[str, Any]:
        """Generate metadata about the analysis."""
        md_files = list(markdown_dir.glob('*.md'))
        
        return {
            'analysis_framework': self.config.name,
            'framework_description': self.config.description,
            'total_files': len(md_files),
            'file_names': [f.name for f in md_files],
            'categories': list(self.config.categories.keys()),
            'total_patterns': sum(len(cat.patterns) for cat in self.config.categories.values())
        }
    
    def export_results(self, results: Dict[str, Any], output_path: Path, format: str = 'json') -> None:
        """Export analysis results to file.
        
        Args:
            results: Analysis results to export
            output_path: Path to output file
            format: Export format ('json' or 'yaml')
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        elif format.lower() == 'yaml':
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(results, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported format: {format}")