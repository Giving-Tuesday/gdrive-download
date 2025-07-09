"""CLI for extracting structured data from AAR documents for manual report writing."""

import click
import json
import csv
from pathlib import Path
from collections import defaultdict, Counter
from rich.console import Console

from ..config import get_config
from ..analyzer import AARAnalyzer, PatternMatcher
from ..utils import setup_logging


@click.command()
@click.option('--input-dir', '-i', default='markdown', help='Directory containing markdown files to analyze')
@click.option('--output-dir', '-o', default='data_export', help='Directory to save extracted data')
@click.option('--config-file', help='Path to configuration file')
@click.option('--log-level', default='INFO', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
def main(input_dir, output_dir, config_file, log_level):
    """Extract structured data from AAR documents for manual report writing."""
    
    # Setup logging
    logger = setup_logging(level=log_level)
    console = Console()
    
    try:
        # Load configuration
        config = get_config(Path(config_file) if config_file else None)
        config.analyzer.input_dir = Path(input_dir)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        markdown_dir = Path(input_dir)
        if not markdown_dir.exists():
            console.print(f"[red]Input directory not found: {input_dir}[/red]")
            raise click.Abort()
        
        file_count = len(list(markdown_dir.glob('*.md')))
        console.print(f"[blue]Extracting data from {file_count} AAR documents...[/blue]")
        
        # Initialize analyzer
        analyzer = AARAnalyzer(config.analyzer)
        
        # Extract basic statistics
        console.print("[blue]📊 Extracting document statistics...[/blue]")
        doc_stats = extract_document_statistics(markdown_dir)
        
        # Extract sections
        console.print("[blue]📝 Extracting improvement sections...[/blue]")
        improvement_sections = analyzer.extract_improvement_sections(markdown_dir)
        
        console.print("[blue]🎯 Extracting success sections...[/blue]")
        success_sections = analyzer.extract_success_sections(markdown_dir)
        
        # Extract keyword frequencies
        console.print("[blue]🔍 Analyzing keyword frequencies...[/blue]")
        keyword_analysis = extract_keyword_frequencies(markdown_dir, config.analyzer)
        
        # Extract file metadata
        console.print("[blue]📋 Extracting file metadata...[/blue]")
        file_metadata = extract_file_metadata(markdown_dir)
        
        # Save all data
        console.print(f"[blue]💾 Saving extracted data to {output_path}...[/blue]")
        
        # 1. Document statistics
        with open(output_path / 'document_statistics.json', 'w') as f:
            json.dump(doc_stats, f, indent=2)
        
        # 2. Raw sections (for manual review)
        with open(output_path / 'improvement_sections.json', 'w') as f:
            json.dump(improvement_sections, f, indent=2)
        
        with open(output_path / 'success_sections.json', 'w') as f:
            json.dump(success_sections, f, indent=2)
        
        # 3. Keyword analysis
        with open(output_path / 'keyword_analysis.json', 'w') as f:
            json.dump(keyword_analysis, f, indent=2)
        
        # 4. File metadata
        with open(output_path / 'file_metadata.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['filename', 'word_count', 'line_count', 'modification_date', 'size_bytes'])
            writer.writeheader()
            writer.writerows(file_metadata)
        
        # 5. Create summary for easy overview
        summary = {
            'analysis_date': doc_stats['analysis_date'],
            'total_documents': file_count,
            'documents_with_improvements': len(improvement_sections),
            'documents_with_successes': len(success_sections),
            'total_word_count': sum(doc['word_count'] for doc in file_metadata),
            'most_common_challenge_keywords': keyword_analysis['challenge_keywords'][:10],
            'most_common_success_keywords': keyword_analysis['success_keywords'][:10],
            'files_by_year': group_files_by_year(file_metadata)
        }
        
        with open(output_path / 'analysis_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        console.print(f"[green]✅ Data extraction complete![/green]")
        console.print(f"[green]📁 Files saved to: {output_path}[/green]")
        console.print(f"\n📈 Summary:")
        console.print(f"   • Documents processed: {file_count}")
        console.print(f"   • Documents with improvement sections: {len(improvement_sections)}")
        console.print(f"   • Documents with success sections: {len(success_sections)}")
        console.print(f"   • Total word count: {summary['total_word_count']:,}")
        
        console.print(f"\n📋 Next steps:")
        console.print(f"   1. Review the generated data files in {output_path}/")
        console.print(f"   2. Read the report_writing_guide.md for instructions")
        console.print(f"   3. Use the extracted data to write comprehensive reports")
        
    except Exception as e:
        logger.error(f"Error during data extraction: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


def extract_document_statistics(markdown_dir: Path) -> dict:
    """Extract basic statistics about the document collection."""
    from datetime import datetime
    
    stats = {
        'analysis_date': datetime.now().isoformat(),
        'total_documents': 0,
        'total_words': 0,
        'total_lines': 0,
        'documents_by_type': defaultdict(int),
        'average_document_length': 0
    }
    
    word_counts = []
    
    for md_file in markdown_dir.glob('*.md'):
        stats['total_documents'] += 1
        
        content = md_file.read_text(encoding='utf-8')
        word_count = len(content.split())
        line_count = len(content.splitlines())
        
        stats['total_words'] += word_count
        stats['total_lines'] += line_count
        word_counts.append(word_count)
        
        # Categorize by document type
        if 'template' in md_file.name.lower():
            stats['documents_by_type']['templates'] += 1
        elif any(year in md_file.name for year in ['2023', '2024', '2025']):
            year = next(year for year in ['2023', '2024', '2025'] if year in md_file.name)
            stats['documents_by_type'][f'year_{year}'] += 1
        else:
            stats['documents_by_type']['other'] += 1
    
    if word_counts:
        stats['average_document_length'] = sum(word_counts) // len(word_counts)
    
    return dict(stats)


def extract_keyword_frequencies(markdown_dir: Path, config) -> dict:
    """Extract keyword frequencies for challenges and successes."""
    challenge_words = []
    success_words = []
    
    # Enhanced keyword lists
    challenge_keywords = [
        'challenge', 'problem', 'issue', 'difficulty', 'constraint', 'limitation',
        'shortage', 'lack', 'insufficient', 'limited', 'struggle', 'barrier',
        'obstacle', 'bottleneck', 'gap', 'missing', 'absent', 'unclear',
        'confused', 'delayed', 'late', 'behind', 'failed', 'error'
    ]
    
    success_keywords = [
        'success', 'achievement', 'accomplishment', 'strength', 'excellent',
        'outstanding', 'effective', 'successful', 'strong', 'good', 'great',
        'improved', 'better', 'positive', 'beneficial', 'valuable', 'useful',
        'helpful', 'productive', 'efficient', 'innovative', 'creative',
        'breakthrough', 'significant', 'meaningful', 'impactful'
    ]
    
    for md_file in markdown_dir.glob('*.md'):
        content = md_file.read_text(encoding='utf-8').lower()
        words = content.split()
        
        # Count challenge keywords
        for word in words:
            clean_word = word.strip('.,!?";()[]{}').lower()
            if clean_word in challenge_keywords:
                challenge_words.append(clean_word)
        
        # Count success keywords  
        for word in words:
            clean_word = word.strip('.,!?";()[]{}').lower()
            if clean_word in success_keywords:
                success_words.append(clean_word)
    
    return {
        'challenge_keywords': [(word, count) for word, count in Counter(challenge_words).most_common(20)],
        'success_keywords': [(word, count) for word, count in Counter(success_words).most_common(20)],
        'total_challenge_mentions': len(challenge_words),
        'total_success_mentions': len(success_words)
    }


def extract_file_metadata(markdown_dir: Path) -> list:
    """Extract metadata for each file."""
    metadata = []
    
    for md_file in markdown_dir.glob('*.md'):
        content = md_file.read_text(encoding='utf-8')
        stat = md_file.stat()
        
        metadata.append({
            'filename': md_file.name,
            'word_count': len(content.split()),
            'line_count': len(content.splitlines()),
            'modification_date': stat.st_mtime,
            'size_bytes': stat.st_size
        })
    
    return sorted(metadata, key=lambda x: x['word_count'], reverse=True)


def group_files_by_year(file_metadata: list) -> dict:
    """Group files by year mentioned in filename."""
    by_year = defaultdict(int)
    
    for file_info in file_metadata:
        filename = file_info['filename']
        if '2023' in filename:
            by_year['2023'] += 1
        elif '2024' in filename:
            by_year['2024'] += 1
        elif '2025' in filename:
            by_year['2025'] += 1
        else:
            by_year['other'] += 1
    
    return dict(by_year)


if __name__ == '__main__':
    main()