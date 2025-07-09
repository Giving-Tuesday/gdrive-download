"""CLI for analyzing AAR documents."""

import click
import json
from pathlib import Path
from rich.console import Console

from ..config import get_config, AnalyzerConfig
from ..analyzer import AARAnalyzer, ReportGenerator
from ..utils import setup_logging


@click.command()
@click.option('--input-dir', '-i', default='markdown', help='Directory containing markdown files to analyze')
@click.option('--output-dir', '-o', default='reports', help='Directory to save analysis reports')
@click.option('--report-type', '-t', 
              type=click.Choice(['challenges', 'successes', 'insights', 'all']),
              default='all', help='Type of report to generate')
@click.option('--url-mappings', help='Path to URL mappings JSON file')
@click.option('--config-file', help='Path to configuration file')
@click.option('--log-level', default='INFO', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
@click.option('--save-analysis/--no-save', default=True, help='Save detailed analysis results')
def main(input_dir, output_dir, report_type, url_mappings, config_file, log_level, save_analysis):
    """Analyze AAR documents and generate reports."""
    
    # Setup logging
    logger = setup_logging(level=log_level)
    console = Console()
    
    try:
        # Load configuration
        config = get_config(Path(config_file) if config_file else None)
        
        # Override with CLI arguments
        config.analyzer.input_dir = Path(input_dir)
        config.analyzer.output_dir = Path(output_dir)
        
        # Load URL mappings if provided
        url_mapping_dict = {}
        if url_mappings:
            with open(url_mappings, 'r') as f:
                url_mapping_dict = json.load(f)
        
        # Initialize analyzer and report generator
        analyzer = AARAnalyzer(config.analyzer)
        report_gen = ReportGenerator(config.analyzer.output_dir, url_mapping_dict)
        
        markdown_dir = Path(input_dir)
        if not markdown_dir.exists():
            console.print(f"[red]Input directory not found: {input_dir}[/red]")
            raise click.Abort()
        
        file_count = analyzer.get_file_count(markdown_dir)
        console.print(f"[blue]Analyzing {file_count} AAR documents...[/blue]")
        
        # Generate reports based on type
        if report_type in ['challenges', 'all']:
            console.print("[blue]Analyzing challenges...[/blue]")
            challenges = analyzer.analyze_challenges(markdown_dir)
            
            if save_analysis:
                with open(config.analyzer.output_dir / 'challenges_analysis.json', 'w') as f:
                    json.dump(challenges, f, indent=2)
            
            report_content = report_gen.generate_challenges_report(challenges, file_count)
            report_path = report_gen.save_report(report_content, 'challenges_report.md')
            console.print(f"[green]Challenges report saved to: {report_path}[/green]")
        
        if report_type in ['successes', 'all']:
            console.print("[blue]Analyzing successes...[/blue]")
            successes = analyzer.analyze_successes(markdown_dir)
            
            if save_analysis:
                with open(config.analyzer.output_dir / 'successes_analysis.json', 'w') as f:
                    json.dump(successes, f, indent=2)
            
            report_content = report_gen.generate_successes_report(successes, file_count)
            report_path = report_gen.save_report(report_content, 'successes_report.md')
            console.print(f"[green]Successes report saved to: {report_path}[/green]")
        
        if report_type in ['insights', 'all']:
            console.print("[blue]Generating insights...[/blue]")
            
            # Need both analyses for insights
            if 'challenges' not in locals():
                challenges = analyzer.analyze_challenges(markdown_dir)
            if 'successes' not in locals():
                successes = analyzer.analyze_successes(markdown_dir)
            
            insights = analyzer.generate_insights(challenges, successes)
            
            if save_analysis:
                with open(config.analyzer.output_dir / 'insights_analysis.json', 'w') as f:
                    json.dump(insights, f, indent=2)
            
            report_content = report_gen.generate_insights_report(insights, challenges, successes)
            report_path = report_gen.save_report(report_content, 'insights_report.md')
            console.print(f"[green]Insights report saved to: {report_path}[/green]")
        
        console.print(f"[bold green]Analysis complete! Reports saved to: {output_dir}[/bold green]")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


if __name__ == '__main__':
    main()