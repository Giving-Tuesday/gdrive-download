# Analyzer Module

This module processes markdown documents to extract patterns, themes, and insights from documents.

## Components

### aar_analyzer.py
- **DocumentAnalyzer**: Main analysis engine
  - Analyzes challenges and successes across multiple documents
  - Aggregates findings by theme
  - Generates comprehensive insights
  - Supports custom analysis patterns

### doc_analyzer.py
- **DocumentAnalyzer**: Individual document processing
  - Extracts sections from templated documents
  - Parses markdown structure
  - Identifies key content areas
  - Supports both generic and template-aware extraction

### pattern_matcher.py
- **PatternMatcher**: Theme identification engine
  - Configurable regex patterns for categorization
  - Pre-defined patterns for common document themes
  - Match context extraction with surrounding text
  - Support for custom pattern definitions

### report_generator.py
- **ReportGenerator**: Output generation
  - Creates formatted markdown reports
  - Includes citations to source documents
  - Generates multiple report types (challenges, successes, insights)
  - Exports analysis data as JSON

## Usage

```python
from gdrive_download.analyzer import DocumentAnalyzer

# Analyze documents
analyzer = DocumentAnalyzer(config)
challenges = analyzer.analyze_challenges()
successes = analyzer.analyze_successes()

# Generate reports
analyzer.generate_reports(output_dir="reports")
```

## Default Pattern Categories

### Challenges
- Resource Constraints
- Data Collection & Measurement
- Communication & Coverage
- Partnership Management
- Timing & Scope

### Successes
- Leadership Development
- Content Creation
- Agility & Innovation
- Data Excellence
- Partnerships
- Community Engagement