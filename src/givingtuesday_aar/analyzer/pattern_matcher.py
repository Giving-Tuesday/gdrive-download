"""Pattern matching for AAR content analysis."""

import re
from typing import Dict, List, Tuple, Pattern
from pathlib import Path


class PatternMatcher:
    """Matches patterns in AAR content to identify themes and categories."""
    
    def __init__(self, patterns: Dict[str, str]):
        self.patterns = {name: re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                        for name, pattern in patterns.items()}
    
    def find_matches(self, text: str, category: str = None) -> Dict[str, List[Tuple[str, int]]]:
        """Find all pattern matches in text."""
        matches = {}
        
        patterns_to_check = {category: self.patterns[category]} if category else self.patterns
        
        for pattern_name, pattern in patterns_to_check.items():
            pattern_matches = []
            for match in pattern.finditer(text):
                # Get surrounding context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                # Clean up context
                context = re.sub(r'\s+', ' ', context)
                if len(context) > 150:
                    context = context[:147] + "..."
                
                pattern_matches.append((context, match.start()))
            
            if pattern_matches:
                matches[pattern_name] = pattern_matches
        
        return matches
    
    def analyze_file(self, file_path: Path) -> Dict[str, List[Tuple[str, int]]]:
        """Analyze a single markdown file for pattern matches."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.find_matches(content)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {}
    
    def analyze_directory(self, directory: Path) -> Dict[str, Dict[str, List[Tuple[str, int]]]]:
        """Analyze all markdown files in a directory."""
        results = {}
        
        for md_file in directory.glob('*.md'):
            matches = self.analyze_file(md_file)
            if matches:
                results[md_file.name] = matches
        
        return results
    
    def get_category_summary(self, analysis_results: Dict) -> Dict[str, int]:
        """Get summary counts for each category across all files."""
        category_counts = {}
        
        for file_results in analysis_results.values():
            for category, matches in file_results.items():
                category_counts[category] = category_counts.get(category, 0) + len(matches)
        
        return category_counts
    
    def extract_quotes_for_category(self, analysis_results: Dict, category: str, 
                                  max_quotes: int = 10) -> List[Tuple[str, str]]:
        """Extract representative quotes for a specific category."""
        quotes = []
        
        for file_name, file_results in analysis_results.items():
            if category in file_results:
                for context, position in file_results[category]:
                    quotes.append((context, file_name))
                    if len(quotes) >= max_quotes:
                        break
                if len(quotes) >= max_quotes:
                    break
        
        return quotes
    
    def find_section_content(self, text: str, section_headers: List[str]) -> Dict[str, str]:
        """Extract content from specific sections of a document."""
        sections = {}
        
        for header in section_headers:
            # Look for various header formats
            patterns = [
                r'^#{{1,6}}\s*{}\s*$'.format(re.escape(header)),  # Markdown headers
                r'^\*\*{}\*\*\s*$'.format(re.escape(header)),      # Bold text
                r'^{}:?\s*$'.format(re.escape(header)),            # Plain text
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