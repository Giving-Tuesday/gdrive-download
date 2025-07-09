"""Report generation for document analysis results."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
from ..templates.base_template import DocumentTemplate


class ReportGenerator:
    """
    Generate analysis reports from document analysis results.
    
    Supports multiple report formats and customizable templates.
    """
    
    def __init__(self, template: DocumentTemplate):
        """
        Initialize report generator.
        
        Args:
            template: Document template used for analysis
        """
        self.template = template
    
    def generate_report(self, 
                       analysis_results: List[Dict[str, Any]], 
                       summary: Dict[str, Any],
                       output_format: str = 'markdown',
                       include_details: bool = True) -> str:
        """
        Generate a comprehensive analysis report.
        
        Args:
            analysis_results: List of individual document analysis results
            summary: Summary statistics across all documents
            output_format: Output format ('markdown', 'html', 'json')
            include_details: Whether to include detailed matches
            
        Returns:
            Formatted report string
        """
        if output_format == 'markdown':
            return self._generate_markdown_report(analysis_results, summary, include_details)
        elif output_format == 'html':
            return self._generate_html_report(analysis_results, summary, include_details)
        elif output_format == 'json':
            return self._generate_json_report(analysis_results, summary)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_markdown_report(self, 
                                 analysis_results: List[Dict[str, Any]], 
                                 summary: Dict[str, Any],
                                 include_details: bool) -> str:
        """Generate markdown format report."""
        lines = []
        
        # Header
        lines.append(f"# {self.template.description} Analysis Report")
        lines.append(f"")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Template:** {self.template.name}")
        lines.append(f"**Documents Analyzed:** {summary.get('total_documents', 0)}")
        lines.append(f"")
        
        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        
        overall_themes = summary.get('overall_themes', {})
        if overall_themes:
            for theme_category, themes in overall_themes.items():
                category_name = theme_category.replace('top_', '').replace('_', ' ').title()
                lines.append(f"### {category_name}")
                lines.append("")
                
                if themes:
                    for theme in themes:
                        lines.append(f"- {theme}")
                    lines.append("")
                else:
                    lines.append("No significant themes identified.")
                    lines.append("")
        
        # Pattern Analysis
        lines.append("## Pattern Analysis")
        lines.append("")
        
        pattern_frequencies = summary.get('pattern_frequencies', {})
        for category, patterns in pattern_frequencies.items():
            if patterns:
                lines.append(f"### {category.title()}")
                lines.append("")
                
                sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
                for pattern_name, count in sorted_patterns[:10]:  # Top 10
                    if count > 0:
                        pattern_display = pattern_name.replace('_', ' ').title()
                        lines.append(f"- **{pattern_display}**: {count} occurrences")
                lines.append("")
        
        # Document-Level Analysis
        if include_details and analysis_results:
            lines.append("## Document-Level Analysis")
            lines.append("")
            
            for i, result in enumerate(analysis_results, 1):
                metadata = result.get('metadata', {})
                doc_title = metadata.get('title', metadata.get('filename', f'Document {i}'))
                
                lines.append(f"### {doc_title}")
                lines.append("")
                
                # Sections found
                sections = result.get('sections', {})
                if sections:
                    lines.append("**Sections Identified:**")
                    for section_name, content in sections.items():
                        word_count = len(content.split())
                        lines.append(f"- {section_name.title()}: {word_count} words")
                    lines.append("")
                
                # Top themes for this document
                themes = result.get('themes', {})
                if themes:
                    lines.append("**Key Themes:**")
                    for theme_category, theme_list in themes.items():
                        if theme_list:
                            category_name = theme_category.replace('_', ' ').title()
                            lines.append(f"- {category_name}: {', '.join(theme_list[:3])}")
                    lines.append("")
                
                # Pattern matches summary
                matches = result.get('matches', {})
                if matches:
                    lines.append("**Pattern Matches:**")
                    for category, category_matches in matches.items():
                        total_matches = sum(len(pattern_matches) for pattern_matches in category_matches.values())
                        if total_matches > 0:
                            lines.append(f"- {category.title()}: {total_matches} matches")
                    lines.append("")
                
                lines.append("---")
                lines.append("")
        
        # Methodology
        lines.append("## Methodology")
        lines.append("")
        lines.append(f"This analysis was conducted using the **{self.template.name}** template, ")
        lines.append(f"which is designed for {self.template.description.lower()}.")
        lines.append("")
        
        # Pattern categories
        pattern_categories = self.template.get_pattern_categories()
        if pattern_categories:
            lines.append("The following pattern categories were analyzed:")
            for category in pattern_categories:
                patterns = self.template.get_patterns_for_category(category)
                lines.append(f"- **{category.title()}**: {len(patterns)} patterns")
            lines.append("")
        
        # Report sections
        report_sections = self.template.report_sections
        if report_sections:
            lines.append("The report includes the following sections:")
            for section in report_sections:
                lines.append(f"- {section.replace('_', ' ').title()}")
            lines.append("")
        
        return "\\n".join(lines)
    
    def _generate_html_report(self, 
                             analysis_results: List[Dict[str, Any]], 
                             summary: Dict[str, Any],
                             include_details: bool) -> str:
        """Generate HTML format report."""
        
        html_parts = []
        
        # HTML header
        html_parts.append("""<!DOCTYPE html>
