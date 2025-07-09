"""Main document analyzer class."""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import re
from ..templates.base_template import DocumentTemplate, load_template


class DocumentAnalyzer:
    """
    Main document analyzer that uses templates to analyze documents.
    
    This class coordinates the analysis process by:
    1. Loading a document template
    2. Preprocessing documents using the template
    3. Extracting sections from documents
    4. Matching patterns against document content
    5. Generating analysis reports
    """
    
    def __init__(self, template: Union[str, DocumentTemplate]):
        """
        Initialize the analyzer with a template.
        
        Args:
            template: Either a template name (string) or a DocumentTemplate instance
        """
        if isinstance(template, str):
            self.template = load_template(template)
        else:
            self.template = template
    
    def analyze_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a single document.
        
        Args:
            content: Document content to analyze
            metadata: Optional document metadata
            
        Returns:
            Analysis results dictionary containing:
            - sections: Extracted sections
            - matches: Pattern matches by category
            - themes: Extracted themes
            - metadata: Document metadata
        """
        # Preprocess document
        processed_content = self.template.preprocess_document(content, metadata)
        
        # Extract sections
        sections = self.template.extract_sections(processed_content)
        
        # Match patterns against content
        matches = self._match_patterns(processed_content, sections)
        
        # Extract themes from matches
        themes = self._extract_themes(matches)
        
        return {
            'sections': sections,
            'matches': matches,
            'themes': themes,
            'metadata': metadata or {},
            'template': self.template.name
        }
    
    def analyze_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple documents.
        
        Args:
            documents: List of document dictionaries with 'content' and optional 'metadata'
            
        Returns:
            List of analysis results
        """
        results = []
        
        for doc in documents:
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            if content:
                analysis = self.analyze_document(content, metadata)
                results.append(analysis)
        
        return results
    
    def _match_patterns(self, content: str, sections: Dict[str, str]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Match patterns against document content.
        
        Args:
            content: Processed document content
            sections: Extracted sections
            
        Returns:
            Nested dictionary of pattern matches by category and pattern name
        """
        matches = {}
        
        # Get analysis patterns from template
        analysis_patterns = self.template.analysis_patterns
        
        for category, patterns in analysis_patterns.items():
            matches[category] = {}
            
            for pattern_name, pattern in patterns.items():
                pattern_matches = []
                
                # Search in full content
                regex = re.compile(pattern, re.IGNORECASE)
                for match in regex.finditer(content):
                    pattern_matches.append({
                        'pattern': pattern_name,
                        'text': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'context': self._get_context(content, match.start(), match.end()),
                        'section': self._find_section_for_match(match.start(), sections)
                    })
                
                # Also search in specific sections if available
                if category in sections:
                    section_content = sections[category]
                    for match in regex.finditer(section_content):
                        pattern_matches.append({
                            'pattern': pattern_name,
                            'text': match.group(),
                            'start': match.start(),
                            'end': match.end(),
                            'context': self._get_context(section_content, match.start(), match.end()),
                            'section': category
                        })
                
                matches[category][pattern_name] = pattern_matches
        
        return matches
    
    def _extract_themes(self, matches: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> Dict[str, List[str]]:
        """
        Extract themes from pattern matches.
        
        Args:
            matches: Pattern matches by category
            
        Returns:
            Dictionary mapping theme names to descriptions
        """
        # Use template's theme extraction if available
        if hasattr(self.template, 'extract_themes'):
            return self.template.extract_themes(matches)
        
        # Default theme extraction
        themes = {}
        
        for category, category_matches in matches.items():
            theme_counts = {}
            
            for pattern_name, pattern_matches in category_matches.items():
                if pattern_matches:  # Only count patterns with matches
                    theme_counts[pattern_name] = len(pattern_matches)
            
            if theme_counts:
                # Sort by frequency and take top themes
                sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
                top_themes = [
                    f"{theme.replace('_', ' ').title()} ({count} matches)"
                    for theme, count in sorted_themes[:3]
                ]
                themes[f"top_{category}"] = top_themes
        
        return themes
    
    def _get_context(self, content: str, start: int, end: int, context_size: int = 50) -> str:
        """
        Get context around a match.
        
        Args:
            content: Document content
            start: Match start position
            end: Match end position
            context_size: Number of characters to include on each side
            
        Returns:
            Context string
        """
        context_start = max(0, start - context_size)
        context_end = min(len(content), end + context_size)
        
        context = content[context_start:context_end]
        
        # Add ellipsis if truncated
        if context_start > 0:
            context = "..." + context
        if context_end < len(content):
            context = context + "..."
        
        return context
    
    def _find_section_for_match(self, match_start: int, sections: Dict[str, str]) -> Optional[str]:
        """
        Find which section a match belongs to.
        
        Args:
            match_start: Start position of the match
            sections: Extracted sections
            
        Returns:
            Section name or None if not found
        """
        # This is a simplified implementation
        # In practice, you'd need to track section positions in the original content
        return None
    
    def get_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary across multiple analysis results.
        
        Args:
            analysis_results: List of analysis results from analyze_documents
            
        Returns:
            Summary dictionary
        """
        total_docs = len(analysis_results)
        
        if not analysis_results:
            return {
                'total_documents': 0,
                'template': self.template.name,
                'overall_themes': {},
                'pattern_frequencies': {}
            }
        
        # Aggregate themes across all documents
        overall_themes = {}
        pattern_frequencies = {}
        
        for category in self.template.get_pattern_categories():
            pattern_frequencies[category] = {}
            
            for result in analysis_results:
                matches = result.get('matches', {})
                if category in matches:
                    for pattern_name, pattern_matches in matches[category].items():
                        if pattern_name not in pattern_frequencies[category]:
                            pattern_frequencies[category][pattern_name] = 0
                        pattern_frequencies[category][pattern_name] += len(pattern_matches)
        
        # Extract overall themes
        for category, patterns in pattern_frequencies.items():
            if patterns:
                sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
                top_patterns = [
                    f"{pattern.replace('_', ' ').title()} ({count} total matches)"
                    for pattern, count in sorted_patterns[:5] if count > 0
                ]
                overall_themes[f"top_{category}"] = top_patterns
        
        return {
            'total_documents': total_docs,
            'template': self.template.name,
            'overall_themes': overall_themes,
            'pattern_frequencies': pattern_frequencies
        }