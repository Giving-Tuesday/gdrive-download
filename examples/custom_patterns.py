#!/usr/bin/env python3
"""
Example: Using custom analysis patterns.

This example shows how to customize the analysis patterns
to look for specific themes relevant to your organization.
"""

from pathlib import Path
from gdrive_download.config import AnalyzerConfig
from gdrive_download.analyzer import AARAnalyzer, PatternMatcher


def main():
    """Demonstrate custom pattern analysis."""
    
    print("🔍 Custom Pattern Analysis Example")
    print("==================================")
    
    # Create custom patterns for your specific needs
    custom_challenge_patterns = {
        'technology_issues': r'(?i)(technical|software|platform|system|bug|crash|server)',
        'volunteer_management': r'(?i)(volunteer|recruitment|retention|training|onboarding)',
        'fundraising_challenges': r'(?i)(fundraising|donation|revenue|budget|financial)',
        'marketing_reach': r'(?i)(marketing|outreach|awareness|visibility|promotion)',
        'event_logistics': r'(?i)(logistics|venue|catering|setup|coordination|timing)'
    }
    
    custom_success_patterns = {
        'innovation': r'(?i)(innovation|creative|novel|breakthrough|pioneering)',
        'collaboration': r'(?i)(collaboration|teamwork|partnership|cooperation|unity)',
        'efficiency': r'(?i)(efficient|streamlined|optimized|faster|improved)',
        'impact_measurement': r'(?i)(impact|measurement|metrics|results|outcomes)',
        'scalability': r'(?i)(scalable|growth|expansion|replication|spread)'
    }
    
    # Set up configuration with custom patterns
    config = AnalyzerConfig()
    config.input_dir = Path("example_markdown")
    config.output_dir = Path("custom_reports")
    config.challenge_patterns = custom_challenge_patterns
    config.success_patterns = custom_success_patterns
    
    print("📋 Custom patterns configured:")
    print(f"   • Challenge categories: {len(custom_challenge_patterns)}")
    print(f"   • Success categories: {len(custom_success_patterns)}")
    
    # Initialize analyzer with custom config
    analyzer = AARAnalyzer(config)
    
    # Check if we have markdown files to analyze
    if not config.input_dir.exists() or not list(config.input_dir.glob('*.md')):
        print("\n⚠️  No markdown files found in example_markdown/")
        print("   Run the basic_usage.py example first to generate some files.")
        return
    
    print(f"\n📖 Analyzing files in {config.input_dir}...")
    
    # Analyze with custom patterns
    challenges = analyzer.analyze_challenges()
    successes = analyzer.analyze_successes()
    
    print("\n📊 Custom Challenge Analysis Results:")
    print("────────────────────────────────────")
    for category, count in challenges['summary'].items():
        if count > 0:
            print(f"   • {category.replace('_', ' ').title()}: {count} mentions")
            
            # Show a sample quote if available
            if category in challenges['representative_quotes']:
                quotes = challenges['representative_quotes'][category]
                if quotes:
                    sample_quote = quotes[0][0][:100] + "..." if len(quotes[0][0]) > 100 else quotes[0][0]
                    print(f"     └─ \"{sample_quote}\"")
    
    print("\n🎯 Custom Success Analysis Results:")
    print("──────────────────────────────────")
    for category, count in successes['summary'].items():
        if count > 0:
            print(f"   • {category.replace('_', ' ').title()}: {count} mentions")
            
            # Show a sample quote if available
            if category in successes['representative_quotes']:
                quotes = successes['representative_quotes'][category]
                if quotes:
                    sample_quote = quotes[0][0][:100] + "..." if len(quotes[0][0]) > 100 else quotes[0][0]
                    print(f"     └─ \"{sample_quote}\"")
    
    # Generate insights
    insights = analyzer.generate_insights(challenges, successes)
    
    print("\n💡 Custom Insights:")
    print("─────────────────")
    print(f"   • Most common challenge: {insights['challenge_priority'][0][0] if insights['challenge_priority'] else 'None'}")
    print(f"   • Biggest strength: {insights['success_strengths'][0][0] if insights['success_strengths'] else 'None'}")
    print(f"   • Recurring challenge themes: {len(insights['challenge_themes'])}")
    print(f"   • Recurring success themes: {len(insights['success_themes'])}")
    
    # Example: Focus on specific patterns
    print("\n🔬 Detailed Pattern Analysis:")
    print("────────────────────────────")
    
    # Create a focused pattern matcher for deep dive
    tech_patterns = {'tech_issues': custom_challenge_patterns['technology_issues']}
    tech_matcher = PatternMatcher(tech_patterns)
    
    # Analyze just technology issues
    tech_results = tech_matcher.analyze_directory(config.input_dir)
    tech_summary = tech_matcher.get_category_summary(tech_results)
    
    if tech_summary.get('tech_issues', 0) > 0:
        print(f"   🖥️  Technology Issues Deep Dive:")
        tech_quotes = tech_matcher.extract_quotes_for_category(tech_results, 'tech_issues', max_quotes=3)
        for i, (quote, file_name) in enumerate(tech_quotes, 1):
            print(f"      {i}. \"{quote[:80]}...\" ({file_name})")
    else:
        print("   🖥️  No significant technology issues found")
    
    print("\n✨ Custom analysis complete!")
    print("\n💡 Pro Tips:")
    print("   • Adjust patterns based on your specific terminology")
    print("   • Combine multiple pattern types for comprehensive analysis") 
    print("   • Use insights to guide future AAR templates")


if __name__ == "__main__":
    main()