<html>
<head>
    <title>Document Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; border-bottom: 2px solid #333; }
        h2 { color: #666; border-bottom: 1px solid #666; }
        h3 { color: #999; }
        .summary { background-color: #f5f5f5; padding: 20px; margin: 20px 0; }
        .document { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
        .pattern-match { background-color: #fffacd; padding: 5px; margin: 5px 0; }
        .metadata { color: #666; font-size: 0.9em; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>""")
        
        # Title and metadata
        html_parts.append(f"<h1>{self.template.description} Analysis Report</h1>")
        html_parts.append(f"<div class='metadata'>")
        html_parts.append(f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html_parts.append(f"<p><strong>Template:</strong> {self.template.name}</p>")
        html_parts.append(f"<p><strong>Documents Analyzed:</strong> {summary.get('total_documents', 0)}</p>")
        html_parts.append(f"</div>")
        
        # Executive Summary
        html_parts.append("<h2>Executive Summary</h2>")
        html_parts.append("<div class='summary'>")
        
        overall_themes = summary.get('overall_themes', {})
        if overall_themes:
            for theme_category, themes in overall_themes.items():
                category_name = theme_category.replace('top_', '').replace('_', ' ').title()
                html_parts.append(f"<h3>{category_name}</h3>")
                html_parts.append("<ul>")
                
                if themes:
                    for theme in themes:
                        html_parts.append(f"<li>{theme}</li>")
                else:
                    html_parts.append("<li>No significant themes identified.</li>")
                
                html_parts.append("</ul>")
        
        html_parts.append("</div>")
        
        # Pattern Analysis Table
        html_parts.append("<h2>Pattern Analysis</h2>")
        html_parts.append("<table>")
        html_parts.append("<tr><th>Category</th><th>Pattern</th><th>Occurrences</th></tr>")
        
        pattern_frequencies = summary.get('pattern_frequencies', {})
        for category, patterns in pattern_frequencies.items():
            if patterns:
                sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
                for pattern_name, count in sorted_patterns:
                    if count > 0:
                        pattern_display = pattern_name.replace('_', ' ').title()
                        html_parts.append(f"<tr><td>{category.title()}</td><td>{pattern_display}</td><td>{count}</td></tr>")
        
        html_parts.append("</table>")
        
        # Document details
        if include_details and analysis_results:
            html_parts.append("<h2>Document-Level Analysis</h2>")
            
            for i, result in enumerate(analysis_results, 1):
                metadata = result.get('metadata', {})
                doc_title = metadata.get('title', metadata.get('filename', f'Document {i}'))
                
                html_parts.append(f"<div class='document'>")
                html_parts.append(f"<h3>{doc_title}</h3>")
                
                # Sections
                sections = result.get('sections', {})
                if sections:
                    html_parts.append("<p><strong>Sections:</strong></p>")
                    html_parts.append("<ul>")
                    for section_name, content in sections.items():
                        word_count = len(content.split())
                        html_parts.append(f"<li>{section_name.title()}: {word_count} words</li>")
                    html_parts.append("</ul>")
                
                # Themes
                themes = result.get('themes', {})
                if themes:
                    html_parts.append("<p><strong>Key Themes:</strong></p>")
                    html_parts.append("<ul>")
                    for theme_category, theme_list in themes.items():
                        if theme_list:
                            category_name = theme_category.replace('_', ' ').title()
                            html_parts.append(f"<li>{category_name}: {', '.join(theme_list[:3])}</li>")
                    html_parts.append("</ul>")
                
                html_parts.append("</div>")
        
        html_parts.append("</body></html>")
        
        return "".join(html_parts)
    
    def _generate_json_report(self, 
                             analysis_results: List[Dict[str, Any]], 
                             summary: Dict[str, Any]) -> str:
        """Generate JSON format report."""
        
        report = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "template": self.template.name,
                "template_description": self.template.description,
                "total_documents": summary.get('total_documents', 0)
            },
            "summary": summary,
            "analysis_results": analysis_results,
            "template_info": {
                "name": self.template.name,
                "description": self.template.description,
                "version": self.template.metadata.get('version', '1.0.0'),
                "pattern_categories": self.template.get_pattern_categories(),
                "report_sections": self.template.report_sections
            }
        }
        
        return json.dumps(report, indent=2, default=str)
    
    def generate_pattern_report(self, 
                               matches: Dict[str, Dict[str, List[Dict[str, Any]]]], 
                               output_format: str = 'markdown') -> str:
        """
        Generate a focused report on pattern matches.
        
        Args:
            matches: Pattern matches by category
            output_format: Output format ('markdown', 'csv', 'json')
            
        Returns:
            Formatted pattern report
        """
        if output_format == 'markdown':
            lines = []
            lines.append("# Pattern Matches Report")
            lines.append("")
            lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"**Template:** {self.template.name}")
            lines.append("")
            
            for category, category_matches in matches.items():
                lines.append(f"## {category.title()}")
                lines.append("")
                
                for pattern_name, pattern_matches in category_matches.items():
                    if pattern_matches:
                        lines.append(f"### {pattern_name.replace('_', ' ').title()}")
                        lines.append(f"**Matches:** {len(pattern_matches)}")
                        lines.append("")
                        
                        for match in pattern_matches[:5]:  # Show first 5 matches
                            lines.append(f"- **Text:** {match.get('text', '')}")
                            lines.append(f"  **Context:** {match.get('context', '')}")
                            lines.append(f"  **Section:** {match.get('section', 'Unknown')}")
                            lines.append("")
                        
                        if len(pattern_matches) > 5:
                            lines.append(f"  *(and {len(pattern_matches) - 5} more matches)*")
                            lines.append("")
                
                lines.append("---")
                lines.append("")
            
            return "\\n".join(lines)
        
        elif output_format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Category', 'Pattern', 'Text', 'Context', 'Section'])
            
            for category, category_matches in matches.items():
                for pattern_name, pattern_matches in category_matches.items():
                    for match in pattern_matches:
                        writer.writerow([
                            category,
                            pattern_name,
                            match.get('text', ''),
                            match.get('context', ''),
                            match.get('section', '')
                        ])
            
            return output.getvalue()
        
        elif output_format == 'json':
            return json.dumps(matches, indent=2, default=str)
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def save_report(self, report_content: str, output_path: Path, format: str = 'markdown') -> None:
        """
        Save report to file.
        
        Args:
            report_content: Generated report content
            output_path: Output file path
            format: Report format for proper file extension
        """
        # Ensure proper file extension
        if format == 'markdown' and not output_path.suffix:
            output_path = output_path.with_suffix('.md')
        elif format == 'html' and not output_path.suffix:
            output_path = output_path.with_suffix('.html')
        elif format == 'json' and not output_path.suffix:
            output_path = output_path.with_suffix('.json')
        
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
    
    def get_report_sections(self) -> List[str]:
        """Get available report sections from template."""
        return self.template.report_sections
    
    def customize_report_sections(self, sections: List[str]) -> None:
        """
        Customize which sections to include in reports.
        
        Args:
            sections: List of section names to include
        """
        # This would modify the template's report_sections
        # For now, we'll just validate the sections exist
        available_sections = self.template.report_sections
        invalid_sections = [s for s in sections if s not in available_sections]
        
        if invalid_sections:
            raise ValueError(f"Invalid sections: {invalid_sections}. Available: {available_sections}")
        
        # In a full implementation, this would update the template
        # self.template.report_sections = sections