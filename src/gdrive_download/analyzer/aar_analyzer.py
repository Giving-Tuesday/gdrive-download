"""Core AAR analysis functionality."""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re
from collections import defaultdict

from .pattern_matcher import PatternMatcher
from ..config import AnalyzerConfig


class AARAnalyzer:
    """Analyzes AAR documents to identify patterns, themes, and insights."""
    
    def __init__(self, config: AnalyzerConfig):
        self.config = config
        
        # Initialize pattern matchers
        self.challenge_matcher = PatternMatcher(config.challenge_patterns)
        self.success_matcher = PatternMatcher(config.success_patterns)
    
    def analyze_challenges(self, markdown_dir: Path = None) -> Dict:
        """Analyze challenges across all AAR documents."""
        if markdown_dir is None:
            markdown_dir = self.config.input_dir
        
        results = self.challenge_matcher.analyze_directory(markdown_dir)
        
        analysis = {
            'summary': self.challenge_matcher.get_category_summary(results),
            'detailed_results': results,
            'representative_quotes': {}
        }
        
        # Extract representative quotes for each category
        for category in self.config.challenge_patterns.keys():
            quotes = self.challenge_matcher.extract_quotes_for_category(results, category, max_quotes=5)
            analysis['representative_quotes'][category] = quotes
        
        return analysis
    
    def analyze_successes(self, markdown_dir: Path = None) -> Dict:
        """Analyze successes across all AAR documents."""
        if markdown_dir is None:
            markdown_dir = self.config.input_dir
        
        results = self.success_matcher.analyze_directory(markdown_dir)
        
        analysis = {
            'summary': self.success_matcher.get_category_summary(results),
            'detailed_results': results,
            'representative_quotes': {}
        }
        
        # Extract representative quotes for each category
        for category in self.config.success_patterns.keys():
            quotes = self.success_matcher.extract_quotes_for_category(results, category, max_quotes=5)
            analysis['representative_quotes'][category] = quotes
        
        return analysis
    
    def extract_improvement_sections(self, markdown_dir: Path = None) -> Dict[str, str]:
        """Extract 'Improvements' sections from all AAR documents."""
        if markdown_dir is None:
            markdown_dir = self.config.input_dir
        
        improvement_sections = {}
        improvement_headers = [
            'improvements', 'areas for improvement', 'what could be improved',
            'lessons learned', 'what went wrong', 'challenges', 'issues'
        ]
        
        for md_file in markdown_dir.glob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matcher = PatternMatcher({})
                sections = matcher.find_section_content(content, improvement_headers)
                
                if sections:
                    improvement_sections[md_file.name] = sections
                    
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
        
        return improvement_sections
    
    def extract_success_sections(self, markdown_dir: Path = None) -> Dict[str, str]:
        """Extract success/strength sections from all AAR documents."""
        if markdown_dir is None:
            markdown_dir = self.config.input_dir
        
        success_sections = {}
        success_headers = [
            'successes', 'what went well', 'strengths', 'wins', 'achievements',
            'highlights', 'positive outcomes', 'what worked'
        ]
        
        for md_file in markdown_dir.glob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matcher = PatternMatcher({})
                sections = matcher.find_section_content(content, success_headers)
                
                if sections:
                    success_sections[md_file.name] = sections
                    
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
        
        return success_sections
    
    def find_recurring_themes(self, analysis_results: Dict, threshold: int = 3) -> Dict[str, List[str]]:
        """Identify themes that appear across multiple documents."""
        recurring_themes = defaultdict(list)
        
        # Count occurrences of each category across files
        category_files = defaultdict(set)
        
        for file_name, file_results in analysis_results['detailed_results'].items():
            for category in file_results.keys():
                category_files[category].add(file_name)
        
        # Identify categories that appear in multiple files
        for category, files in category_files.items():
            if len(files) >= threshold:
                recurring_themes[category] = list(files)
        
        return dict(recurring_themes)
    
    def generate_insights(self, challenges: Dict, successes: Dict) -> Dict:
        """Generate high-level insights from challenge and success analysis."""
        insights = {
            'challenge_themes': self.find_recurring_themes(challenges),
            'success_themes': self.find_recurring_themes(successes),
            'challenge_priority': self._rank_categories(challenges['summary']),
            'success_strengths': self._rank_categories(successes['summary']),
        }
        
        # Calculate theme overlap
        challenge_categories = set(insights['challenge_themes'].keys())
        success_categories = set(insights['success_themes'].keys())
        
        insights['theme_analysis'] = {
            'total_challenge_themes': len(challenge_categories),
            'total_success_themes': len(success_categories),
            'overlapping_themes': list(challenge_categories & success_categories),
            'challenge_only_themes': list(challenge_categories - success_categories),
            'success_only_themes': list(success_categories - challenge_categories)
        }
        
        return insights
    
    def _rank_categories(self, category_counts: Dict[str, int]) -> List[Tuple[str, int]]:
        """Rank categories by frequency."""
        return sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    
    def get_file_count(self, markdown_dir: Path = None) -> int:
        """Get the number of markdown files analyzed."""
        if markdown_dir is None:
            markdown_dir = self.config.input_dir
        
        return len(list(markdown_dir.glob('*.md')))