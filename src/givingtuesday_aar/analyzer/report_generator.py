"""Generate comprehensive reports from AAR analysis."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

from ..downloader.relationship_tracker import FileRelationshipTracker


class ReportGenerator:
    """Generates markdown reports from AAR analysis results."""
    
    def __init__(self, output_dir: Path, url_mappings: Dict[str, str] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.url_mappings = url_mappings or {}
    
    def generate_challenges_report(self, analysis_results: Dict, file_count: int) -> str:
        """Generate a comprehensive challenges report."""
        report_lines = [
            "# Persistent Challenges Across GivingTuesday After Action Reviews",
            "",
            f"*Analysis of {file_count} AAR documents*",
            "",
            "## Executive Summary",
            "",
            "Analysis of GivingTuesday's After Action Review documents reveals recurring systemic challenges that persist across teams, regions, and time periods. While each AAR documents specific successes and learnings, the analysis identifies key challenge areas that require organizational attention and systemic improvements.",
            "",
            "## Key Challenge Areas",
            ""
        ]
        
        # Add sections for each major challenge category
        for category, count in analysis_results['summary'].items():
            category_title = self._format_category_title(category)
            report_lines.extend([
                f"### {category_title}",
                "",
                f"This challenge appears across {count} instances in the analyzed documents.",
                ""
            ])
            
            # Add representative quotes
            if category in analysis_results['representative_quotes']:
                report_lines.append("**Representative examples:**")
                report_lines.append("")
                
                for quote, file_name in analysis_results['representative_quotes'][category][:3]:
                    citation = self._create_citation(file_name)
                    report_lines.append(f'*"{quote}"* ({citation})')
                    report_lines.append("")
        
        # Add recommendations section
        report_lines.extend([
            "## Recommendations for Systemic Improvement",
            "",
            "1. **Implement Standardized Planning**: Develop organizational templates for timeline estimation, resource planning, and risk assessment.",
            "",
            "2. **Create Data Infrastructure**: Establish consistent data collection frameworks and provide capacity building for measurement challenges.",
            "",
            "3. **Develop Partnership Assessment**: Create standardized criteria for evaluating potential partners and collaboration readiness.",
            "",
            "4. **Establish Communication Protocols**: Define clear communication frameworks for different types of initiatives.",
            "",
            "5. **Build Learning Loops**: Create systematic processes for applying AAR insights to future planning.",
            "",
            "---",
            "",
            f"*Analysis based on {file_count} AAR documents documenting challenges across GivingTuesday operations.*"
        ])
        
        return "\n".join(report_lines)
    
    def generate_successes_report(self, analysis_results: Dict, file_count: int) -> str:
        """Generate a comprehensive successes report."""
        report_lines = [
            "# Organizational Strengths and Successes Across GivingTuesday AARs",
            "",
            f"*Analysis of {file_count} AAR documents*",
            "",
            "## Executive Summary",
            "",
            "Analysis of GivingTuesday's After Action Review documents reveals remarkable patterns of organizational strengths and consistent successes across global operations. These successes demonstrate core competencies that form the foundation for the movement's continued growth and impact.",
            "",
            "## Core Organizational Strengths",
            ""
        ]
        
        # Add sections for each major success category
        for category, count in analysis_results['summary'].items():
            category_title = self._format_category_title(category)
            report_lines.extend([
                f"### {category_title}",
                "",
                f"This strength appears consistently across {count} instances in the analyzed documents.",
                ""
            ])
            
            # Add representative quotes
            if category in analysis_results['representative_quotes']:
                report_lines.append("**Key examples:**")
                report_lines.append("")
                
                for quote, file_name in analysis_results['representative_quotes'][category][:3]:
                    citation = self._create_citation(file_name)
                    report_lines.append(f'*"{quote}"* ({citation})')
                    report_lines.append("")
        
        # Add recommendations for scaling
        report_lines.extend([
            "## Recommendations for Scaling Successes",
            "",
            "1. **Systematize Excellence**: Document and replicate the approaches that consistently produce strong results.",
            "",
            "2. **Expand Best Practices**: Scale successful strategies to support teams globally.",
            "",
            "3. **Institutionalize Innovation**: Create mechanisms to recognize and respond to opportunities.",
            "",
            "4. **Leverage Core Strengths**: Apply proven capabilities across broader organizational contexts.",
            "",
            "5. **Amplify Success Stories**: Create systematic mechanisms for sharing innovations across the network.",
            "",
            "---",
            "",
            f"*Analysis based on {file_count} AAR documents documenting successes across GivingTuesday operations.*"
        ])
        
        return "\n".join(report_lines)
    
    def generate_insights_report(self, insights: Dict, challenges: Dict, successes: Dict) -> str:
        """Generate a high-level insights report."""
        report_lines = [
            "# AAR Analysis Insights Report",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Theme Analysis Overview",
            "",
            f"- **Challenge themes identified**: {insights['theme_analysis']['total_challenge_themes']}",
            f"- **Success themes identified**: {insights['theme_analysis']['total_success_themes']}",
            f"- **Overlapping themes**: {len(insights['theme_analysis']['overlapping_themes'])}",
            "",
            "## Top Challenge Areas",
            ""
        ]
        
        for category, count in insights['challenge_priority'][:5]:
            category_title = self._format_category_title(category)
            report_lines.append(f"1. **{category_title}**: {count} instances")
        
        report_lines.extend([
            "",
            "## Top Success Areas",
            ""
        ])
        
        for category, count in insights['success_strengths'][:5]:
            category_title = self._format_category_title(category)
            report_lines.append(f"1. **{category_title}**: {count} instances")
        
        # Add recurring themes analysis
        if insights['challenge_themes']:
            report_lines.extend([
                "",
                "## Recurring Challenge Themes",
                ""
            ])
            
            for theme, files in insights['challenge_themes'].items():
                theme_title = self._format_category_title(theme)
                report_lines.append(f"- **{theme_title}**: Appears in {len(files)} documents")
        
        if insights['success_themes']:
            report_lines.extend([
                "",
                "## Recurring Success Themes",
                ""
            ])
            
            for theme, files in insights['success_themes'].items():
                theme_title = self._format_category_title(theme)
                report_lines.append(f"- **{theme_title}**: Appears in {len(files)} documents")
        
        return "\n".join(report_lines)
    
    def _format_category_title(self, category: str) -> str:
        """Format category name for display."""
        return category.replace('_', ' ').title()
    
    def _create_citation(self, file_name: str) -> str:
        """Create a proper citation with URL if available."""
        base_name = Path(file_name).stem
        
        # Look for URL mapping
        google_url = None
        for citation_name, url in self.url_mappings.items():
            if citation_name.lower() in base_name.lower() or base_name.lower() in citation_name.lower():
                google_url = url
                break
        
        if google_url:
            return f"[{base_name}]({google_url})"
        else:
            return base_name
    
    def save_report(self, content: str, filename: str) -> Path:
        """Save a report to file."""
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def update_report_urls(self, report_path: Path, url_mappings: Dict[str, str]) -> None:
        """Update URLs in an existing report."""
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        replacements_made = 0
        
        for citation_name, google_url in url_mappings.items():
            # Pattern to match citations with any URL
            pattern = rf'\\[{re.escape(citation_name)}\\]\\([^)]+\\)'
            replacement = f'[{citation_name}]({google_url})'
            
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                replacements_made += 1
        
        # Write updated content
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {replacements_made} URLs in {report_path.name}")